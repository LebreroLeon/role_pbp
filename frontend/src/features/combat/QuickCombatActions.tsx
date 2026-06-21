import { useMemo, useState } from "react";

import type { CampaignEntity, Scene } from "../../api/types";
import { Button } from "../../components/ui";
import { useCombatAttackMutation } from "../../hooks/mutations/useSceneMutations";
import { getGameSystemProfile } from "../campaign/gameSystems";
import type { SceneStateInput } from "../scene/sceneState";
import {
  buildCombatEntityOptions,
  extractAttacksFromEntity,
  findPlayerPcOption,
} from "./combatEntityOptions";

type QuickCombatActionsProps = {
  sceneId: string;
  campaignId: string;
  gameSystem: string | null | undefined;
  sceneState: SceneStateInput;
  entities: CampaignEntity[];
  currentUserId: string;
  isMaster: boolean;
  disabled?: boolean;
  onSceneUpdate: (scene: Scene) => void;
};

export function QuickCombatActions({
  sceneId,
  campaignId,
  gameSystem,
  sceneState,
  entities,
  currentUserId,
  isMaster,
  disabled,
  onSceneUpdate,
}: QuickCombatActionsProps) {
  const profile = getGameSystemProfile(gameSystem);
  const combatEnabled = Boolean(profile?.combatEnabled);

  const entityOptions = useMemo(
    () => buildCombatEntityOptions(sceneState, entities),
    [sceneState, entities],
  );

  const myPcOption = useMemo(
    () => findPlayerPcOption(entityOptions, currentUserId),
    [entityOptions, currentUserId],
  );

  const [attackerId, setAttackerId] = useState("");
  const [defenderId, setDefenderId] = useState("");
  const [weaponIndex, setWeaponIndex] = useState(0);
  const [localError, setLocalError] = useState<string | null>(null);

  const effectiveAttackerId = isMaster ? attackerId : (myPcOption?.id ?? "");
  const attackerEntity = entities.find((entity) => entity.id === effectiveAttackerId) ?? null;
  const attacks = useMemo(() => extractAttacksFromEntity(attackerEntity), [attackerEntity]);

  const targetOptions = useMemo(
    () => entityOptions.filter((option) => option.id !== effectiveAttackerId),
    [entityOptions, effectiveAttackerId],
  );

  const attackMutation = useCombatAttackMutation({ campaignId, onSceneUpdate });

  if (!combatEnabled || entityOptions.length < 2) {
    return null;
  }

  const attackerOption = entityOptions.find((option) => option.id === effectiveAttackerId);
  const defenderOption = targetOptions.find((option) => option.id === defenderId);
  const selectedAttack = attacks[weaponIndex];
  const canAttack =
    Boolean(attackerOption && defenderOption && effectiveAttackerId !== defenderId) &&
    !disabled &&
    !attackMutation.isPending &&
    (isMaster || Boolean(myPcOption));

  async function handleAttack() {
    if (!attackerOption || !defenderOption) return;

    setLocalError(null);
    try {
      await attackMutation.mutateAsync({
        sceneId,
        attacker_ref: attackerOption.label,
        defender_ref: defenderOption.label,
        weapon_name: selectedAttack?.name,
        attack_index: attacks.length > 0 ? weaponIndex : undefined,
      });
      if (!isMaster) {
        setDefenderId("");
      }
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "No se pudo resolver el ataque");
    }
  }

  return (
    <section className="quick-combat" aria-label="Acciones de combate">
      <h3 className="quick-combat__title">Combate rápido</h3>

      {!isMaster && !myPcOption && (
        <p className="quick-combat__hint muted">Necesitas un personaje en escena para atacar.</p>
      )}

      <div className="quick-combat__grid">
        {isMaster ? (
          <label className="quick-combat__field">
            <span>Atacante</span>
            <select
              value={attackerId}
              onChange={(event) => {
                setAttackerId(event.target.value);
                setWeaponIndex(0);
                if (event.target.value === defenderId) setDefenderId("");
              }}
              disabled={disabled || attackMutation.isPending}
            >
              <option value="">Elegir atacante…</option>
              {entityOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label} ({option.entityType})
                </option>
              ))}
            </select>
          </label>
        ) : (
          myPcOption && (
            <p className="quick-combat__attacker">
              Atacante: <strong>{myPcOption.label}</strong>
            </p>
          )
        )}

        <label className="quick-combat__field">
          <span>Objetivo</span>
          <select
            value={defenderId}
            onChange={(event) => setDefenderId(event.target.value)}
            disabled={disabled || attackMutation.isPending || !effectiveAttackerId}
          >
            <option value="">Elegir objetivo…</option>
            {targetOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label} ({option.entityType})
              </option>
            ))}
          </select>
        </label>

        {attacks.length > 0 && (
          <label className="quick-combat__field">
            <span>Ataque</span>
            <select
              value={weaponIndex}
              onChange={(event) => setWeaponIndex(Number(event.target.value))}
              disabled={disabled || attackMutation.isPending || !effectiveAttackerId}
            >
              {attacks.map((attack, index) => (
                <option key={`${attack.name}-${index}`} value={index}>
                  {attack.name}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {localError && <p className="quick-combat__error">{localError}</p>}

      <Button
        type="button"
        variant="secondary"
        className="quick-combat__submit"
        disabled={!canAttack}
        onClick={handleAttack}
      >
        {attackMutation.isPending ? "Atacando…" : "Atacar"}
      </Button>
    </section>
  );
}
