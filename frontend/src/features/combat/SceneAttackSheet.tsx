import { useMemo, useState } from "react";
import { ArrowRight, Swords } from "lucide-react";

import type { CampaignEntity } from "../../api/types";
import { Button, Modal } from "../../components/ui";
import { supportsAdvantage, type AdvantageMode } from "../systems";
import { AdvantageToggle } from "../systems/dnd5e/AdvantageToggle";
import { useCombatAttackMutation } from "../../hooks/mutations/useSceneMutations";
import { extractAttacksFromEntity } from "./combatEntityOptions";
import type { SceneRosterEntry } from "./sceneRoster";

type SceneAttackSheetProps = {
  sceneId: string;
  campaignId: string;
  gameSystem?: string;
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
  gameSystem,
  attacker,
  target,
  entities,
  disabled,
  onClose,
  onSceneUpdate,
}: SceneAttackSheetProps) {
  const [weaponIndex, setWeaponIndex] = useState(0);
  const [localError, setLocalError] = useState<string | null>(null);
  const [advantageMode, setAdvantageMode] = useState<AdvantageMode>("normal");

  const attackerEntity = entities.find((entity) => entity.id === attacker.id) ?? null;
  const attacks = useMemo(() => extractAttacksFromEntity(attackerEntity), [attackerEntity]);
  const selectedAttack = attacks[weaponIndex];

  const attackMutation = useCombatAttackMutation({ campaignId, onSceneUpdate });

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
        ...(advantageMode === "advantage" ? { advantage: true } : {}),
        ...(advantageMode === "disadvantage" ? { disadvantage: true } : {}),
      });
      onClose();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "No se pudo resolver el ataque");
    }
  }

  const isBusy = disabled || attackMutation.isPending;

  return (
    <Modal
      onClose={onClose}
      size="sm"
      className="scene-attack-sheet"
      titleId="scene-attack-title"
      header={
        <header className="scene-attack-sheet__header">
          <div className="scene-attack-sheet__header-top">
            <div className="scene-attack-sheet__title-row">
              <span className="scene-attack-sheet__icon-wrap" aria-hidden>
                <Swords size={18} />
              </span>
              <h2 id="scene-attack-title">Atacar</h2>
            </div>
            <button type="button" className="scene-attack-sheet__close" onClick={onClose} aria-label="Cerrar">
              ×
            </button>
          </div>

          <div className="scene-attack-sheet__participants" aria-label="Atacante y objetivo">
            <EntityChip entry={attacker} />
            <ArrowRight size={14} className="scene-attack-sheet__arrow" aria-hidden />
            <EntityChip entry={target} />
          </div>
        </header>
      }
      footer={
        <>
          <Button
            type="button"
            variant="secondary"
            className="scene-attack-sheet__cancel"
            onClick={onClose}
            disabled={attackMutation.isPending}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            tone="rose"
            disabled={isBusy}
            onClick={() => {
              void handleAttack();
            }}
          >
            {attackMutation.isPending ? "Atacando…" : "Atacar"}
          </Button>
        </>
      }
    >
      {supportsAdvantage(gameSystem) && (
        <div className="scene-attack-sheet__advantage">
          <AdvantageToggle value={advantageMode} onChange={setAdvantageMode} disabled={isBusy} compact />
        </div>
      )}

      {attacks.length > 0 ? (
        <div className="scene-attack-sheet__attacks" role="radiogroup" aria-label="Elegir ataque">
          {attacks.map((attack, index) => {
            const isSelected = weaponIndex === index;
            return (
              <button
                key={`${attack.name}-${index}`}
                type="button"
                role="radio"
                aria-checked={isSelected}
                className={`scene-attack-sheet__attack-card${isSelected ? " is-selected" : ""}`}
                onClick={() => setWeaponIndex(index)}
                disabled={isBusy}
              >
                <span className="scene-attack-sheet__attack-name">{attack.name}</span>
                {attack.statsLabel && (
                  <span className="scene-attack-sheet__attack-stats">{attack.statsLabel}</span>
                )}
              </button>
            );
          })}
        </div>
      ) : (
        <p className="scene-attack-sheet__empty muted">Sin ataques configurados en la ficha.</p>
      )}

      {localError && <p className="scene-attack-sheet__error">{localError}</p>}
    </Modal>
  );
}

function EntityChip({ entry }: { entry: SceneRosterEntry }) {
  return (
    <span
      className={`scene-attack-sheet__chip scene-attack-sheet__chip--${entry.entityType.toLowerCase()}${entry.playerVisibility === "hidden" || entry.playerVisibility === "unknown" ? " scene-attack-sheet__chip--hidden" : ""}`}
    >
      <span className="scene-attack-sheet__chip-badge">{entry.entityType}</span>
      <span className="scene-attack-sheet__chip-name">{entry.label}</span>
    </span>
  );
}

function getAttackRef(entity: CampaignEntity | null, rosterEntry: SceneRosterEntry): string {
  if (!entity) return rosterEntry.label;
  const identity = entity.document.identity as { name?: string } | undefined;
  return identity?.name?.trim() || rosterEntry.label;
}
