"""D&D 5e dice helpers — shared by plugin and generic scene rolls."""

import random


def roll_d20(*, advantage: bool = False, disadvantage: bool = False) -> tuple[list[int], int]:
    """Roll 1d20, or 2d20 keep high/low when advantage/disadvantage."""
    if advantage and disadvantage:
        advantage = False
        disadvantage = False

    if advantage or disadvantage:
        rolls = [random.randint(1, 20), random.randint(1, 20)]
        chosen = max(rolls) if advantage else min(rolls)
        return rolls, chosen

    roll = random.randint(1, 20)
    return [roll], roll
