import { useMemo, useState, type MouseEvent } from "react";
import { Plus, Swords, UserMinus } from "lucide-react";

import type { CampaignEntity, Scene } from "../../api/types";
import { Button, Modal, Tooltip } from "../../components/ui";
import { getGameSystemProfile } from "../campaign/gameSystems";
import {
  withNpcPlayerVisibility,
  type NpcPlayerVisibility,
} from "../entities/entityDefaults";
import { NpcVisibilityControl } from "../entities/NpcVisibilityControl";
import type { SceneStateInput } from "../scene/sceneState";
import { useUpdateEntityMutation } from "../../hooks/mutations/useEntityMutations";
import { useAddPlayerToSceneMutation, useScenePresenceMutation } from "../../hooks/mutations/useSceneMutations";
import { SceneAttackSheet } from "./SceneAttackSheet";
import {
  buildSceneRoster,
  getOffSceneNpcs,
  getOffScenePcs,
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
  const offScenePcs = useMemo(() => getOffScenePcs(sceneState, entities), [sceneState, entities]);

  const [selectedAttackerId, setSelectedAttackerId] = useState<string | null>(null);
  const [attackPair, setAttackPair] = useState<AttackPair | null>(null);
  const [addToSceneOpen, setAddToSceneOpen] = useState(false);
  const [addToSceneTab, setAddToSceneTab] = useState<"npc" | "pc">("npc");
  const [presenceError, setPresenceError] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ entry: SceneRosterEntry; x: number; y: number } | null>(null);

  const presenceMutation = useScenePresenceMutation({ campaignId, onSceneUpdate });
  const addPlayerMutation = useAddPlayerToSceneMutation({ campaignId, onSceneUpdate });
  const updateEntityMutation = useUpdateEntityMutation(campaignId);

  const presencePending =
    presenceMutation.isPending || addPlayerMutation.isPending || updateEntityMutation.isPending;

  const selectedAttacker = roster.find((entry) => entry.id === selectedAttackerId) ?? null;

  if (roster.length === 0 && !isMaster) {
    return null;
  }

  async function handleAddNpc(entityId: string) {
    setPresenceError(null);
    try {
      await presenceMutation.mutateAsync({
        sceneId,
        add: [{ entity_id: entityId, is_hidden_from_players: false }],
      });
      setAddToSceneOpen(false);
    } catch (err) {
      setPresenceError(err instanceof Error ? err.message : "No se pudo añadir el NPC");
    }
  }

  async function handleNpcVisibilityChange(entry: SceneRosterEntry, visibility: NpcPlayerVisibility) {
    if (entry.entityType !== "NPC") return;
    const entity = entities.find((item) => item.id === entry.id);
    if (!entity) return;

    setPresenceError(null);
    try {
      await updateEntityMutation.mutateAsync({
        entityId: entry.id,
        document: withNpcPlayerVisibility(entity.document, visibility),
      });
    } catch (err) {
      setPresenceError(err instanceof Error ? err.message : "No se pudo cambiar la visibilidad");
    }
  }

  async function handleAddPc(entityId: string) {
    setPresenceError(null);
    try {
      await addPlayerMutation.mutateAsync({ sceneId, entity_id: entityId });
      setAddToSceneOpen(false);
    } catch (err) {
      setPresenceError(err instanceof Error ? err.message : "No se pudo añadir el jugador");
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
                  <Tooltip
                    content={
                      canClick ? (isMaster ? "Seleccionar o atacar" : "Atacar") : undefined
                    }
                  >
                    <button
                      type="button"
                      className={`scene-roster__entry ${isSelectedAttacker ? "is-attacker" : ""} ${canClick ? "is-actionable" : ""}`}
                      onClick={() => handleEntryClick(entry)}
                      onContextMenu={(event) => handleContextMenu(event, entry)}
                      disabled={!canClick && !isMaster}
                      aria-pressed={isSelectedAttacker}
                      aria-label={
                        canClick ? (isMaster ? "Seleccionar o atacar" : "Atacar") : undefined
                      }
                    >
                    <span className={`scene-roster__badge scene-roster__badge--${entry.entityType.toLowerCase()}`}>
                      {entry.entityType}
                    </span>
                    <span className="scene-roster__name">
                      <span className="scene-roster__name-row">
                        <span>{entry.label}</span>
                        {isMaster && entry.playerVisibilityLabel && entry.playerVisibility && (
                          <span
                            className={`scene-roster__visibility scene-roster__visibility--${entry.playerVisibility}`}
                          >
                            {entry.playerVisibilityLabel}
                          </span>
                        )}
                      </span>
                    </span>
                    {entry.hpLabel && <span className="scene-roster__hp">{entry.hpLabel} PV</span>}
                    {combatEnabled && canClick && (
                      <Swords size={14} className="scene-roster__attack-icon" aria-hidden />
                    )}
                  </button>
                  </Tooltip>

                  {isMaster && entry.entityType === "NPC" && entry.playerVisibility && (
                    <div className="scene-roster__master-actions">
                      <NpcVisibilityControl
                        value={entry.playerVisibility}
                        onChange={(visibility) => {
                          void handleNpcVisibilityChange(entry, visibility);
                        }}
                        disabled={disabled || presencePending}
                        compact
                        className="scene-roster__visibility-control"
                      />
                      <Tooltip content="Quitar de escena">
                        <button
                          type="button"
                          className="scene-roster__icon-btn scene-roster__icon-btn--danger"
                          aria-label="Quitar de escena"
                          disabled={disabled || presencePending}
                          onClick={() => {
                            void handleRemoveNpc(entry.id);
                          }}
                        >
                          <UserMinus size={14} />
                        </button>
                      </Tooltip>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}

        {isMaster && offScenePcs.length > 0 && (
          <div className="scene-roster__off-scene">
            <h4 className="scene-roster__subtitle">Jugadores fuera de escena</h4>
            <ul className="scene-roster__off-list">
              {offScenePcs.map((pc) => {
                const name =
                  (pc.document.identity as { name?: string } | undefined)?.name ?? pc.id.slice(0, 8);
                return (
                  <li key={pc.id} className="scene-roster__off-item">
                    <span>{name}</span>
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={disabled || presencePending}
                      onClick={() => {
                        void handleAddPc(pc.id);
                      }}
                    >
                      Añadir a escena
                    </Button>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {presenceError && <p className="scene-roster__error">{presenceError}</p>}

        {isMaster && (
          <div className="scene-roster__footer">
            <Button
              type="button"
              variant="secondary"
              className="scene-roster__add-btn"
              disabled={disabled || presencePending}
              onClick={() => {
                setAddToSceneTab(offSceneNpcs.length > 0 ? "npc" : "pc");
                setAddToSceneOpen(true);
              }}
            >
              <Plus size={14} aria-hidden />
              Añadir a escena
            </Button>
          </div>
        )}
      </aside>

      {addToSceneOpen && (
        <Modal
          title="Añadir a escena"
          titleId="add-to-scene-title"
          onClose={() => setAddToSceneOpen(false)}
          size="sm"
        >
          <div className="scene-roster-modal__tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={addToSceneTab === "npc"}
              className={addToSceneTab === "npc" ? "is-active" : undefined}
              onClick={() => setAddToSceneTab("npc")}
            >
              NPCs
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={addToSceneTab === "pc"}
              className={addToSceneTab === "pc" ? "is-active" : undefined}
              onClick={() => setAddToSceneTab("pc")}
            >
              Jugadores
            </button>
          </div>

          {addToSceneTab === "npc" ? (
            offSceneNpcs.length === 0 ? (
              <p className="muted">No hay NPCs fuera de escena.</p>
            ) : (
              <ul className="scene-roster-modal__list">
                {offSceneNpcs.map((npc) => {
                  const name =
                    (npc.document.identity as { name?: string } | undefined)?.name ?? npc.id.slice(0, 8);
                  return (
                    <li key={npc.id} className="scene-roster-modal__item">
                      <span>{name}</span>
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={presencePending}
                        onClick={() => {
                          void handleAddNpc(npc.id);
                        }}
                      >
                        Añadir
                      </Button>
                    </li>
                  );
                })}
              </ul>
            )
          ) : offScenePcs.length === 0 ? (
            <p className="muted">No hay jugadores fuera de escena.</p>
          ) : (
            <ul className="scene-roster-modal__list">
              {offScenePcs.map((pc) => {
                const name =
                  (pc.document.identity as { name?: string } | undefined)?.name ?? pc.id.slice(0, 8);
                return (
                  <li key={pc.id} className="scene-roster-modal__item">
                    <span>{name}</span>
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={presencePending}
                      onClick={() => {
                        void handleAddPc(pc.id);
                      }}
                    >
                      Añadir
                    </Button>
                  </li>
                );
              })}
            </ul>
          )}
        </Modal>
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
          gameSystem={gameSystem ?? undefined}
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
