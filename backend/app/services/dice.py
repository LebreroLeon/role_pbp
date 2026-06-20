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


def format_raw_roll_summary(expression: str, result: dict) -> str:
    """Human-readable summary for generic dice expressions (e.g. 3d20+5)."""
    rolls = result.get("rolls") or []
    total = result.get("final_result", 0)
    raw = result.get("raw_result", 0)
    misc = total - raw if isinstance(total, int) and isinstance(raw, int) else 0

    if len(rolls) > 1:
        line = " + ".join(str(r) for r in rolls)
        if misc:
            line += f" {misc:+d}"
        return f"{line} = {total}"

    if len(rolls) == 1:
        base_expr = expression.strip()
        for sep in ("+", "-"):
            if sep in base_expr:
                base_expr = base_expr.split(sep, 1)[0].strip()
                break
        line = f"{base_expr}={rolls[0]}"
        if misc:
            line += f" {misc:+d}"
        return f"{line} = {total}"

    return f"{expression} = {total}"


def build_generic_roll_details(expression: str, result: dict) -> dict:
    rolls = result.get("rolls") or []
    raw = result.get("raw_result", 0)
    misc = result.get("final_result", 0) - raw
    modifier_breakdown: list[dict] = []

    if rolls:
        sides = result.get("dice_sides")
        if len(rolls) == 1 and sides:
            label = f"1d{sides}={rolls[0]}"
        elif len(rolls) > 1:
            label = " + ".join(str(r) for r in rolls)
        else:
            label = str(rolls[0])
        modifier_breakdown.append({"label": label, "value": raw, "rolls": rolls})

    if misc:
        modifier_breakdown.append({"label": "Modificador", "value": misc})

    return {
        "expression": expression,
        "modifier": misc,
        "modifier_breakdown": modifier_breakdown,
        "rolls": rolls,
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
    misc_mod = inline_mod + modifier
    modifier_breakdown: dict = {}
    if misc_mod:
        modifier_breakdown["misc_mod"] = misc_mod

    return {
        "dice_expression": expression,
        "rolls": rolls,
        "raw_result": raw_result,
        "final_result": final_result,
        "inline_modifier": inline_mod,
        "extra_modifier": modifier,
        "modifier_breakdown": modifier_breakdown,
        "dice_count": count,
        "dice_sides": sides,
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
    roll_details = dict(result.details)
    if result.rolls and "rolls" not in roll_details:
        roll_details["rolls"] = result.rolls
    if "expression" not in roll_details:
        roll_details["expression"] = result.expression
    payload = {
        "dice_expression": result.expression,
        "rolls": result.rolls,
        "raw_result": raw_result,
        "final_result": result.total,
        "contextual": True,
        "game_system": game_system,
        "roll_type": result.roll_type,
        "success": result.success,
        "roll_details": roll_details,
        "chat_summary": result.chat_summary,
    }
    if roll_details.get("modifier_breakdown"):
        payload["modifier_breakdown"] = roll_details["modifier_breakdown"]
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
