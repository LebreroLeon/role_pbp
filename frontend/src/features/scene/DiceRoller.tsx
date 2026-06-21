import { Dices } from "lucide-react";

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
    <section className="dice-panel" aria-label="Tirada de dados">
      <div className="dice-panel__header">
        <Dices size={15} aria-hidden />
        <h4>Tirada de dados</h4>
      </div>
      <div className="dice-panel__body">
        <div className="dice-panel__primary">
          <input
            className="dice-panel__expression"
            value={expression}
            onChange={(event) => onExpressionChange(event.target.value)}
            disabled={disabled}
            aria-label="Expresión de dados"
          />
          <Button
            variant="secondary"
            type="button"
            className="dice-panel__roll-btn"
            onClick={handleRoll}
            disabled={disabled}
          >
            Tirar dados
          </Button>
        </div>
        {(showAdvantage || (isMaster && onMasterOnlyChange)) && (
          <div className="dice-panel__options">
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
          </div>
        )}
      </div>
    </section>
  );
}
