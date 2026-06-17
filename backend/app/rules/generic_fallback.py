from pydantic import BaseModel, Field

from app.rules.base import GameSystemPlugin, RollContext, RollResult
from app.services import dice as dice_service


class GenericSheet(BaseModel):
    """Placeholder sheet for systems without a dedicated plugin."""

    notes: str = ""


class GenericFallbackPlugin(GameSystemPlugin):
    system_id = "generic"
    dice_mode = "generic"
    sheet_schema_version = "0.0.0"

    def validate_pc_sheet(self, sheet: dict) -> BaseModel:
        return GenericSheet.model_validate(sheet)

    def validate_npc_sheet(self, sheet: dict) -> BaseModel:
        return GenericSheet.model_validate(sheet)

    def default_pc_sheet(self) -> dict:
        return GenericSheet().model_dump()

    def default_npc_sheet(self, power_scale: str = "medium") -> dict:
        return GenericSheet(notes=f"power_scale={power_scale}").model_dump()

    def resolve_roll(
        self,
        roll_type: str,
        actor_sheet: dict,
        context: RollContext,
    ) -> RollResult:
        expression = context.expression or "1d20"
        modifier = context.modifier_override or 0
        raw = dice_service.roll_dice(expression, modifier=modifier)
        total = raw["final_result"]
        return RollResult(
            roll_type=roll_type,
            expression=raw["dice_expression"],
            rolls=raw["rolls"],
            total=total,
            success=None,
            details={"modifier": modifier, "raw_result": raw["raw_result"]},
            chat_summary=f"Tirada {roll_type}: {expression} = {total}",
        )
