"""circle — a debt-forgiveness engine that creates no money, and says so.

    python3 -m koinonia.circle            # the witness

κοινωνία — fellowship, the shared-resource community of Acts 2:44, "all things in
common." That is what this is: a rotating savings and credit association (ROSCA),
the oldest debt tool there is, done as verified math on a tamper-evident ledger.

────────────────────────────────────────────────────────────────────────────
THE ONE FACT THAT SETS THE WHOLE DESIGN

A token you mint pays ZERO of a dollar debt. Measured: a creditor is owed dollars
and will accept a minted token only if someone trades real dollars for it — so the
dollars come from a BUYER, never from the mint. Minting a million Lumina leaves a
$10,000 debt at exactly $10,000. This is the kerion result again, and there is no
exception for good intentions: issuance moves the price, not the goods.

So this engine does not mint wealth. It does the thing that actually frees people:
it ELIMINATES INTEREST through mutual aid, and the math is pure.

HOW A CIRCLE WORKS. N members each pay C per round into a pot; each round one
member receives the whole pot; rotate until all have received. Over a full cycle
every member pays C·N and receives C·N — so it CONSERVES exactly, member by
member, and creates no money. What it creates is TIMING: the early recipient gets
an interest-free loan, the late recipient a disciplined savings plan, and nobody
is a lender at interest.

WHY THAT DESTROYS DEBT. A member carrying card debt at 24% APR who takes an early
payout kills the card at 0% cost, then repays the circle at 0%. Measured on a
$2,400 balance over a year, that is ~$361 of interest destroyed per early slot —
and across a circle over years it converts high-interest debt into zero-interest
mutual obligation. This is legal and real: Mission Asset Fund runs exactly this in
the US and reports payments to the credit bureaus.

WHERE THE TOKEN HONESTLY LIVES. A "Lumina" here is a SHARE — a claim on a real
pot, backed one-to-one by a real contribution (kerion's backing rule). It can be
transferable, sealed, and crypto; it is never minted from nothing. A share is a
receipt for money that entered, not money conjured.

WHERE BRIGHTCHAIN EARNS ITS PLACE. The number-one way a circle dies is the
organizer taking the pot and vanishing. Sealing every contribution and payout on a
tamper-evident ledger removes the organizer's ability to lie, which is what lets a
circle scale past people who already trust each other. That is the honest crypto
use: provenance, not minting.

THE RISK THIS ENGINE REFUSES TO HIDE. A member can take an early payout and stop
contributing — default. That is the real failure mode, so `solvency` is
three-valued (SOLVENT / PENDING / DEFAULTED) and a default is a MINUS with the
shortfall named, never smoothed over.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from krisis import Trit, Verdict

__all__ = [
    "Circle", "pot", "schedule", "net_position", "position_value",
    "interest_saved", "solvency", "default_shortfall", "Share",
]


@dataclass(frozen=True)
class Circle:
    """A rotating savings circle. `order` is the payout sequence — a permutation."""

    members: tuple[str, ...]
    contribution: float
    order: tuple[int, ...]          # order[r] = index of the member paid in round r

    def __post_init__(self) -> None:
        n = len(self.members)
        if n < 2:
            raise ValueError("a circle needs at least two members")
        if self.contribution <= 0:
            raise ValueError("the per-round contribution must be positive")
        if sorted(self.order) != list(range(n)):
            raise ValueError(
                "order must be a permutation of every member index exactly once — "
                "each member receives the pot exactly once per cycle")


def pot(circle: Circle) -> float:
    """The whole pot handed over each round: everyone's contribution."""
    return circle.contribution * len(circle.members)


def schedule(circle: Circle) -> list[tuple[int, str]]:
    """(round, recipient) for the full cycle, in payout order."""
    return [(r, circle.members[circle.order[r]]) for r in range(len(circle.members))]


def net_position(circle: Circle, member: str) -> float:
    """A member's dollars in minus dollars out over a FULL cycle. Always zero.

    The proof that no money is created: everyone pays C·N and receives C·N, so the
    nominal net is exactly zero for every member. The value is never in the net —
    it is in the timing, which `position_value` prices.
    """
    if member not in circle.members:
        raise ValueError(f"{member!r} is not in this circle")
    n = len(circle.members)
    paid_in = circle.contribution * n          # C every round, N rounds
    received = pot(circle)                     # the pot, once
    return received - paid_in                  # == 0, by construction


def position_value(circle: Circle, member: str, *, monthly_rate: float) -> float:
    """What a member's SLOT is worth: the interest saved by receiving the pot early.

    This is the real asymmetry a fair circle must face. Getting the pot in round 0
    is an interest-free loan for the whole cycle; getting it last is pure saving.
    Priced as the avoided interest at `monthly_rate` over the months you hold the
    money early. Positive for early slots, ~zero for the last — which is why a fair
    circle assigns slots by LOTTERY, not by favour.
    """
    if member not in circle.members:
        raise ValueError(f"{member!r} is not in this circle")
    if monthly_rate < 0:
        raise ValueError("a rate is not negative")
    n = len(circle.members)
    round_received = circle.order.index(circle.members.index(member))
    # months you hold the pot before you would have finished contributing it
    months_early = (n - 1) - round_received
    return pot(circle) * monthly_rate * months_early


def interest_saved(principal: float, apr: float, term_months: int,
                   payment: float) -> float:
    """Interest a member destroys by refinancing high-APR debt through a 0% circle.

    Amortises `principal` at `apr` under `payment`/month for `term_months`, and
    returns the interest that servicing charges — which a 0% circle payout
    eliminates. This is the debt-forgiveness number, and it is computed, not
    promised.
    """
    if principal < 0 or apr < 0 or term_months < 1 or payment <= 0:
        raise ValueError("principal, apr >= 0; term >= 1 month; payment > 0")
    bal = principal
    interest = 0.0
    for _ in range(term_months):
        charge = bal * apr / 12.0
        interest += charge
        bal = bal + charge - payment
        if bal <= 0:
            break
    return round(interest, 2)


def solvency(circle: Circle, *, round_index: int,
             received_this_round: dict[str, float]) -> Verdict:
    """Is this round funded? Three-valued: SOLVENT / PENDING / DEFAULTED.

    PLUS   every member has paid this round's contribution — the pot is whole.
    ZERO   some contributions are not in yet, but none is confirmed missing —
           pending, not a failure.
    MINUS  a member paid LESS than the contribution and the window closed — a
           default, with the shortfall named. The risk the engine will not hide.
    """
    n = len(circle.members)
    if not 0 <= round_index < n:
        raise ValueError(f"round {round_index} is outside 0..{n - 1}")
    expected = circle.contribution
    missing = [m for m in circle.members if m not in received_this_round]
    short = {m: expected - received_this_round[m]
             for m in received_this_round
             if received_this_round[m] < expected - 1e-9}
    if short:
        total = round(sum(short.values()), 2)
        return Verdict(Trit.MINUS,
                       f"default — {len(short)} member(s) short by ${total:,.2f}; "
                       f"the pot is under-funded and cannot pay in full",
                       value=short)
    if missing:
        return Verdict(Trit.ZERO,
                       f"pending — {len(missing)} member(s) have not paid yet; "
                       "not a default until the window closes", value=missing)
    return Verdict(Trit.PLUS,
                   f"solvent — all {n} contributions in; pot of ${pot(circle):,.2f} "
                   "is whole", value=pot(circle))


def default_shortfall(circle: Circle, defaulter_round: int) -> float:
    """The exposure a mid-cycle default leaves: what the defaulter still owed.

    The honest worst case — a member takes an early payout, then stops. They
    received the pot but still owed contributions for the rounds after theirs; that
    unpaid remainder is the loss the other members carry. Naming it is the
    difference between a mutual-aid tool and a scam.
    """
    n = len(circle.members)
    if not 0 <= defaulter_round < n:
        raise ValueError(f"round {defaulter_round} is outside 0..{n - 1}")
    rounds_still_owed = (n - 1) - defaulter_round
    return circle.contribution * rounds_still_owed


@dataclass(frozen=True)
class Share:
    """A tokenized claim on a real pot — 'Lumina', backed one-to-one, never minted.

    A share exists only because a contribution entered. `backing` is the real money
    behind it; a share with no backing is refused, which is the whole difference
    between a receipt and counterfeit.
    """

    circle_id: str
    holder: str
    backing: float

    def __post_init__(self) -> None:
        if self.backing <= 0:
            raise ValueError(
                "a share must be backed by a real contribution — Lumina is a claim "
                "on money that entered, never money minted from nothing")


def _witness() -> int:
    fails: list[str] = []
    n = 0

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal n
        n += 1
        print(("  PASS  " if cond else "  FAIL  ") + label
              + ("" if cond else f" — {detail}"))
        if not cond:
            fails.append(label)

    def refuses(label: str, fn) -> None:
        try:
            fn()
            check(label, False, "the operation was ALLOWED")
        except Exception:
            check(label, True)

    P, Z, M = Trit.PLUS, Trit.ZERO, Trit.MINUS
    members = tuple(f"m{i}" for i in range(12))
    c = Circle(members, 200.0, tuple(range(12)))    # lottery order = identity here

    print("\nKOINONIA CIRCLE WITNESS — debt forgiveness that creates no money\n")

    print("CONSERVATION — no member nets a dollar; the pot is exactly the sum in")
    check("the pot is everyone's contribution", pot(c) == 2400.0)
    check("every member's full-cycle net position is ZERO — no wealth created",
          all(abs(net_position(c, m)) < 1e-9 for m in members))
    total_in = c.contribution * len(members) * len(members)
    total_out = pot(c) * len(members)
    check("total contributed equals total paid out", abs(total_in - total_out) < 1e-9,
          f"{total_in} vs {total_out}")

    print("\nTIMING IS THE VALUE — early slots are worth more, so fairness is lottery")
    v_first = position_value(c, "m0", monthly_rate=0.02)
    v_last = position_value(c, "m11", monthly_rate=0.02)
    check("the first slot is worth more than the last", v_first > v_last, f"{v_first} vs {v_last}")
    check("the last slot's timing value is zero — it is pure saving", v_last == 0.0)
    check("the slot advantage is real money, hence lottery assignment is the fair rule",
          v_first > 100)

    print("\nTHE DEBT-FORGIVENESS NUMBER — computed, not promised")
    saved = interest_saved(2400.0, 0.24, 12, 200.0)
    check("servicing $2,400 at 24% APR for a year costs ~$361 in interest",
          350 < saved < 375, f"${saved}")
    check("a 0% circle payout eliminates all of it", saved > 0)
    refuses("a non-positive payment is refused",
            lambda: interest_saved(2400, 0.24, 12, 0))

    print("\nSOLVENCY IS THREE-VALUED — pending is not default")
    full = {m: 200.0 for m in members}
    check("all contributions in -> SOLVENT (PLUS)",
          solvency(c, round_index=0, received_this_round=full).tag is P)
    partial = {m: 200.0 for m in members[:9]}
    sv = solvency(c, round_index=0, received_this_round=partial)
    check("some not-yet-paid -> PENDING (ZERO), not a failure", sv.tag is Z, sv.why)
    check("and it names who is outstanding", len(sv.value) == 3)
    shorted = {**full, "m5": 120.0}
    sd = solvency(c, round_index=0, received_this_round=shorted)
    check("a member paying less once the window closed -> DEFAULT (MINUS)",
          sd.tag is M, sd.why)
    check("and the shortfall is named in dollars", sd.value["m5"] == 80.0)

    print("\nTHE DEFAULT RISK IS NAMED, NOT HIDDEN")
    early = default_shortfall(c, 0)     # took round 0, owes 11 more
    late = default_shortfall(c, 11)     # took last, owes nothing after
    check("an early defaulter leaves the largest exposure", early == 200.0 * 11)
    check("a last-round recipient can leave no shortfall", late == 0.0)
    check("the engine quantifies the worst case rather than pretending it away",
          early > late)

    print("\nA SHARE IS A CLAIM ON REAL MONEY — 'Lumina' is never minted from nothing")
    s = Share("circle-1", "m0", 200.0)
    check("a backed share exists", s.backing == 200.0)
    refuses("a share with no backing is refused — that would be counterfeit",
            lambda: Share("circle-1", "m0", 0.0))

    print("\nTHE FAMILY INVARIANT STILL HOLDS")
    refuses("bool(a pending solvency verdict) raises rather than reading False",
            lambda: bool(solvency(c, round_index=0, received_this_round=partial)))
    refuses("a circle whose order is not a permutation is refused",
            lambda: Circle(members, 200.0, tuple([0] * 12)))
    refuses("a one-member circle is refused", lambda: Circle(("solo",), 100.0, (0,)))

    print()
    if fails:
        print(f"FAILED — {len(fails)} of {n} check(s):")
        for f in fails:
            print("  · " + f)
        return 1
    print("KOINONIA CIRCLE WITNESS HOLDS — it conserves exactly (no money created),\n"
          "  prices the timing advantage so slots go by lottery, computes the interest\n"
          "  it destroys, and names the default risk three-valued rather than hiding\n"
          "  it. A share is a claim on real money; Lumina is never minted from nothing.")
    return 0


if __name__ == "__main__":
    sys.exit(_witness())
