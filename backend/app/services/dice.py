import random
import re

from app.rules.base import RollContext, RollResult

_DICE_PATTERN = re.compile(
    r"^(?:(\d+)d(\d+)(?:([+-]\d+))?|(\d+)([+-]\d+)?)$",
    re.IGNORECASE,
)

_ROLL_CONTEXT_FIELDS = {
    "ability",
    "skill",
    "attack_name",
    "attack_index",
    "dc",
    "target_ac",
    "advantage",
    "disadvantage",
    "modifier_override",
    "expression",
}


def roll_dice(
    expression: str,
    modifier: int = 0,
    *,
    game_system: str | None = None,
    sheet: dict | None = None,
    roll_type: str | None = None,
    context: dict | None = None,
) -> dict:
    """Roll dice. Delegates to the RuleEngine plugin when contextual args are provided."""
    if game_system and roll_type and sheet is not None:
        return _roll_contextual(game_system, sheet, roll_type, context or {}, expression, modifier)

    return _roll_raw(expression, modifier)


def _roll_raw(expression: str, modifier: int = 0) -> dict:
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


def _build_roll_context(context: dict, expression: str, modifier: int) -> RollContext:
    kwargs = {key: context[key] for key in _ROLL_CONTEXT_FIELDS if key in context}
    if "expression" not in kwargs and expression:
        kwargs["expression"] = expression
    if "modifier_override" not in kwargs and modifier:
        kwargs["modifier_override"] = modifier
    return RollContext(**kwargs)


def _roll_result_to_dict(result: RollResult, game_system: str) -> dict:
    raw_result = sum(result.rolls) if result.rolls else None
    payload = {
        "dice_expression": result.expression,
        "rolls": result.rolls,
        "raw_result": raw_result,
        "final_result": result.total,
        "contextual": True,
        "game_system": game_system,
        "roll_type": result.roll_type,
        "success": result.success,
        "roll_details": result.details,
        "chat_summary": result.chat_summary,
    }
    return payload


def _roll_contextual(
    game_system: str,
    sheet: dict,
    roll_type: str,
    context: dict,
    expression: str,
    modifier: int,
) -> dict:
    from app.rules.registry import get_plugin

    plugin = get_plugin(game_system)
    roll_context = _build_roll_context(context, expression, modifier)
    result = plugin.resolve_roll(roll_type, sheet, roll_context)
    return _roll_result_to_dict(result, game_system)
