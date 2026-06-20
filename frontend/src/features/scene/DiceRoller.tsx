import { Button } from "../../components/ui";
import { supportsAdvantage, isSingleD20Expression, type AdvantageMode } from "../systems";
import { AdvantageToggle } from "../systems/dnd5e/AdvantageToggle";

type DiceRollerProps = {
  expression: string;
  onExpressionChange: (value: string) => void;
  onRoll: (options?: { advantage?: boolean; disadvantage?: boolean }) => void;
  disabled: boolean;
  gameSystem?: string;
  advantageMode?: AdvantageMode;
  onAdvantageModeChange?: (mode: AdvantageMode) => void;
};

export function DiceRoller({
  expression,
  onExpressionChange,
  onRoll,
  disabled,
  gameSystem,
  advantageMode = "normal",
  onAdvantageModeChange,
}: DiceRollerProps) {
  const showAdvantage =
    supportsAdvantage(gameSystem) && isSingleD20Expression(expression);

  function handleRoll() {
    if (!showAdvantage || advantageMode === "normal") {
      onRoll();
      return;
    }
    onRoll({
      advantage: advantageMode === "advantage",
      disadvantage: advantageMode === "disadvantage",
    });
  }

  return (
    <div className="dice-row">
      <input value={expression} onChange={(event) => onExpressionChange(event.target.value)} disabled={disabled} />
      {showAdvantage && onAdvantageModeChange && (
        <AdvantageToggle
          value={advantageMode}
          onChange={onAdvantageModeChange}
          disabled={disabled}
          compact
        />
      )}
      <Button variant="secondary" type="button" onClick={handleRoll} disabled={disabled}>
        Tirar dados
      </Button>
    </div>
  );
}
