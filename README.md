# koinonia

**Mutual-aid debt relief as verified math. A 0% lending circle and a funded
forgiveness covenant — both create no money, and both say so.**

Pure Python. One dependency: [krisis](https://github.com/drkoll/krisis), for the
three-valued solvency and fund verdicts.

```bash
pip install koinonia
python3 -m koinonia            # all three witnesses
```

κοινωνία — fellowship; the shared-resource community of Acts 2:44, "all things in
common."

## The one fact that sets the whole design

**A token you mint pays zero of a dollar debt.** A creditor is owed dollars and
accepts a minted token only if someone trades real dollars for it — so the dollars
come from a *buyer*, never from the mint. Minting a million Lumina leaves a $10,000
debt at exactly $10,000. There is no exception for good intentions: issuance moves
the price, not the goods.

So this engine does not mint wealth. It does the thing that actually frees people:
it **eliminates interest through mutual aid**, and the math is pure.

## The circle — rotating savings, conserves exactly

N members each pay C per round into a pot; each round one member receives the whole
pot; rotate until all have received.

```python
from koinonia import Circle, pot, net_position
c = Circle(members=tuple(f"m{i}" for i in range(12)), contribution=200.0,
           order=tuple(range(12)))
pot(c)                       # 2400.0 — the whole pot each round
net_position(c, "m0")        # 0.0 — every member nets zero; no money is created
```

Over a full cycle everyone pays C·N and receives C·N. It **conserves member by
member.** What it creates is *timing*: the early recipient gets an interest-free
loan, the late recipient a savings plan, and nobody is a lender at interest.

**Why that destroys debt** — a member with $2,400 of card debt at 24% APR:

```python
from koinonia import interest_saved
interest_saved(2400.0, apr=0.24, term_months=12, payment=200.0)   # 361.36
```

An early circle payout kills the card at 0% cost. **~$361 of interest destroyed
per early slot**, converting 24% debt into 0% mutual obligation. This is legal and
real — Mission Asset Fund runs exactly this in the US and reports to the credit
bureaus.

**Timing is the value, so slots go by lottery.** `position_value` prices the
early-slot advantage as real money; a fair circle assigns slots by lot, not favour.

## The release — forgiveness at a covenant ratio, funded by real gift

Debt cancellation has a scriptural precedent: the **Jubilee** of Leviticus 25, the
"release" (ἄφεσις) Christ proclaims in Luke 4:18. The question that shaped this
module was whether to spare **two-thirds** of a debt, echoing Revelation, where a
third is struck and two-thirds spared (Rev 8–9).

**The ratio is a covenant the community chooses — not a number the math derives.**
Scripture may inspire the fraction; pretending a formula hands you 2/3 would be
numerology. So it's a parameter, and the math's only job is to keep the mercy
honest:

```python
from koinonia import Covenant, relief
cov = Covenant(spared_fraction=2/3, fund=6000.0)
r = relief(cov, 9000.0)
r.spared, r.borne            # (6000.0, 3000.0) — and they sum back to 9000
```

**Whatever is spared must be funded.** Sparing two-thirds of a $9,000 debt is
$6,000 of *real donated money* — a tithe, alms, a matching fund. The mercy costs
exactly what it relieves; nothing vanishes for free, and `Relief` refuses any split
that doesn't reconstitute the whole debt.

**The leverage is real but modest** — a dollar of fund lifts *more* than a dollar
of burden, because the spared principal would have accrued interest the member now
never pays:

```python
from koinonia import burden_lifted
burden_lifted(6000.0, apr=0.24, years=2)   # ~9226 — about 1.5×, not a miracle
```

**And the trade is explicit.** A more generous ratio frees fewer people per dollar:

```python
from koinonia import members_freed
members_freed(Covenant(1/3, 10000.0), 9000.0)   # 3.33 members fully freed
members_freed(Covenant(2/3, 10000.0), 9000.0)   # 1.67 — deeper mercy, less reach
```

## Three-valued throughout — pending is not default

```python
from koinonia import solvency, fund_status
# a round: PLUS solvent · ZERO pending · MINUS default (with the shortfall named)
# a fund:  PLUS funded  · ZERO partial · MINUS unbacked ("relief that isn't funded
#          is not relief")
```

The real failure mode — a member takes an early payout and stops contributing — is
a first-class MINUS with the exposure named (`default_shortfall`), never smoothed
over. That honesty is the difference between mutual aid and a scam.

## The capture layer — value from removing waste, not creating it

The most efficient *licit* capture is not generation — it is netting away the
flows that do no net work. A owes B, B owes C, C owes A, each $100: three
transactions, $300 moved, and every net position is **zero**. The circulation
cancels entirely — a loop current that does no work, pure loss to friction.

```python
from koinonia import capture_report, Obligation
cap, verdict = capture_report(obligations, fee=0.30)
cap.line()   # "300 → 39 transfers (87% removed), $78.30 in fees captured"
```

On a realistic graph — 40 parties, 300 obligations — netting removes **87% of the
transactions**. Net positions sum to zero (Kirchhoff), so nothing is conjured; the
captured value is real fees saved by removing waste. **Entropy is the control
knob:** each transaction leaks a fee, so the transaction count *is* the settlement's
entropy, and netting minimizes it.

**One honest limit, named:** reducing to `(creditors + debtors − 1)` transfers is
easy and always available; finding the *absolute* fewest is NP-hard. The verdict is
PLUS on "settles correctly and conserves," never on "provably minimal."

**The float, and the kenosis.** Money in escrow during a cycle earns licit
time-value. And `distribute_kenotic` enforces the posture in code — **the operator's
take must be zero**; captured fees and float flow to the members:

```python
distribute_kenotic(captured, members, operator_take=1.0)  # raises — self-emptying
```

**Waste becomes fertilizer.** The captured fees plus the float feed the `aphesis`
relief fund — the eliminated friction of one cycle becomes the funded forgiveness
of the next. Value that was leaking away is composted into debt relief.

## Where brightchain earns its place

The number-one way a lending circle dies is the organizer taking the pot and
vanishing. Sealing every contribution and payout on a tamper-evident ledger removes
the organizer's ability to lie — which is what lets a circle scale past people who
already trust each other. That's the honest crypto use: **provenance, not minting.**
A "Lumina" here is a `Share` — a claim on a real pot, backed one-to-one by a real
contribution, never conjured.

## Honest scope

- **It creates no money.** Every function conserves; the witnesses assert it. The
  power is interest elimination and pooled timing, not wealth generation.
- **The relief fund must be real.** Forgiveness is funded by gift, and an unfunded
  covenant is a MINUS. This engine cannot make donations appear.
- **Default is a real risk, modelled not hidden.** An early defaulter leaves the
  others exposed; the amount is computed, and mitigations (collateral, staggered
  trust, credit-building slots) are policy the community layers on top.
- **Not legal or financial advice.** A real circle in the US touches lending and
  securities law; this is the math, not the compliance.
