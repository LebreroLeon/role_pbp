import { useEffect, useState, type ReactNode } from "react";

import type { CombatInitiativeEntry, Scene } from "../../api/types";
import { Button } from "../../components/ui";
import { useRollCombatInitiativeMutation } from "../../hooks/mutations/useSceneMutations";
import type { MemberLookup } from "../scene/ChatEntry";
import {
  getCombatState,
  getCurrentCombatTurnIndex,
  getCurrentTurnPlayerId,
  getTurnOrder,
  isConflictModeActive,
  normalizeSceneState,
  type SceneStateInput,
} from "../scene/sceneState";

type InitiativeOrderPanelProps = {
  sceneId: string;
  campaignId: string;
  sceneState: SceneStateInput;
  members: MemberLookup;
  isMaster?: boolean;
  onSceneUpdate?: (scene: Scene) => void;
};

export function InitiativeOrderPanel({
  sceneId,
  campaignId,
  sceneState,
  members,
  isMaster = false,
  onSceneUpdate,
}: InitiativeOrderPanelProps) {
  const state = normalizeSceneState(sceneState);
  const combat = getCombatState(state);
  const turnOrder = getTurnOrder(state);
  const currentTurnPlayerId = getCurrentTurnPlayerId(state);
  const conflictActive = isConflictModeActive(state);
  const [manageOpen, setManageOpen] = useState(false);
  const rollInitiative = useRollCombatInitiativeMutation({ campaignId, onSceneUpdate });

  const manageModal = manageOpen ? (
    <InitiativeManageModal
      entries={
        combat.is_active && combat.initiative_order.length > 0
          ? combat.initiative_order
          : turnOrder.length > 0
            ? turnOrder.map((userId) => ({
                entity_id: userId,
                display_name: members[userId]?.display_name ?? userId.slice(0, 8),
                entity_type: members[userId]?.role === "MASTER" ? "MASTER" : "PC",
              }))
            : []
      }
      onClose={() => setManageOpen(false)}
      onSave={() => rollInitiative.mutateAsync(sceneId).then(() => setManageOpen(false))}
      isSaving={rollInitiative.isPending}
      saveError={rollInitiative.error instanceof Error ? rollInitiative.error.message : null}
    />
  ) : null;

  const manageButton = isMaster ? (
    <Button type="button" variant="secondary" className="initiative-panel__manage" onClick={() => setManageOpen(true)}>
      Gestionar iniciativa
    </Button>
  ) : null;

  if (combat.is_active && combat.initiative_order.length > 0) {
    return (
      <>
        <CombatInitiativePanel combat={combat} manageButton={manageButton} />
        {manageModal}
      </>
    );
  }

  if (turnOrder.length === 0) {
    if (!conflictActive) return null;
    return (
      <aside className="initiative-panel initiative-panel--empty" aria-label="Iniciativa">
        <h3 className="initiative-panel__title">Iniciativa</h3>
        <p className="muted">Modo conflicto activo — sin orden definido aún.</p>
        {manageButton}
        {manageModal}
      </aside>
    );
  }

  return (
    <>
      <aside className="initiative-panel" aria-label="Orden de turnos">
        <div className="initiative-panel__head">
          <h3 className="initiative-panel__title">Turno narrativo</h3>
          {manageButton}
        </div>
        <ol className="initiative-list">
          {turnOrder.map((userId) => {
            const member = members[userId];
            const isCurrent = userId === currentTurnPlayerId;
            return (
              <li key={userId} className={`initiative-entry ${isCurrent ? "is-current" : ""}`}>
                <span className="initiative-entry__marker" aria-hidden>
                  {isCurrent ? "►" : "·"}
                </span>
                <span className="initiative-entry__name">{member?.display_name ?? userId.slice(0, 8)}</span>
                {member?.role === "MASTER" && <span className="initiative-entry__tag">Máster</span>}
              </li>
            );
          })}
        </ol>
      </aside>
      {manageModal}
    </>
  );
}

function CombatInitiativePanel({
  combat,
  manageButton,
}: {
  combat: ReturnType<typeof getCombatState>;
  manageButton: ReactNode;
}) {
  const currentIndex = getCurrentCombatTurnIndex(combat);

  return (
    <aside className="initiative-panel initiative-panel--combat" aria-label="Iniciativa de combate">
      <div className="initiative-panel__head">
        <h3 className="initiative-panel__title">Iniciativa — Ronda {combat.round}</h3>
        {manageButton}
      </div>
      <ol className="initiative-list">
        {combat.initiative_order.map((entry, index) => {
          const isCurrent = index === currentIndex;
          const hpLabel =
            entry.hp_current != null && entry.hp_max != null
              ? `${entry.hp_current}/${entry.hp_max}`
              : null;
          const displayName = entry.display_name ?? entry.entity_id.slice(0, 8);

          return (
            <li
              key={entry.entity_id}
              className={`initiative-entry initiative-entry--combat ${isCurrent ? "is-current" : ""} ${entry.is_active === false ? "is-inactive" : ""}`}
            >
              <span className="initiative-entry__marker" aria-hidden>
                {isCurrent ? "►" : "·"}
              </span>
              <span className="initiative-entry__name">{displayName}</span>
              {entry.initiative_score != null && (
                <span className="initiative-entry__score">{entry.initiative_score}</span>
              )}
              {entry.entity_type && <span className="initiative-entry__tag">{entry.entity_type}</span>}
              {hpLabel && <span className="initiative-entry__hp">{hpLabel} PV</span>}
            </li>
          );
        })}
      </ol>
    </aside>
  );
}

type InitiativeManageModalProps = {
  entries: CombatInitiativeEntry[];
  onClose: () => void;
  onSave: () => Promise<void>;
  isSaving?: boolean;
  saveError?: string | null;
};

function InitiativeManageModal({
  entries,
  onClose,
  onSave,
  isSaving = false,
  saveError = null,
}: InitiativeManageModalProps) {
  const [localEntries, setLocalEntries] = useState(entries);

  useEffect(() => {
    setLocalEntries(entries);
  }, [entries]);

  function moveEntry(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= localEntries.length) return;
    const next = [...localEntries];
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item);
    setLocalEntries(next);
  }

  return (
    <div className="initiative-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="initiative-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="initiative-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="initiative-modal__header">
          <h2 id="initiative-modal-title">Gestionar iniciativa</h2>
          <button type="button" className="initiative-modal__close" onClick={onClose} aria-label="Cerrar">
            ×
          </button>
        </header>

        {localEntries.length === 0 ? (
          <p className="muted">No hay entidades en el orden de iniciativa.</p>
        ) : (
          <ol className="initiative-manage-list">
            {localEntries.map((entry, index) => (
              <li key={entry.entity_id} className="initiative-manage-item">
                <span className="initiative-manage-item__name">
                  {entry.display_name ?? entry.entity_id.slice(0, 8)}
                </span>
                {entry.entity_type && <span className="initiative-entry__tag">{entry.entity_type}</span>}
                <div className="initiative-manage-item__actions">
                  <button
                    type="button"
                    disabled={index === 0}
                    onClick={() => moveEntry(index, -1)}
                    aria-label="Subir"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    disabled={index === localEntries.length - 1}
                    onClick={() => moveEntry(index, 1)}
                    aria-label="Bajar"
                  >
                    ↓
                  </button>
                </div>
              </li>
            ))}
          </ol>
        )}

        <footer className="initiative-modal__footer">
          <p className="muted initiative-modal__note">
            Guardar tira iniciativa para las entidades en escena y actualiza el orden de combate.
          </p>
          {saveError && <p className="error">{saveError}</p>}
          <div className="initiative-modal__buttons">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSaving}>
              Cerrar
            </Button>
            <Button
              type="button"
              disabled={isSaving}
              onClick={() => {
                void onSave().catch(() => undefined);
              }}
            >
              {isSaving ? "Guardando…" : "Guardar orden"}
            </Button>
          </div>
        </footer>
      </div>
    </div>
  );
}
