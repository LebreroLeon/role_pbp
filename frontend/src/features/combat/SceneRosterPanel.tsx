import { useMemo, useState, type MouseEvent } from "react";
import { Eye, EyeOff, Plus, Swords, UserMinus } from "lucide-react";

import type { CampaignEntity, Scene } from "../../api/types";
import { Button } from "../../components/ui";
import { getGameSystemProfile } from "../campaign/gameSystems";
import type { SceneStateInput } from "../scene/sceneState";
import { useScenePresenceMutation } from "../../hooks/mutations/useSceneMutations";
import { SceneAttackSheet } from "./SceneAttackSheet";
import {
  buildSceneRoster,
  getOffSceneNpcs,
  HIDDEN_NPC_HINT,
  type SceneRosterEntry,
} from "./sceneRoster";

type SceneRosterPanelProps = {
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

type AttackPair = {
  attacker: SceneRosterEntry;
  target: SceneRosterEntry;
};

export function SceneRosterPanel({
  sceneId,
  campaignId,
  gameSystem,
  sceneState,
  entities,
  currentUserId,
  isMaster,
  disabled,
  onSceneUpdate,
}: SceneRosterPanelProps) {
  const profile = getGameSystemProfile(gameSystem);
  const combatEnabled = Boolean(profile?.combatEnabled);

  const roster = useMemo(
    () => buildSceneRoster(sceneState, entities, isMaster),
    [sceneState, entities, isMaster],
  );

  const myPc = useMemo(
    () => roster.find((entry) => entry.entityType === "PC" && entry.userId === currentUserId) ?? null,
    [roster, currentUserId],
  );

  const offSceneNpcs = useMemo(() => getOffSceneNpcs(sceneState, entities), [sceneState, entities]);

  const [selectedAttackerId, setSelectedAttackerId] = useState<string | null>(null);
  const [attackPair, setAttackPair] = useState<AttackPair | null>(null);
  const [addNpcOpen, setAddNpcOpen] = useState(false);
  const [presenceError, setPresenceError] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ entry: SceneRosterEntry; x: number; y: number } | null>(null);

  const presenceMutation = useScenePresenceMutation({ campaignId, onSceneUpdate });

  const selectedAttacker = roster.find((entry) => entry.id === selectedAttackerId) ?? null;

  if (roster.length === 0 && !isMaster) {
    return null;
  }

  async function handleAddNpc(entityId: string, hidden = false) {
    setPresenceError(null);
    try {
      await presenceMutation.mutateAsync({
        sceneId,
        add: [{ entity_id: entityId, is_hidden_from_players: hidden }],
      });
      setAddNpcOpen(false);
    } catch (err) {
      setPresenceError(err instanceof Error ? err.message : "No se pudo añadir el NPC");
    }
  }

  async function handleRemoveNpc(entityId: string) {
    setPresenceError(null);
    try {
      await presenceMutation.mutateAsync({ sceneId, remove: [entityId] });
    } catch (err) {
      setPresenceError(err instanceof Error ? err.message : "No se pudo quitar el NPC");
    }
  }

  async function handleToggleHidden(entry: SceneRosterEntry) {
    setPresenceError(null);
    const reveal = entry.isHiddenFromPlayers;
    try {
      await presenceMutation.mutateAsync({
        sceneId,
        add: [{ entity_id: entry.id, is_hidden_from_players: !reveal }],
      });
    } catch (err) {
      setPresenceError(err instanceof Error ? err.message : "No se pudo cambiar la visibilidad");
    }
  }

  function openAttack(attacker: SceneRosterEntry, target: SceneRosterEntry) {
    if (attacker.id === target.id) return;
    setAttackPair({ attacker, target });
    setContextMenu(null);
  }

  function handleEntryClick(entry: SceneRosterEntry) {
    if (!combatEnabled || disabled) return;
    setContextMenu(null);

    if (isMaster) {
      if (!selectedAttacker) {
        setSelectedAttackerId(entry.id);
        return;
      }
      if (selectedAttacker.id === entry.id) {
        setSelectedAttackerId(null);
        return;
      }
      openAttack(selectedAttacker, entry);
      return;
    }

    if (!myPc) return;
    if (entry.id === myPc.id) return;
    openAttack(myPc, entry);
  }

  function handleContextMenu(event: MouseEvent, entry: SceneRosterEntry) {
    if (!combatEnabled || disabled) return;
    event.preventDefault();
    setContextMenu({ entry, x: event.clientX, y: event.clientY });
  }

  function handleContextAttack(entry: SceneRosterEntry) {
    if (isMaster) {
      if (selectedAttacker && selectedAttacker.id !== entry.id) {
        openAttack(selectedAttacker, entry);
        return;
      }
      setSelectedAttackerId(entry.id);
      setContextMenu(null);
      return;
    }
    if (myPc && entry.id !== myPc.id) {
      openAttack(myPc, entry);
    }
  }

  return (
    <>
      <aside className="scene-roster" aria-label="En escena">
        <div className="scene-roster__head">
          <h3 className="scene-roster__title">En escena</h3>
          {combatEnabled && isMaster && (
            <span className="scene-roster__hint muted">Toca atacante → objetivo</span>
          )}
        </div>

        {combatEnabled && !isMaster && !myPc && (
          <p className="scene-roster__note muted">Necesitas un personaje en escena para atacar.</p>
        )}

        {combatEnabled && isMaster && selectedAttacker && (
          <p className="scene-roster__attacker-pick">
            Atacante: <strong>{selectedAttacker.label}</strong>
            <button
              type="button"
              className="scene-roster__clear-attacker"
              onClick={() => setSelectedAttackerId(null)}
            >
              Cambiar
            </button>
          </p>
        )}

        {roster.length === 0 ? (
          <p className="muted scene-roster__empty">Nadie en escena aún.</p>
        ) : (
          <ul className="scene-roster__list">
            {roster.map((entry) => {
              const isSelectedAttacker = selectedAttackerId === entry.id;
              const canClick =
                combatEnabled &&
                !disabled &&
                (isMaster || (myPc && entry.id !== myPc.id));

              return (
                <li key={entry.id}>
                  <button
                    type="button"
                    className={`scene-roster__entry ${isSelectedAttacker ? "is-attacker" : ""} ${canClick ? "is-actionable" : ""}`}
                    onClick={() => handleEntryClick(entry)}
                    onContextMenu={(event) => handleContextMenu(event, entry)}
                    disabled={!canClick && !isMaster}
                    aria-pressed={isSelectedAttacker}
                    title={
                      canClick
                        ? isMaster
                          ? "Seleccionar o atacar"
                          : "Atacar"
                        : undefined
                    }
                  >
                    <span className={`scene-roster__badge scene-roster__badge--${entry.entityType.toLowerCase()}`}>
                      {entry.entityType}
                    </span>
                    <span className="scene-roster__name">
                      <span>{entry.label}</span>
                      {entry.isHiddenFromPlayers && entry.label !== entry.maskedLabel && (
                        <span className="scene-roster__masked">{HIDDEN_NPC_HINT}</span>
                      )}
                    </span>
                    {entry.hpLabel && <span className="scene-roster__hp">{entry.hpLabel} PV</span>}
                    {combatEnabled && canClick && (
                      <Swords size={14} className="scene-roster__attack-icon" aria-hidden />
                    )}
                  </button>

                  {isMaster && entry.entityType === "NPC" && (
                    <div className="scene-roster__master-actions">
                      <button
                        type="button"
                        className="scene-roster__icon-btn"
                        aria-label={entry.isHiddenFromPlayers ? "Revelar NPC" : "Ocultar NPC"}
                        title={entry.isHiddenFromPlayers ? "Revelar" : "Ocultar"}
                        disabled={disabled || presenceMutation.isPending}
                        onClick={() => {
                          void handleToggleHidden(entry);
                        }}
                      >
                        {entry.isHiddenFromPlayers ? <Eye size={14} /> : <EyeOff size={14} />}
                      </button>
                      <button
                        type="button"
                        className="scene-roster__icon-btn scene-roster__icon-btn--danger"
                        aria-label="Quitar de escena"
                        title="Quitar de escena"
                        disabled={disabled || presenceMutation.isPending}
                        onClick={() => {
                          void handleRemoveNpc(entry.id);
                        }}
                      >
                        <UserMinus size={14} />
                      </button>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}

        {presenceError && <p className="scene-roster__error">{presenceError}</p>}

        {isMaster && (
          <div className="scene-roster__footer">
            <Button
              type="button"
              variant="secondary"
              className="scene-roster__add-btn"
              disabled={disabled || presenceMutation.isPending}
              onClick={() => setAddNpcOpen(true)}
            >
              <Plus size={14} aria-hidden />
              Añadir NPC
            </Button>
          </div>
        )}
      </aside>

      {addNpcOpen && (
        <div className="scene-roster-modal-backdrop" role="presentation" onClick={() => setAddNpcOpen(false)}>
          <div
            className="scene-roster-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="add-npc-title"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="scene-roster-modal__header">
              <h2 id="add-npc-title">Añadir NPC a escena</h2>
              <button
                type="button"
                className="scene-roster-modal__close"
                onClick={() => setAddNpcOpen(false)}
                aria-label="Cerrar"
              >
                ×
              </button>
            </header>

            {offSceneNpcs.length === 0 ? (
              <p className="muted">No hay NPCs fuera de escena.</p>
            ) : (
              <ul className="scene-roster-modal__list">
                {offSceneNpcs.map((npc) => {
                  const name =
                    (npc.document.identity as { name?: string } | undefined)?.name ?? npc.id.slice(0, 8);
                  return (
                    <li key={npc.id} className="scene-roster-modal__item">
                      <span>{name}</span>
                      <div className="scene-roster-modal__item-actions">
                        <Button
                          type="button"
                          variant="secondary"
                          disabled={presenceMutation.isPending}
                          onClick={() => {
                            void handleAddNpc(npc.id, false);
                          }}
                        >
                          Visible
                        </Button>
                        <Button
                          type="button"
                          variant="secondary"
                          disabled={presenceMutation.isPending}
                          onClick={() => {
                            void handleAddNpc(npc.id, true);
                          }}
                        >
                          Oculto
                        </Button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      )}

      {contextMenu && (
        <div
          className="scene-roster-context"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          role="menu"
        >
          {isMaster && (
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                setSelectedAttackerId(contextMenu.entry.id);
                setContextMenu(null);
              }}
            >
              Marcar como atacante
            </button>
          )}
          <button type="button" role="menuitem" onClick={() => handleContextAttack(contextMenu.entry)}>
            Atacar
          </button>
          <button type="button" role="menuitem" onClick={() => setContextMenu(null)}>
            Cancelar
          </button>
        </div>
      )}

      {attackPair && (
        <SceneAttackSheet
          sceneId={sceneId}
          campaignId={campaignId}
          attacker={attackPair.attacker}
          target={attackPair.target}
          entities={entities}
          disabled={disabled}
          onClose={() => setAttackPair(null)}
          onSceneUpdate={onSceneUpdate}
        />
      )}
    </>
  );
}
