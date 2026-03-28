from __future__ import annotations

from backend.rules.whirlpool_shared import WhirlpoolRuleBase


class WhirlpoolRule(WhirlpoolRuleBase):
    """
    Outward Whirlpool Vortex

    A center-aware excitable vortex rule with outward propagation and clockwise swirl.
    """
    name = "whirlpool"
    display_name = "Excitable: Outward Whirlpool"
    description = (
        "Clockwise outward-spiraling vortex centered on a one- or two-cell eye. "
        "Excitation is driven outward from inner neighbors and shaped by tangential "
        "clockwise bias across multiple radial bands. Source cells emit directional "
        "pulses without advancing through the cycle."
    )
