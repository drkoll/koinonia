"""koinonia — mutual-aid debt relief that creates no money, and says so.

    from koinonia import Circle, solvency          # the lending circle
    from koinonia import Covenant, relief          # the funded release

κοινωνία, fellowship — the shared-resource community of Acts 2:44. A token you mint
pays zero of a dollar debt (conservation); what actually frees people is a rotating
lending circle (0% interest, ancient, legal) and a funded release at a covenant
ratio. Every dollar spared is real donated money; nothing vanishes for free.

Depends on krisis for the three-valued solvency and fund verdicts — pending is not
default, and unfunded relief is refused as no relief at all.
"""

from __future__ import annotations

from koinonia.aphesis import (
    Covenant,
    Relief,
    burden_lifted,
    fund_status,
    members_freed,
    relief,
)
from koinonia.netting import (
    Capture,
    Obligation,
    Transfer,
    capture_report,
    distribute_kenotic,
    entropy,
    float_yield,
    net_positions,
    settle,
)
from koinonia.circle import (
    Circle,
    Share,
    default_shortfall,
    interest_saved,
    net_position,
    position_value,
    pot,
    schedule,
    solvency,
)

__version__ = "0.1.0"
__all__ = [
    # the circle — rotating savings, conserves exactly
    "Circle", "Share", "pot", "schedule", "net_position", "position_value",
    "interest_saved", "solvency", "default_shortfall",
    # the release — funded forgiveness at a covenant ratio
    "Covenant", "Relief", "relief", "burden_lifted", "members_freed", "fund_status",
    # netting — the capture layer: remove waste, keep the float, operator takes nothing
    "Obligation", "Transfer", "net_positions", "settle", "entropy",
    "Capture", "capture_report", "float_yield", "distribute_kenotic",
    "__version__",
]
