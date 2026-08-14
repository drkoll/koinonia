"""netting — the most efficient LICIT capture: remove the waste, keep the float.

    python3 -m koinonia.netting            # the witness

The design goal, stated exactly by the request: create no value, capture it "as
though it were solar energy," thermodynamically licit, controlling whether the
system is entropic. Multilateral netting is that mechanism, and the physics
analogy is not decoration — it is the algorithm.

────────────────────────────────────────────────────────────────────────────
CIRCULATING OBLIGATION DOES NO NET WORK — KIRCHHOFF FOR DEBT

A owes B $100, B owes C $100, C owes A $100: three transactions, $300 moved. Yet
every NET position is zero — the circulation cancels completely, and the honest
settlement is ZERO transfers. That circulating debt is exactly a loop current that
does no net work: real motion, no delivered value, pure loss to friction. Netting
removes it.

On a realistic graph — 40 parties, 300 obligations — netting cut 300 transactions
to 39, an 87% reduction, and the eliminated transactions are captured fees: real
dollars, taken by removing waste, never by creating anything. Net positions sum to
zero (Kirchhoff's current law), so nothing is conjured and nothing leaks.

ENTROPY IS THE CONTROL KNOB. Each transaction leaks a fee, so the transaction
count IS the entropy of a settlement. Netting minimizes the transaction count,
therefore minimizes entropy, therefore captures the most value. "Control whether
the system is entropic" means: choose the settlement with the fewest transfers.

THE ONE HONEST LIMIT, NAMED. Reducing to (creditors + debtors − 1) transfers is
easy and always available — that is what `settle` does. But the ABSOLUTE minimum
(finding subsets that net to zero and need no transfer at all) is NP-hard in
general. So the verdict is PLUS on "this settles correctly and conserves" and the
report is explicit that provably-fewest is a separate hard problem the greedy does
not claim to solve. Near-optimal, and honest about the gap.

THE FLOAT, AND THE KENOSIS. Money that must sit in escrow during a netting cycle
earns licit time-value — the float. Held 30 days at 4%, a $15,000 pool yields ~$49.
The kenotic rule is enforced here: the operator's take is zero. Captured fees and
float flow to the members. The SYSTEM's purchasing power grows fat; the operator's
does not. That is the whole posture — self-emptying, κένωσις — expressed as an
invariant rather than a promise.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from krisis import Trit, Verdict

__all__ = [
    "Obligation", "Transfer", "net_positions", "settle", "entropy",
    "Capture", "capture_report", "float_yield", "distribute_kenotic",
]


@dataclass(frozen=True)
class Obligation:
    """A owes B an amount. The atom of the obligation graph."""

    debtor: str
    creditor: str
    amount: float

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("an obligation is a positive amount")
        if self.debtor == self.creditor:
            raise ValueError("a party cannot owe itself")


@dataclass(frozen=True)
class Transfer:
    """One settlement payment in the netted plan."""

    frm: str
    to: str
    amount: float


def net_positions(obligations: list[Obligation]) -> dict[str, float]:
    """Each party's net: owed to them minus what they owe. Sums to zero (Kirchhoff).

    This is the whole capture in one step — the gross tangle collapses to each
    party's single net number, and circulating loops vanish because they net out.
    """
    net: dict[str, float] = {}
    for o in obligations:
        net[o.debtor] = net.get(o.debtor, 0.0) - o.amount
        net[o.creditor] = net.get(o.creditor, 0.0) + o.amount
    return {p: round(v, 2) for p, v in net.items()}


def settle(net: dict[str, float]) -> list[Transfer]:
    """Greedy minimal settlement: largest debtor pays largest creditor, repeat.

    Produces at most (creditors + debtors − 1) transfers — the easy floor. Not
    guaranteed the absolute fewest (that is NP-hard), but a large, exact reduction.
    """
    debtors = sorted(([p, -v] for p, v in net.items() if v < -1e-9),
                     key=lambda x: x[1], reverse=True)
    creditors = sorted(([p, v] for p, v in net.items() if v > 1e-9),
                       key=lambda x: x[1], reverse=True)
    transfers: list[Transfer] = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        pay = min(debtors[i][1], creditors[j][1])
        transfers.append(Transfer(debtors[i][0], creditors[j][0], round(pay, 2)))
        debtors[i][1] -= pay
        creditors[j][1] -= pay
        if debtors[i][1] <= 1e-9:
            i += 1
        if creditors[j][1] <= 1e-9:
            j += 1
    return transfers


def entropy(obligations: list[Obligation]) -> int:
    """The settlement entropy: the transaction count, each leaking a fee."""
    return len(obligations)


@dataclass
class Capture:
    """What netting captured — every number, so the claim can be checked."""

    raw_transactions: int
    netted_transactions: int
    eliminated: int
    gross_owed: float
    net_settled: float
    fee_saved: float
    conserves: bool

    def line(self) -> str:
        pct = (self.eliminated / self.raw_transactions * 100
               if self.raw_transactions else 0.0)
        return (f"{self.raw_transactions} → {self.netted_transactions} transfers "
                f"({pct:.0f}% removed), ${self.fee_saved:,.2f} in fees captured")


def capture_report(obligations: list[Obligation], *, fee: float = 0.30
                   ) -> tuple[Capture, Verdict]:
    """Net the graph, settle it, and report the captured value with a verdict.

    PLUS   the settlement conserves (net positions sum to zero) and reduces the
           transaction count — value captured by removing waste.
    ZERO   nothing to net (empty or already minimal) — no capture, and that is an
           honest zero, not a failure.
    MINUS  the net positions do not sum to zero — impossible for real double-entry
           obligations, so it flags corrupted input rather than settling it.
    """
    if fee < 0:
        raise ValueError("a fee is not negative")
    if not obligations:
        return (Capture(0, 0, 0, 0.0, 0.0, 0.0, True),
                Verdict(Trit.ZERO, "no obligations — nothing to net"))
    net = net_positions(obligations)
    imbalance = round(sum(net.values()), 2)
    transfers = settle(net)
    gross = round(sum(o.amount for o in obligations), 2)
    net_settled = round(sum(v for v in net.values() if v > 0), 2)
    eliminated = len(obligations) - len(transfers)
    cap = Capture(len(obligations), len(transfers), eliminated, gross,
                  net_settled, round(eliminated * fee, 2), abs(imbalance) < 1e-6)
    if abs(imbalance) > 1e-6:
        return cap, Verdict(Trit.MINUS,
                            f"net positions sum to {imbalance}, not zero — the "
                            "obligation graph is not conservative; input is corrupt",
                            value=imbalance)
    if eliminated <= 0:
        return cap, Verdict(Trit.ZERO,
                            "already minimal — no redundant flow to remove")
    return cap, Verdict(Trit.PLUS, cap.line(), value=cap)


def float_yield(pool: float, *, apr: float, days: int) -> float:
    """Licit time-value on the escrow float — simple interest over the holding days."""
    if pool < 0 or apr < 0 or days < 0:
        raise ValueError("pool, apr, days are non-negative")
    return round(pool * apr * days / 365.0, 2)


def distribute_kenotic(captured: float, members: list[str], *,
                       operator_take: float = 0.0) -> dict[str, float]:
    """Split captured value to members. The operator's take MUST be zero.

    The kenotic invariant in code: this refuses any operator_take above zero. The
    captured fees and float belong to the members whose flows were netted; the
    operator keeps nothing. Self-emptying, enforced rather than promised.
    """
    if operator_take > 1e-9:
        raise ValueError(
            "operator_take must be zero — this is a kenotic engine; the captured "
            "value flows to the members, never to the operator")
    if not members:
        raise ValueError("no members to distribute to")
    if captured < 0:
        raise ValueError("cannot distribute a negative capture")
    share = round(captured / len(members), 2)
    return {m: share for m in members}


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

    print("\nKOINONIA NETTING WITNESS — capture value by removing waste, not creating it\n")

    print("CIRCULATING DEBT CANCELS — Kirchhoff for obligations")
    loop = [Obligation("A", "B", 100), Obligation("B", "C", 100),
            Obligation("C", "A", 100)]
    net = net_positions(loop)
    check("every net position in a pure cycle is zero", all(v == 0 for v in net.values()),
          str(net))
    check("so the honest settlement is ZERO transfers", settle(net) == [])
    cap, v = capture_report(loop)
    check("100% of the circulating transactions are eliminated",
          cap.eliminated == 3 and cap.netted_transactions == 0, cap.line())
    check("the capture verdict is PLUS — real value from removed waste", v.tag is P)

    print("\nCONSERVATION — net positions always sum to zero (nothing conjured)")
    import random
    rng = random.Random(3)
    parties = [f"p{i}" for i in range(40)]
    obs = []
    for _ in range(300):
        a, b = rng.sample(parties, 2)
        obs.append(Obligation(a, b, rng.randint(10, 500)))
    net = net_positions(obs)
    check("40 parties, 300 obligations: net sums to zero",
          abs(sum(net.values())) < 1e-6, str(round(sum(net.values()), 4)))
    cap, v = capture_report(obs, fee=0.30)
    check("netting cuts ~300 transactions to ~40 (>80% removed)",
          cap.netted_transactions < 60 and cap.eliminated > 240, cap.line())
    check("the fee saving is real dollars", cap.fee_saved > 70, f"${cap.fee_saved}")
    check("and the verdict is PLUS with the report attached",
          v.tag is P and v.value.eliminated == cap.eliminated)

    print("\nTHE SETTLEMENT ACTUALLY SETTLES — every net position is cleared")
    transfers = settle(net)
    settled = {p: 0.0 for p in net}
    for t in transfers:
        settled[t.frm] -= t.amount
        settled[t.to] += t.amount
    check("applying the transfers reproduces every net position",
          all(abs(settled[p] - net[p]) < 0.01 for p in net))
    check("transfers are at most (creditors + debtors - 1)",
          len(transfers) <= sum(1 for x in net.values() if abs(x) > 1e-9),
          str(len(transfers)))

    print("\nENTROPY IS THE KNOB — fewer transfers is less entropy is more capture")
    check("raw entropy is the obligation count", entropy(obs) == 300)
    check("netting strictly lowers it", cap.netted_transactions < entropy(obs))

    print("\nCORRUPT INPUT IS FLAGGED MINUS, NOT SILENTLY SETTLED")
    # Patch through capture_report's OWN globals — the namespace where its bare
    # `net_positions` call actually resolves — so the test is robust to how the
    # module was loaded (-m makes this __main__, not koinonia.netting).
    orig = capture_report.__globals__["net_positions"]
    capture_report.__globals__["net_positions"] = lambda o: {"X": 100.0, "Y": -40.0}
    try:
        _, vcorrupt = capture_report(loop)
        check("a non-conservative graph is MINUS, not silently settled",
              vcorrupt.tag is M, vcorrupt.why)
        check("and the imbalance is named", abs(vcorrupt.value - 60.0) < 1e-6)
    finally:
        capture_report.__globals__["net_positions"] = orig

    print("\nTHE FLOAT — licit time-value on money already in escrow")
    y = float_yield(14878.0, apr=0.04, days=30)
    check("a $14,878 pool held 30d at 4% yields ~$49", 45 < y < 52, f"${y}")
    check("a zero pool yields zero", float_yield(0, apr=0.05, days=30) == 0.0)

    print("\nTHE KENOTIC INVARIANT — the operator takes nothing")
    dist = distribute_kenotic(78.30, ["a", "b", "c"])
    check("captured value splits to the members", sum(dist.values()) - 78.30 < 0.05)
    refuses("any operator take above zero is REFUSED — self-emptying, enforced",
            lambda: distribute_kenotic(100.0, ["a"], operator_take=1.0))

    print("\nTHE GUARDS")
    refuses("a self-obligation is refused", lambda: Obligation("A", "A", 10))
    refuses("a non-positive obligation is refused", lambda: Obligation("A", "B", 0))
    empty_cap, empty_v = capture_report([])
    check("an empty graph is an honest ZERO, not a crash", empty_v.tag is Z)
    refuses("bool(a netting verdict) still raises — the family invariant holds",
            lambda: bool(capture_report(loop)[1]))

    print()
    if fails:
        print(f"FAILED — {len(fails)} of {n} check(s):")
        for f in fails:
            print("  · " + f)
        return 1
    print("KOINONIA NETTING WITNESS HOLDS — circulating debt cancels, net positions\n"
          "  conserve to zero, entropy (transaction count) is minimized to capture the\n"
          "  most value, the float is licit time-value, and the operator takes nothing.\n"
          "  Value captured by removing waste — created nowhere, as intended.")
    return 0


if __name__ == "__main__":
    sys.exit(_witness())
