import { Button, Switch } from "../../components/ui";
import { supportsAdvantage, isSingleD20Expression, type AdvantageMode } from "../systems";
import { AdvantageToggle } from "../systems/dnd5e/AdvantageToggle";

type DiceRollerProps = {
  expression: string;
  onExpressionChange: (value: string) => void;
  onRoll: (options?: { advantage?: boolean; disadvantage?: boolean; masterOnly?: boolean }) => void;
  disabled: boolean;
  gameSystem?: string;
  advantageMode?: AdvantageMode;
  onAdvantageModeChange?: (mode: AdvantageMode) => void;
  isMaster?: boolean;
  masterOnly?: boolean;
  onMasterOnlyChange?: (value: boolean) => void;
};

export function DiceRoller({
  expression,
  onExpressionChange,
  onRoll,
  disabled,
  gameSystem,
  advantageMode = "normal",
  onAdvantageModeChange,
  isMaster = false,
  masterOnly = false,
  onMasterOnlyChange,
}: DiceRollerProps) {
  const showAdvantage =
    supportsAdvantage(gameSystem) && isSingleD20Expression(expression);

  function handleRoll() {
    const rollOptions = {
      ...(showAdvantage && advantageMode === "advantage" ? { advantage: true } : {}),
      ...(showAdvantage && advantageMode === "disadvantage" ? { disadvantage: true } : {}),
      ...(isMaster && masterOnly ? { masterOnly: true } : {}),
    };
    onRoll(Object.keys(rollOptions).length > 0 ? rollOptions : undefined);
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
      {isMaster && onMasterOnlyChange && (
        <Switch
          checked={masterOnly}
          onCheckedChange={onMasterOnlyChange}
          label="Tirada en secreto"
          description="Solo visible para el Máster"
          tone="rose"
          disabled={disabled}
        />
      )}
      <Button variant="secondary" type="button" onClick={handleRoll} disabled={disabled}>
        Tirar dados
      </Button>
    </div>
  );
}
