import random
import re


_DICE_PATTERN = re.compile(
    r"^(?:(\d+)d(\d+)(?:([+-]\d+))?|(\d+)([+-]\d+)?)$",
    re.IGNORECASE,
)


def roll_dice(expression: str, modifier: int = 0) -> dict:
    expression = expression.strip().lower().replace(" ", "")

    match = _DICE_PATTERN.match(expression)
    if not match:
        raise ValueError(f"Invalid dice expression: {expression}")

    if match.group(1):
        count = int(match.group(1))
        sides = int(match.group(2))
        inline_mod = int(match.group(3) or 0)
    else:
        count = 1
        sides = int(match.group(4))
        inline_mod = int(match.group(5) or 0)

    if count < 1 or sides < 1:
        raise ValueError("Dice count and sides must be positive")

    rolls = [random.randint(1, sides) for _ in range(count)]
    raw_result = sum(rolls)
    final_result = raw_result + inline_mod + modifier

    return {
        "dice_expression": expression,
        "rolls": rolls,
        "raw_result": raw_result,
        "final_result": final_result,
    }
