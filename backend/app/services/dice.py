import random
import re

from app.rules.base import RollContext, RollResult

_DICE_TERM_RE = re.compile(r"([+-]?)(\d+)d(\d+)", re.IGNORECASE)
_MODIFIER_TERM_RE = re.compile(r"([+-])(\d+)(?!d)", re.IGNORECASE)
_LEGACY_SIDES_RE = re.compile(r"^(\d+)([+-]\d+)?$", re.IGNORECASE)

_D20_ROLL_TYPES = frozenset({"dnd5e"})

# Plugins for these roll types derive dice from sheet data. The API default
# dice_expression ("1d20") must not override that unless context["expression"]
# is set explicitly (e.g. doubled crit damage).
_SHEET_RESOLVED_ROLL_TYPES = frozenset(
    {
        "ability_check",
        "saving_throw",
        "skill_check",
        "stat_check",
        "attribute_check",
        "attack_roll",
        "attack",
        "damage",
        "healing",
        "initiative",
        "death_save",
        "rouse_check",
        "discipline_check",
    }
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


def _parse_dice_expression(expression: str) -> tuple[list[tuple[int, int]], int]:
    """Parse NdX terms and flat modifiers, e.g. 1d20+3+2d6 or 2d6+1d4+2."""
    expr = expression.strip().lower().replace(" ", "")
    if not expr:
        raise ValueError("Invalid dice expression: (empty)")

    if "d" not in expr:
        legacy = _LEGACY_SIDES_RE.match(expr)
        if legacy:
            sides = int(legacy.group(1))
            modifier = int(legacy.group(2) or 0)
            if sides < 1:
                raise ValueError(f"Invalid dice expression: {expression}")
            return [(1, sides)], modifier
        raise ValueError(f"Invalid dice expression: {expression}")

    dice_groups: list[tuple[int, int]] = []
    flat_modifier = 0
    pos = 0
    first = True

    while pos < len(expr):
        dice_match = _DICE_TERM_RE.match(expr, pos)
        if dice_match:
            sign = dice_match.group(1)
            if sign == "-":
                raise ValueError(f"Negative dice not supported: {expression}")
            count = int(dice_match.group(2))
            sides = int(dice_match.group(3))
            if count < 1 or sides < 1:
                raise ValueError("Dice count and sides must be positive")
            dice_groups.append((count, sides))
            pos = dice_match.end()
            first = False
            continue

        mod_match = _MODIFIER_TERM_RE.match(expr, pos)
        if mod_match:
            if first:
                raise ValueError(f"Invalid dice expression: {expression}")
            sign = mod_match.group(1)
            value = int(mod_match.group(2))
            flat_modifier += value if sign == "+" else -value
            pos = mod_match.end()
            first = False
            continue

        raise ValueError(f"Invalid dice expression: {expression}")

    if not dice_groups:
        raise ValueError(f"Invalid dice expression: {expression}")

    return dice_groups, flat_modifier


def is_single_d20_expression(expression: str) -> bool:
    """True when expression is exactly one d20 (optional inline modifier)."""
    try:
        dice_groups, _ = _parse_dice_expression(expression)
    except ValueError:
        return False
    return len(dice_groups) == 1 and dice_groups[0] == (1, 20)


def roll_dice(
    expression: str,
    modifier: int = 0,
    *,
    game_system: str | None = None,
    sheet: dict | None = None,
    roll_type: str | None = None,
    context: dict | None = None,
    advantage: bool = False,
    disadvantage: bool = False,
) -> dict:
    """Roll dice. Delegates to the RuleEngine plugin when contextual args are provided."""
    if game_system and roll_type and sheet is not None:
        return _roll_contextual(game_system, sheet, roll_type, context or {}, expression, modifier)

    if (advantage or disadvantage) and game_system in _D20_ROLL_TYPES and is_single_d20_expression(expression):
        return _roll_d20_expression(expression, modifier, advantage=advantage, disadvantage=disadvantage)

    return _roll_raw(expression, modifier)


def _roll_d20_expression(
    expression: str,
    modifier: int = 0,
    *,
    advantage: bool = False,
    disadvantage: bool = False,
) -> dict:
    from app.rules.dnd5e.rolls import roll_d20

    expression = expression.strip().lower().replace(" ", "")
    dice_groups, inline_mod = _parse_dice_expression(expression)
    if dice_groups != [(1, 20)]:
        raise ValueError(f"Invalid d20 expression: {expression}")
    rolls, natural = roll_d20(advantage=advantage, disadvantage=disadvantage)
    misc_mod = inline_mod + modifier
    final_result = natural + misc_mod

    dice_label = "2d20 (ventaja)" if advantage else "2d20 (desventaja)" if disadvantage else "1d20"
    sign = f"{misc_mod:+d}" if misc_mod else ""
    expr = f"{dice_label}{sign}"
    summary = f"{dice_label}={natural}"
    if misc_mod:
        summary += f" {sign}"
    summary += f" = {final_result}"

    modifier_breakdown: list[dict] = []
    if len(rolls) > 1:
        modifier_breakdown.append({"label": dice_label, "value": natural, "rolls": rolls})
    else:
        modifier_breakdown.append({"label": f"1d20={natural}", "value": natural, "rolls": rolls})
    if misc_mod:
        modifier_breakdown.append({"label": "Modificador", "value": misc_mod})

    return {
        "dice_expression": expr,
        "rolls": rolls,
        "raw_result": natural,
        "final_result": final_result,
        "inline_modifier": inline_mod,
        "extra_modifier": modifier,
        "modifier_breakdown": {"misc_mod": misc_mod} if misc_mod else {},
        "dice_count": len(rolls),
        "dice_sides": 20,
        "roll_details": {
            "natural_roll": natural,
            "modifier": misc_mod,
            "advantage": advantage,
            "disadvantage": disadvantage,
            "modifier_breakdown": modifier_breakdown,
            "rolls": rolls,
            "expression": expr,
        },
        "chat_summary": summary,
    }


def _roll_raw(expression: str, modifier: int = 0) -> dict:
    expression = expression.strip().lower().replace(" ", "")
    dice_groups, inline_mod = _parse_dice_expression(expression)

    rolls: list[int] = []
    dice_sides: int | None = None
    for count, sides in dice_groups:
        if dice_sides is None:
            dice_sides = sides
        elif dice_sides != sides:
            dice_sides = None
        rolls.extend(random.randint(1, sides) for _ in range(count))

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
        "dice_count": len(rolls),
        "dice_sides": dice_sides,
    }


def _normalize_roll_type(roll_type: str | None) -> str:
    return (roll_type or "").strip().lower().replace(" ", "_")


def _build_roll_context(
    context: dict,
    expression: str,
    modifier: int,
    *,
    roll_type: str | None = None,
) -> RollContext:
    kwargs = {key: context[key] for key in _ROLL_CONTEXT_FIELDS if key in context}
    if "expression" not in kwargs and expression:
        if _normalize_roll_type(roll_type) not in _SHEET_RESOLVED_ROLL_TYPES:
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
    roll_context = _build_roll_context(context, expression, modifier, roll_type=roll_type)
    result = plugin.resolve_roll(roll_type, sheet, roll_context)
    return _roll_result_to_dict(result, game_system)
