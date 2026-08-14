"""metabolism — the whole loop: capture, power the work, give the surplus away.

    python3 -m koinonia.metabolism            # the witness

The capstone composition. It ties the pieces the session built into one living
loop: a `kerion` ATP battery that stores captured value, processes that are
rate-limited by that energy, and the surplus routed to a `koinonia` relief fund. The
system runs on what it captures and gives away what it does not need — a body that
feeds itself and tithes.

────────────────────────────────────────────────────────────────────────────
THE METABOLIC LOOP

    CAPTURE   real value enters (earnings, donations, netting fees, float)   → reserve
    MINT      charge Lumina against the reserve, never beyond it             → ATP
    RUN       a process requests ATP; it runs only if the battery can pay    → work
    HARVEST   surplus (reserve beyond what Lumina commits) → the relief fund → charity

Nothing is minted from nothing; nothing is spent that was not charged; nothing is
given that is not surplus. Each arrow is a guard, not a hope. `run` gates a process
on the energy budget — admitted (PLUS) it executes, throttled (ZERO) it waits,
unaffordable (MINUS) it is refused until more value is captured. `harvest` moves
only the surplus, so giving never touches the backing.

WHY THIS IS THE HONEST "FREEMIUM ENGINE." A gambling app hands you a premium token
that holds real-world value, and the conversion works because the operator's reserve
covers it. This is that, made transparent and kenotic: the token (Lumina) is backed
by a published, auditable reserve; the conversion cannot exceed the backing; and the
operator's take is not profit but the poor's relief. The science-fiction part —
"take any value at a moment and store it as luminal buying power" — is just capture
plus a backed mint. The honest part is that it never pretends the buying power
appeared; it was captured, and the surplus is given away.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Callable

from kerion import Capture, Cell
from krisis import Trit, Verdict

__all__ = ["Metabolism", "ProcessRun"]


@dataclass
class ProcessRun:
    """The outcome of asking the metabolism to run a process on its energy budget."""

    process: str
    cost: float
    verdict: Verdict          # PLUS ran · ZERO throttled · MINUS unaffordable
    result: object = None     # the process's return value, when it ran

    @property
    def ran(self) -> bool:
        return self.verdict.tag is Trit.PLUS


class Metabolism:
    """One living loop over a Lumina battery and a relief fund. Capture → power → give.

    `operating_floor` is the reserve the body keeps for itself before anything is
    called surplus — a cell does not tithe itself into starvation. Only reserve above
    the floor, and above what Lumina commits, is ever given away.
    """

    def __init__(self, cell: Cell | None = None, *, operating_floor: float = 0.0) -> None:
        if operating_floor < 0:
            raise ValueError("the operating floor is non-negative")
        self.cell = cell or Cell()
        self.operating_floor = operating_floor
        self.relieved = 0.0                       # total given to the relief fund
        self.log: list[str] = []

    # — capture: real value in —
    def capture(self, amount: float, *, source: str, evidence: str) -> None:
        """Real value enters the reserve. The only way the battery grows."""
        self.cell.capture(Capture(amount, source, evidence))
        self.log.append(f"captured {amount:.2f} from {source}")

    def charge(self, amount: float) -> Verdict:
        """Mint Lumina against the reserve — the backed charge. Refused past backing."""
        v = self.cell.mint(amount)
        self.log.append(f"charge {amount:.2f}: {v.tag.glyph}")
        return v

    # — run: a process is rate-limited by the energy it costs —
    def run(self, process: str, cost: float, do_work: Callable[[], object]
            ) -> ProcessRun:
        """Run a process only if the battery can pay its ATP cost.

        Admitted (PLUS): `do_work` executes and its result is returned. Throttled
        (ZERO): not enough charged now — it does not run, wait and recharge.
        Unaffordable (MINUS): it costs more than the whole reserve — capture first.
        """
        v = self.cell.admit(cost, process=process)
        if v.tag is Trit.PLUS:
            result = do_work()
            self.log.append(f"ran '{process}' (cost {cost:.2f})")
            return ProcessRun(process, cost, v, result)
        self.log.append(f"held '{process}': {v.tag.glyph}")
        return ProcessRun(process, cost, v, None)

    # — harvest: the surplus becomes charity —
    def givable(self) -> float:
        """Surplus above the operating floor — what the body may give without harm."""
        return round(max(0.0, self.cell.surplus() - self.operating_floor), 6)

    def harvest(self) -> Verdict:
        """Route the givable surplus to the relief fund. The tithe.

        Gives only surplus above the operating floor, so backing and the body's own
        reserve are untouched. Nothing to give is an honest ZERO, not a failure.
        """
        give = self.givable()
        if give <= 0:
            return Verdict(Trit.ZERO,
                           "nothing to harvest — no surplus above the operating floor")
        v = self.cell.disburse(give, purpose="relief fund")
        if v.tag is Trit.PLUS:
            self.relieved += give
            self.log.append(f"harvested {give:.2f} to relief (total {self.relieved:.2f})")
            return Verdict(Trit.PLUS,
                           f"harvested {give:.2f} to the relief fund; the body kept "
                           f"its floor of {self.operating_floor:.2f} and gave the rest",
                           value=give)
        return v

    def report(self) -> dict:
        """The body's state: reserve, charge, surplus, and total relieved."""
        return {"reserve": self.cell.reserve, "charged": self.cell.charged,
                "spent": self.cell.spent, "givable": self.givable(),
                "relieved": round(self.relieved, 6),
                "solvency": self.cell.solvency().tag.glyph}


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

    print("\nKOINONIA METABOLISM WITNESS — capture, power the work, give the surplus\n")

    print("CAPTURE → MINT — the battery grows only on real value, backed")
    m = Metabolism(operating_floor=100.0)
    m.capture(1000.0, source="clinic earnings", evidence="sha256:receipt")
    check("captured value grows the reserve", m.cell.reserve == 1000.0)
    check("minting within backing succeeds", m.charge(500.0).tag is P)
    check("minting beyond backing is refused (inflation)", m.charge(600.0).tag is M)

    print("\nRUN — every process is rate-limited by the energy it costs")
    ran = m.run("transcreation", 200.0, lambda: "a dubbed line")
    check("an affordable process is admitted and RUNS", ran.ran and ran.result, ran.verdict.why)
    check("its ATP was spent", m.cell.charged == 300.0, str(m.cell.charged))
    throttled = m.run("big batch", 400.0, lambda: "should not run")
    check("a process beyond the charged battery is THROTTLED, not run",
          throttled.verdict.tag is Z and not throttled.ran, throttled.verdict.why)
    check("and it did not execute", throttled.result is None)
    unaff = m.run("impossible", 5000.0, lambda: "never")
    check("a process costing more than the whole reserve is UNAFFORDABLE (MINUS)",
          unaff.verdict.tag is M and not unaff.ran)

    print("\nHARVEST — the surplus above the floor becomes charity")
    # reserve 1000, charged 300 (after spending 200), spent 200 -> surplus 500,
    # floor 100 -> givable 400
    check("givable is surplus above the operating floor",
          abs(m.givable() - 400.0) < 1e-6, f"{m.givable()}")
    h = m.harvest()
    check("harvesting routes the givable surplus to relief (PLUS)", h.tag is P, h.why)
    check("the relief total grew", m.relieved == 400.0)
    check("and the reserve shrank by exactly the gift", m.cell.reserve == 600.0)
    check("charged Lumina is still fully backed after the tithe",
          m.cell.solvency().tag in (P, Z))

    print("\nGIVING NEVER TOUCHES THE BACKING OR THE FLOOR")
    check("a second harvest finds nothing above the floor -> ZERO",
          m.harvest().tag is Z, m.harvest().why)
    # the body keeps its operating floor: reserve 600 = charged 300 + spent 200 + 100 floor
    check("the reserve retained the operating floor for the body",
          m.cell.reserve - m.cell.charged - m.cell.spent <= m.operating_floor + 1e-6)
    refuses("a negative operating floor is refused",
            lambda: Metabolism(operating_floor=-1))

    print("\nTHE FULL LOOP RUNS END TO END")
    body = Metabolism()
    body.capture(300, source="donation", evidence="e")
    body.charge(300)
    body.run("seal", 50, lambda: "sealed")
    body.run("netting", 50, lambda: "netted")
    body.capture(100, source="netting fees", evidence="e")   # off-time capture
    rep = body.report()
    check("the loop tracked reserve, charge, and solvency coherently",
          rep["reserve"] == 400.0 and rep["charged"] == 200.0 and rep["solvency"] in "+0")
    check("bool(a run verdict) still raises — the family invariant holds",
          _refuses(lambda: bool(ran.verdict)))

    print()
    if fails:
        print(f"FAILED — {len(fails)} of {n} check(s):")
        for f in fails:
            print("  · " + f)
        return 1
    print("KOINONIA METABOLISM WITNESS HOLDS — the system captures real value, mints\n"
          "  Lumina only within its backing, gates every process on the energy budget,\n"
          "  and gives the surplus above its floor to relief — never touching the\n"
          "  backing. A body that feeds itself and tithes, all of it audited.")
    return 0


def _refuses(fn) -> bool:
    try:
        fn()
        return False
    except Exception:
        return True


if __name__ == "__main__":
    sys.exit(_witness())
