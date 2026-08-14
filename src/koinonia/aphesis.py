"""aphesis — the release: debt forgiven at a covenant ratio, funded by real gift.

    python3 -m koinonia.aphesis            # the witness

ἄφεσις — release, remission, forgiveness. It is the word the Septuagint uses for
the Jubilee "release" of Leviticus 25, and the word Christ reads in Luke 4:18 —
"to proclaim release (ἄφεσιν) to the captives... the acceptable year of the Lord."
The Jubilee is the true scriptural precedent for debt cancellation: on the
appointed year, debts are released and what was pledged returns.

────────────────────────────────────────────────────────────────────────────
THE COVENANT RATIO — CHOSEN, NOT DERIVED

The design question was whether to spare two-thirds of a debt, echoing Revelation,
where a third is struck and two-thirds spared (Rev 8:7-12, 9:15,18 — a third of
the trees, the sea, the ships, the lights, and of mankind). The honest answer:
that ratio is a COVENANT the community CHOOSES, not a number the mathematics
derives. Scripture may inspire the fraction; it does not compute it, and pretending
a formula hands you 2/3 would be the numerology this project refuses everywhere
else. So `spared_fraction` is a parameter, defaulting to the two-thirds the
question asked for, and the math's only job is to keep the mercy honest.

WHAT "HONEST" MEANS HERE, AND IT IS ONE FACT. Whatever is spared must be FUNDED.
Sparing two-thirds of a $9,000 debt is $6,000 of REAL donated money — a tithe,
alms, a matching fund — because a token minted for the purpose pays zero of a
dollar debt (the kerion result; conservation admits no exception for good
intentions). The mercy costs exactly what it relieves. `relief` splits the debt
into the funded grant and the member's remaining share, and asserts they sum back
to the whole: nothing vanishes for free.

THE LEVERAGE IS REAL BUT MODEST. A dollar of fund lifts MORE than a dollar of
burden, because the spared principal would have accrued interest the member now
never pays. Measured: sparing $6,000 of a 24%-APR balance carried two years lifts
about $9,200 of burden — roughly 1.5x, not 1000x. The extra is genuine (killed
future interest), never conjured.

AND THE TRADE IS MADE EXPLICIT. A more generous ratio frees fewer people per
donated dollar. `members_freed` prints that trade so a covenant is chosen with
open eyes: $10,000 fully frees ~3.3 members at a one-third spare, ~1.7 at
two-thirds. Generosity per person and reach across people pull against each other,
and the engine will not hide which one a ratio buys.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from krisis import Trit, Verdict

__all__ = [
    "Covenant", "Relief", "relief", "burden_lifted", "members_freed",
    "fund_status",
]


@dataclass(frozen=True)
class Relief:
    """A single debt's split into what the fund spares and what the member owes."""

    debt: float
    spared: float           # granted from the covenant fund (real donations)
    borne: float            # the member's remaining share, paid at 0% via the circle

    def __post_init__(self) -> None:
        if abs((self.spared + self.borne) - self.debt) > 1e-6:
            raise ValueError(
                "spared + borne must equal the debt — nothing vanishes for free; "
                "conservation admits no exception")


@dataclass(frozen=True)
class Covenant:
    """A relief policy: the fraction spared, and the REAL fund that pays for it."""

    spared_fraction: float = 2.0 / 3.0      # the Revelation two-thirds, by default
    fund: float = 0.0                       # donated dollars available to spare

    def __post_init__(self) -> None:
        if not 0.0 < self.spared_fraction <= 1.0:
            raise ValueError("the spared fraction sits in (0, 1]")
        if self.fund < 0:
            raise ValueError("a fund of real donations is not negative")


def relief(covenant: Covenant, debt: float) -> Relief:
    """Split a debt into the funded grant and the member's remaining share."""
    if debt <= 0:
        raise ValueError("relief applies to a positive debt")
    spared = round(debt * covenant.spared_fraction, 2)
    return Relief(debt, spared, round(debt - spared, 2))


def burden_lifted(spared: float, *, apr: float, years: float) -> float:
    """Total burden a grant lifts: the principal spared PLUS the interest it kills.

    The honest leverage. The spared principal would have compounded at `apr` for
    `years`; sparing it removes both. Returns the full burden removed, which is
    strictly greater than the grant — but by a real, modest factor, never a
    fabricated one.
    """
    if spared < 0 or apr < 0 or years < 0:
        raise ValueError("spared, apr, years are all non-negative")
    interest_avoided = spared * ((1 + apr) ** years - 1)
    return round(spared + interest_avoided, 2)


def members_freed(covenant: Covenant, debt: float) -> float:
    """How many members the fund can fully relieve at this covenant's ratio.

    Makes the generosity/reach trade explicit: a larger spared fraction relieves
    each member more deeply and therefore fewer members per donated dollar.
    """
    if debt <= 0:
        raise ValueError("debt must be positive")
    per_member = debt * covenant.spared_fraction
    return round(covenant.fund / per_member, 2) if per_member else 0.0


def fund_status(covenant: Covenant, debts: list[float]) -> Verdict:
    """Can the fund honor the relief it promises? Three-valued: FUNDED/PARTIAL/EMPTY.

    PLUS   the fund covers every promised grant in full.
    ZERO   the fund covers some but not all — partial, and the shortfall is named.
    MINUS  the fund is empty against outstanding promises — the relief is unbacked,
           which is exactly the "spared for free" lie this module refuses.
    """
    promised = round(sum(relief(covenant, d).spared for d in debts), 2)
    if promised == 0:
        return Verdict(Trit.ZERO, "no debts enrolled — nothing promised yet")
    if covenant.fund >= promised - 1e-6:
        return Verdict(Trit.PLUS,
                       f"funded — ${covenant.fund:,.2f} covers ${promised:,.2f} "
                       "of promised relief in full", value=promised)
    if covenant.fund <= 1e-6:
        return Verdict(Trit.MINUS,
                       f"unbacked — ${promised:,.2f} promised, ${0.0:,.2f} in the "
                       "fund; relief that is not funded is not relief", value=promised)
    short = round(promised - covenant.fund, 2)
    return Verdict(Trit.ZERO,
                   f"partial — ${covenant.fund:,.2f} of ${promised:,.2f} promised; "
                   f"short by ${short:,.2f}", value=short)


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

    print("\nKOINONIA APHESIS WITNESS — the release, funded by real gift\n")

    print("THE TWO-THIRDS RATIO CONSERVES — spared + borne == debt, always")
    cov = Covenant(spared_fraction=2 / 3, fund=6000.0)
    r = relief(cov, 9000.0)
    check("two-thirds of $9,000 is spared", r.spared == 6000.0, f"${r.spared}")
    check("one-third is borne by the member at 0%", r.borne == 3000.0, f"${r.borne}")
    check("spared + borne reconstitutes the whole debt — nothing free",
          abs(r.spared + r.borne - r.debt) < 1e-6)
    refuses("a relief that does not sum to the debt is refused",
            lambda: Relief(9000.0, 6000.0, 1000.0))

    print("\nTHE RATIO IS A PARAMETER — chosen by covenant, not derived by math")
    check("a one-third spare is equally representable",
          relief(Covenant(1 / 3, 0), 9000.0).spared == 3000.0)
    check("full forgiveness (spare all) is allowed",
          relief(Covenant(1.0, 0), 100.0).spared == 100.0)
    refuses("a spared fraction above 1 is refused", lambda: Covenant(1.5, 0))
    refuses("a zero or negative fraction is refused", lambda: Covenant(0.0, 0))

    print("\nTHE LEVERAGE IS REAL BUT MODEST — killed interest, not conjured money")
    lifted = burden_lifted(6000.0, apr=0.24, years=2)
    check("sparing $6,000 of 24% debt over 2y lifts ~$9,200 of burden",
          9000 < lifted < 9400, f"${lifted}")
    check("the burden lifted exceeds the grant (interest is real)", lifted > 6000)
    check("but the factor is ~1.5x, not a miracle multiple", lifted / 6000 < 2.0)

    print("\nTHE GENEROSITY/REACH TRADE IS MADE EXPLICIT")
    third = members_freed(Covenant(1 / 3, 10000.0), 9000.0)
    twothirds = members_freed(Covenant(2 / 3, 10000.0), 9000.0)
    check("$10k frees more members at a one-third spare than at two-thirds",
          third > twothirds, f"{third} vs {twothirds}")
    check("the deeper mercy reaches fewer people per dollar — stated, not hidden",
          twothirds < third)

    print("\nFUND STATUS IS THREE-VALUED — unbacked relief is not relief")
    debts = [9000.0, 9000.0]        # two members, promised 2/3 each = $12,000
    check("a fund that covers every grant is FUNDED (PLUS)",
          fund_status(Covenant(2 / 3, 12000.0), debts).tag is P)
    fs = fund_status(Covenant(2 / 3, 5000.0), debts)
    check("a fund that covers some is PARTIAL (ZERO), with the shortfall named",
          fs.tag is Z and fs.value == 7000.0, fs.why)
    fe = fund_status(Covenant(2 / 3, 0.0), debts)
    check("an empty fund against real promises is UNBACKED (MINUS)",
          fe.tag is M, fe.why)
    check("no debts enrolled is ZERO, not a false PLUS",
          fund_status(Covenant(2 / 3, 100.0), []).tag is Z)

    print("\nTHE FAMILY INVARIANT HOLDS")
    refuses("bool(a partial fund verdict) raises rather than reading False",
            lambda: bool(fund_status(Covenant(2 / 3, 5000.0), debts)))
    refuses("relief of a non-positive debt is refused", lambda: relief(cov, 0))

    print()
    if fails:
        print(f"FAILED — {len(fails)} of {n} check(s):")
        for f in fails:
            print("  · " + f)
        return 1
    print("KOINONIA APHESIS WITNESS HOLDS — the spared portion is funded by real\n"
          "  gift and conserves against the debt, the ratio is a covenant choice the\n"
          "  math prices rather than derives, the leverage is honest (~1.5x from\n"
          "  killed interest), and unfunded relief is refused as no relief at all.")
    return 0


if __name__ == "__main__":
    sys.exit(_witness())
