import { useMemo, useState } from "react";

import type { CampaignEntity } from "../../api/types";
import { Button } from "../../components/ui";
import { useCombatAttackMutation } from "../../hooks/mutations/useSceneMutations";
import { extractAttacksFromEntity } from "./combatEntityOptions";
import type { SceneRosterEntry } from "./sceneRoster";

type SceneAttackSheetProps = {
  sceneId: string;
  campaignId: string;
  attacker: SceneRosterEntry;
  target: SceneRosterEntry;
  entities: CampaignEntity[];
  disabled?: boolean;
  onClose: () => void;
  onSceneUpdate: (scene: import("../../api/types").Scene) => void;
};

export function SceneAttackSheet({
  sceneId,
  campaignId,
  attacker,
  target,
  entities,
  disabled,
  onClose,
  onSceneUpdate,
}: SceneAttackSheetProps) {
  const [weaponIndex, setWeaponIndex] = useState(0);
  const [localError, setLocalError] = useState<string | null>(null);

  const attackerEntity = entities.find((entity) => entity.id === attacker.id) ?? null;
  const attacks = useMemo(() => extractAttacksFromEntity(attackerEntity), [attackerEntity]);
  const selectedAttack = attacks[weaponIndex];

  const attackMutation = useCombatAttackMutation({ campaignId, onSceneUpdate });

  const attackerLabel = attacker.isHiddenFromPlayers ? attacker.maskedLabel : attacker.label;
  const targetLabel = target.isHiddenFromPlayers ? target.maskedLabel : target.label;

  async function handleAttack() {
    setLocalError(null);
    try {
      await attackMutation.mutateAsync({
        sceneId,
        attacker_ref: attackerEntity ? getAttackRef(attackerEntity, attacker) : attacker.label,
        defender_ref: getAttackRef(
          entities.find((entity) => entity.id === target.id) ?? null,
          target,
        ),
        weapon_name: selectedAttack?.name,
        attack_index: attacks.length > 0 ? weaponIndex : undefined,
      });
      onClose();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "No se pudo resolver el ataque");
    }
  }

  return (
    <div className="scene-attack-backdrop" role="presentation" onClick={onClose}>
      <div
        className="scene-attack-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="scene-attack-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="scene-attack-sheet__header">
          <h2 id="scene-attack-title">Atacar</h2>
          <button type="button" className="scene-attack-sheet__close" onClick={onClose} aria-label="Cerrar">
            ×
          </button>
        </header>

        <p className="scene-attack-sheet__pair">
          <strong>{attackerLabel}</strong>
          <span aria-hidden>→</span>
          <strong>{targetLabel}</strong>
        </p>

        {attacks.length > 1 && (
          <div className="scene-attack-sheet__attacks" role="radiogroup" aria-label="Elegir ataque">
            {attacks.map((attack, index) => (
              <label key={`${attack.name}-${index}`} className="scene-attack-sheet__attack-option">
                <input
                  type="radio"
                  name="attack-choice"
                  value={index}
                  checked={weaponIndex === index}
                  onChange={() => setWeaponIndex(index)}
                  disabled={disabled || attackMutation.isPending}
                />
                <span>{attack.name}</span>
              </label>
            ))}
          </div>
        )}

        {attacks.length === 1 && <p className="muted scene-attack-sheet__weapon">{attacks[0].name}</p>}

        {localError && <p className="scene-attack-sheet__error">{localError}</p>}

        <footer className="scene-attack-sheet__footer">
          <Button type="button" variant="secondary" onClick={onClose} disabled={attackMutation.isPending}>
            Cancelar
          </Button>
          <Button
            type="button"
            disabled={disabled || attackMutation.isPending}
            onClick={() => {
              void handleAttack();
            }}
          >
            {attackMutation.isPending ? "Atacando…" : "Atacar"}
          </Button>
        </footer>
      </div>
    </div>
  );
}

function getAttackRef(entity: CampaignEntity | null, rosterEntry: SceneRosterEntry): string {
  if (!entity) return rosterEntry.label;
  const identity = entity.document.identity as { name?: string } | undefined;
  return identity?.name?.trim() || rosterEntry.label;
}
