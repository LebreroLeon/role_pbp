import { Button } from "../../components/ui";

type DiceRollerProps = {
  expression: string;
  onExpressionChange: (value: string) => void;
  onRoll: () => void;
  disabled: boolean;
};

export function DiceRoller({ expression, onExpressionChange, onRoll, disabled }: DiceRollerProps) {
  return (
    <div className="dice-row">
      <input value={expression} onChange={(event) => onExpressionChange(event.target.value)} disabled={disabled} />
      <Button variant="secondary" type="button" onClick={onRoll} disabled={disabled}>
        Tirar dados
      </Button>
    </div>
  );
}
