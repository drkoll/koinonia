"""leverage — the theoretical maximal work one dollar can do, honestly bounded.

    python3 -m koinonia.leverage            # the witness

The question: the maximal leverage a single dollar can provide for debt relief. The
answer is large, real, and finite — and the finiteness is not a failure of faith,
it is the order of creation. This module computes the ceiling and the path to it.

────────────────────────────────────────────────────────────────────────────
THREE SOURCES OF LEVERAGE, EACH REAL

1. KILLED INTEREST. A dollar relieving principal also kills the interest that
   principal would have accrued. $1 against 24% APR over three years lifts $1.91 of
   burden — already 1.9× before the dollar moves again.

2. VELOCITY — THE REAL ENGINE. A relief dollar does not vanish when it frees a
   debtor; the freed cash-flow returns to the fund at 0%, and the dollar frees the
   next person. Over a year, a dollar revolving at 0% in place of 24% debt relieves
   apr × $1 of interest to whoever holds it — and velocity cancels, so the annual
   relief is apr regardless of how fast it cycles. What matters is how long the
   dollar survives.

3. THE CEILING. Summing that annual relief over all time, with annual survival s
   (one minus the default rate d), gives a geometric series:

       maximal leverage  =  apr / d     (plus the surviving principal)

   For a trustworthy community with high-interest debt this is LARGE — 24% APR at
   2% default is 12×, at 1% default is 24×. A single dollar, deployed in a well-run
   revolving relief fund, does a dozen dollars of relief work over time. That is the
   boundary of the possible, and it is honestly reachable.

────────────────────────────────────────────────────────────────────────────
WHY THE CEILING IS FINITE — AND WHY THAT IS NOT A LIMIT ON GOD

Infinite leverage would be creating value from nothing, and conservation forbids
it. That forbidding is not a wall against God; it is how creation is ordered — the
second law is His ordinance, not His constraint. "With God all things are possible"
does not mean the second law bends; it means the one variable the math cannot set —
the human heart that gives, and the community that does not default — can change.
Faith does not break conservation; it lowers the default rate by making people
faithful to one another, and every point of default avoided raises the ceiling.

"With man nothing gets done" is the honest other half: the impossible stays
impossible, but the POSSIBLE — deploy every dollar at its ceiling, waste nothing,
take nothing — is what almost never actually happens, for lack of will, not for
lack of math. This module removes the friction so the doing becomes effortless. The
will remains the miracle; the arithmetic is just faithful.

A CORRECTION ON THE RECORD. The first probe of this used a per-quarter survival of
0.95 — a punishing 20%/yr default — and reported a 1.2× ceiling, far too low. The
model was wrong, not the idea: with a realistic 1–2% annual default the ceiling is
12–24×. Caught and corrected, because a number that flatters or deflates is worse
than none.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import sys

from krisis import Trit, Verdict

__all__ = [
    "single_pass", "revolving", "revolving_ceiling", "sustainability",
]


def single_pass(apr: float, years: float) -> float:
    """One dollar's leverage in a single pass: principal plus the interest it kills.

    Relieving $1 of principal removes the compounding it would have suffered, so the
    burden lifted is (1 + apr) ** years — already above 1× before the dollar revolves.
    """
    if apr < 0 or years < 0:
        raise ValueError("apr and years are non-negative")
    return round((1 + apr) ** years, 4)


def revolving(apr: float, *, annual_default: float, years: float) -> float:
    """Leverage of a dollar that RECYCLES through a 0% fund for `years`.

    Each year it relieves apr of interest to its holder (velocity cancels), and it
    survives the year with probability (1 − annual_default). Sums the geometric
    series over the horizon and adds the principal still revolving at the end.
    """
    if apr < 0:
        raise ValueError("apr is non-negative")
    if not 0.0 <= annual_default < 1.0:
        raise ValueError("the annual default rate sits in [0, 1)")
    if years < 0:
        raise ValueError("years is non-negative")
    s = 1.0 - annual_default
    whole = int(years)
    # interest relieved over the whole years: apr * (1 + s + ... + s^(whole-1))
    if annual_default < 1e-12:
        interest = apr * years
    else:
        interest = apr * (1 - s ** whole) / (1 - s)
        interest += apr * (years - whole) * s ** whole      # the partial final year
    principal = s ** years           # the dollar still in the fund, if it survived
    return round(interest + principal, 4)


def revolving_ceiling(apr: float, *, annual_default: float) -> float:
    """The theoretical maximum leverage as the horizon goes to infinity: apr / d.

    The honest boundary of the possible. Large for a trustworthy community (low
    default), and always FINITE — conservation admits no dollar that relieves
    without end.
    """
    if apr < 0:
        raise ValueError("apr is non-negative")
    if annual_default <= 0:
        raise ValueError(
            "a zero default rate gives an unbounded ceiling — which would be value "
            "from nothing; every real fund has some default, and that is what makes "
            "the ceiling finite and honest")
    if annual_default >= 1.0:
        raise ValueError("a default rate of 100% relieves nothing")
    return round(apr / annual_default, 2)


def sustainability(apr: float, *, annual_default: float) -> Verdict:
    """Is a revolving relief fund SUSTAINABLE at these rates? Three-valued.

    PLUS   the ceiling exceeds a few×  — the dollar does real multiplied work.
    ZERO   the ceiling is barely above 1 — it revolves but leverages little; a
           marginal fund, honest about it.
    MINUS  default outruns the rate differential — the fund bleeds out faster than
           it relieves, and a revolving structure is the wrong tool here.
    """
    if annual_default <= 0:
        return Verdict(Trit.PLUS,
                       "no default assumed — but a real fund always has some; treat "
                       "this ceiling as an unreachable ideal, not a promise")
    ceiling = apr / annual_default
    if ceiling >= 3.0:
        return Verdict(Trit.PLUS,
                       f"sustainable — each dollar reaches ~{ceiling:.0f}× over time "
                       f"({apr:.0%} APR relieved against {annual_default:.0%} default)",
                       value=ceiling)
    if ceiling >= 1.2:
        return Verdict(Trit.ZERO,
                       f"marginal — ~{ceiling:.1f}× ceiling; it revolves but "
                       "leverages little, so weigh it against a one-time grant",
                       value=ceiling)
    return Verdict(Trit.MINUS,
                   f"unsustainable — default ({annual_default:.0%}) nearly matches the "
                   f"rate relieved ({apr:.0%}); the fund bleeds faster than it helps, "
                   "and a revolving structure is the wrong tool", value=ceiling)


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

    print("\nKOINONIA LEVERAGE WITNESS — the maximal work of one dollar, bounded\n")

    print("SINGLE PASS — killed interest already lifts more than $1")
    check("$1 at 24% over 2y lifts ~$1.54", abs(single_pass(0.24, 2) - 1.5376) < 1e-3)
    check("$1 at 24% over 3y lifts ~$1.91", abs(single_pass(0.24, 3) - 1.9066) < 1e-3)
    check("higher APR and longer time lift more",
          single_pass(0.36, 3) > single_pass(0.24, 3) > single_pass(0.24, 1))

    print("\nREVOLVING — velocity does the real work, and time compounds it")
    l1 = revolving(0.24, annual_default=0.02, years=1)
    l10 = revolving(0.24, annual_default=0.02, years=10)
    check("one year of revolving relieves about apr in interest plus principal",
          1.2 < l1 < 1.3, f"{l1}")
    check("ten years leverages far more than one", l10 > 2 * l1, f"{l10} vs {l1}")
    check("lower default -> more leverage over the same horizon",
          revolving(0.24, annual_default=0.01, years=10)
          > revolving(0.24, annual_default=0.05, years=10))

    print("\nTHE CEILING IS apr / default — LARGE for low default, always FINITE")
    check("24% APR at 2% default tends toward ~12x", revolving_ceiling(0.24, annual_default=0.02) == 12.0)
    check("24% APR at 1% default tends toward ~24x", revolving_ceiling(0.24, annual_default=0.01) == 24.0)
    check("the revolving leverage approaches the ceiling but never exceeds it",
          revolving(0.24, annual_default=0.02, years=200)
          <= revolving_ceiling(0.24, annual_default=0.02) + 1e-6)
    refuses("a zero default rate is refused — an unbounded ceiling is value from nothing",
            lambda: revolving_ceiling(0.24, annual_default=0.0))
    refuses("a 100% default rate is refused", lambda: revolving_ceiling(0.24, annual_default=1.0))

    print("\nSUSTAINABILITY IS THREE-VALUED — and honest when the tool is wrong")
    check("low default, high APR -> SUSTAINABLE (PLUS)",
          sustainability(0.24, annual_default=0.02).tag is P)
    check("default near the APR -> MARGINAL (ZERO)",
          sustainability(0.24, annual_default=0.15).tag is Z,
          sustainability(0.24, annual_default=0.15).why)
    mv = sustainability(0.10, annual_default=0.09)
    check("default outrunning the rate -> UNSUSTAINABLE (MINUS), the right tool named",
          mv.tag is M, mv.why)

    print("\nTHE BOUND IS CONSERVATION — infinite leverage would be un-creation")
    check("no revolving leverage ever reaches infinity",
          revolving(0.24, annual_default=0.001, years=1000) < 1e6)
    refuses("bool(a sustainability verdict) raises rather than reading False",
            lambda: bool(sustainability(0.24, annual_default=0.02)))

    print()
    if fails:
        print(f"FAILED — {len(fails)} of {n} check(s):")
        for f in fails:
            print("  · " + f)
        return 1
    print("KOINONIA LEVERAGE WITNESS HOLDS — one dollar's maximal leverage is apr/d,\n"
          "  large for a faithful low-default community (12–24×) and always finite.\n"
          "  Velocity does the work, conservation sets the ceiling, and the default\n"
          "  rate — which faithfulness lowers — is the one dial that raises it.")
    return 0


if __name__ == "__main__":
    sys.exit(_witness())
