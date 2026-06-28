import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import type { CampaignEntity, CombatInitiativeEntry, Scene } from "../../api/types";
import { Button, Modal, Switch, Tooltip } from "../../components/ui";
import {
  useAdvancePbpTurnMutation,
  useRollCombatInitiativeMutation,
  useUpdateSceneTurnManagementMutation,
} from "../../hooks/mutations/useSceneMutations";
import type { MemberLookup } from "../scene/ChatEntry";
import {
  getCombatState,
  getCurrentCombatTurnIndex,
  getCurrentTurnEntityId,
  canUserAdvancePbpTurn,
  isConflictModeActive,
  isPbpEnabled,
  normalizeSceneState,
  resolveCurrentTurnLabel,
  type SceneStateInput,
} from "../scene/sceneState";
import {
  buildSceneRoster,
  enrichInitiativeEntry,
  getSceneRosterNotInInitiative,
  resolveInitiativeEntryDisplay,
  rosterEntryToInitiativeEntry,
  type SceneRosterEntry,
} from "./sceneRoster";

type InitiativeOrderPanelProps = {
  sceneId: string;
  campaignId: string;
  sceneState: SceneStateInput;
  entities: CampaignEntity[];
  members: MemberLookup;
  currentUserId?: string;
  isMaster?: boolean;
  onSceneUpdate?: (scene: Scene) => void;
};

function buildDisplayEntries(
  sceneState: SceneStateInput,
  entities: CampaignEntity[],
  isMaster: boolean,
): CombatInitiativeEntry[] {
  const normalized = normalizeSceneState(sceneState);
  if (normalized.combat.initiative_order.length > 0) {
    return normalized.combat.initiative_order.map((entry) =>
      enrichInitiativeEntry(entry, entities, sceneState, isMaster),
    );
  }

  return buildSceneRoster(sceneState, entities, isMaster).map((entry) => ({
    entity_id: entry.id,
    display_name: entry.label,
    entity_type: entry.entityType,
  }));
}

function buildManageEntries(
  sceneState: SceneStateInput,
  entities: CampaignEntity[],
  isMaster: boolean,
): CombatInitiativeEntry[] {
  return buildDisplayEntries(sceneState, entities, isMaster);
}

export function InitiativeOrderPanel({
  sceneId,
  campaignId,
  sceneState,
  entities,
  members,
  currentUserId,
  isMaster = false,
  onSceneUpdate,
}: InitiativeOrderPanelProps) {
  const state = normalizeSceneState(sceneState);
  const combat = getCombatState(state);
  const currentTurnEntityId = getCurrentTurnEntityId(state);
  const conflictActive = isConflictModeActive(state);
  const pbpOn = isPbpEnabled(state);
  const turnLabel = resolveCurrentTurnLabel(sceneState, members, entities, isMaster);
  const [manageOpen, setManageOpen] = useState(false);

  const rollInitiative = useRollCombatInitiativeMutation({ campaignId, onSceneUpdate });
  const updateTurnManagement = useUpdateSceneTurnManagementMutation({ campaignId, onSceneUpdate });
  const advancePbpTurn = useAdvancePbpTurnMutation({ campaignId, onSceneUpdate });

  const displayEntries = useMemo(
    () => buildDisplayEntries(sceneState, entities, isMaster),
    [sceneState, entities, isMaster],
  );

  const manageEntries = useMemo(
    () => buildManageEntries(sceneState, entities, isMaster),
    [sceneState, entities, isMaster],
  );

  const isTurnBusy = updateTurnManagement.isPending || advancePbpTurn.isPending;

  const canAdvanceTurn =
    pbpOn &&
    displayEntries.length > 0 &&
    currentUserId != null &&
    canUserAdvancePbpTurn(sceneState, currentUserId, isMaster, entities);

  async function handleTogglePbp(enabled: boolean) {
    await updateTurnManagement.mutateAsync({ sceneId, pbp_enabled: enabled });
  }

  async function handleAdvanceTurn() {
    await advancePbpTurn.mutateAsync({ sceneId });
  }

  async function handleAssignTurn(entityId: string) {
    await updateTurnManagement.mutateAsync({ sceneId, current_turn_entity_id: entityId });
  }

  const pbpTurnControls = canAdvanceTurn ? (
    <div className="initiative-panel__master-actions">
      <Button
        type="button"
        variant="secondary"
        className="initiative-panel__advance"
        disabled={isTurnBusy}
        onClick={() => {
          void handleAdvanceTurn().catch(() => undefined);
        }}
      >
        {advancePbpTurn.isPending ? "Avanzando…" : "Siguiente turno"}
      </Button>
    </div>
  ) : null;

  const manageModal = manageOpen ? (
    <InitiativeManageModal
      entries={manageEntries}
      entities={entities}
      sceneState={sceneState}
      isMaster={isMaster}
      onClose={() => setManageOpen(false)}
      onRollAll={(entityIds) =>
        rollInitiative
          .mutateAsync({ sceneId, activateCombat: false, entityIds })
          .then(() => undefined)
          .catch(() => undefined)
      }
      onSave={(entries) => {
        const turnStillValid =
          currentTurnEntityId != null &&
          entries.some((entry) => entry.entity_id === currentTurnEntityId);
        return updateTurnManagement.mutateAsync({
          sceneId,
          order_source: "manual",
          initiative_order: entries,
          ...(turnStillValid ? { current_turn_entity_id: currentTurnEntityId } : {}),
          resort: false,
        });
      }}
      isSaving={updateTurnManagement.isPending}
      saveError={
        updateTurnManagement.error instanceof Error ? updateTurnManagement.error.message : null
      }
      isRolling={rollInitiative.isPending}
    />
  ) : null;

  const manageButton = isMaster ? (
    <Button type="button" variant="secondary" className="initiative-panel__manage" onClick={() => setManageOpen(true)}>
      Gestionar iniciativa
    </Button>
  ) : null;

  const pbpControls = isMaster ? (
    <Switch
      className="initiative-panel__pbp-toggle"
      checked={pbpOn}
      onCheckedChange={(enabled) => {
        void handleTogglePbp(enabled).catch(() => undefined);
      }}
      disabled={updateTurnManagement.isPending}
      label="Modo PBP"
      description="Turnos estrictos"
      tone="teal"
    />
  ) : null;

  const turnBanner =
    pbpOn && turnLabel ? (
      <p className="initiative-panel__turn-banner" role="status">
        Turno de <strong>{turnLabel}</strong>
      </p>
    ) : null;

  if (combat.is_active && combat.initiative_order.length > 0) {
    return (
      <>
        <CombatInitiativePanel
          combat={combat}
          sceneState={sceneState}
          entities={entities}
          manageButton={manageButton}
          pbpControls={pbpControls}
          turnBanner={turnBanner}
          masterTurnControls={pbpTurnControls}
          isMaster={isMaster}
          pbpOn={pbpOn}
          isTurnBusy={isTurnBusy}
          onAssignTurn={handleAssignTurn}
        />
        {manageModal}
      </>
    );
  }

  if (displayEntries.length === 0) {
    if (!conflictActive && !pbpOn) return null;
    return (
      <aside className="initiative-panel initiative-panel--empty" aria-label="Iniciativa">
        <h3 className="initiative-panel__title">Turnos</h3>
        {pbpControls}
        {turnBanner}
        <p className="muted">
          {pbpOn
            ? "PBP activo — añade PCs o PNJs a la escena para definir el orden."
            : "Modo conflicto activo — sin orden definido aún."}
        </p>
        {manageButton}
        {manageModal}
      </aside>
    );
  }

  const currentIndex = displayEntries.findIndex((entry) => entry.entity_id === currentTurnEntityId);
  const panelTitle = combat.initiative_order.length > 0 ? "Orden de turnos" : "Turno narrativo";

  return (
    <>
      <aside className="initiative-panel" aria-label="Orden de turnos PBP">
        <div className="initiative-panel__head">
          <h3 className="initiative-panel__title">{panelTitle}</h3>
          {manageButton}
        </div>
        {pbpControls}
        {turnBanner}
        <EntityTurnList
          entries={displayEntries}
          entities={entities}
          sceneState={sceneState}
          currentIndex={currentIndex >= 0 ? currentIndex : 0}
          isMaster={isMaster}
          pbpOn={pbpOn}
          isTurnBusy={isTurnBusy}
          onAssignTurn={handleAssignTurn}
        />
        {pbpTurnControls}
      </aside>
      {manageModal}
    </>
  );
}

type EntityTurnListProps = {
  entries: CombatInitiativeEntry[];
  entities: CampaignEntity[];
  sceneState: SceneStateInput;
  currentIndex: number;
  isMaster: boolean;
  pbpOn: boolean;
  isTurnBusy: boolean;
  onAssignTurn: (entityId: string) => Promise<void>;
  showCombatDetails?: boolean;
  combatHpById?: Map<string, { current?: number; max?: number }>;
};

function EntityTurnList({
  entries,
  entities,
  sceneState,
  currentIndex,
  isMaster,
  pbpOn,
  isTurnBusy,
  onAssignTurn,
  showCombatDetails = false,
  combatHpById,
}: EntityTurnListProps) {
  return (
    <ol className="initiative-list">
      {entries.map((entry, index) => {
        const isCurrent = index === currentIndex;
        const hp = combatHpById?.get(entry.entity_id);
        const hpLabel =
          hp?.current != null && hp?.max != null ? `${hp.current}/${hp.max}` : null;
        const { label: displayName, entityType } = resolveInitiativeEntryDisplay(
          entry,
          entities,
          sceneState,
          isMaster,
        );
        const entity = entities?.find((item) => item.id === entry.entity_id);
        const stateFlags = entity?.document.state_flags as
          | { is_incapacitated?: boolean; is_dead?: boolean }
          | undefined;
        const hpAboveZero = hp?.current != null && hp.current > 0;
        const statusMarker = !hpAboveZero && stateFlags?.is_dead
          ? "☠"
          : !hpAboveZero && stateFlags?.is_incapacitated
            ? "💤"
            : null;
        const canAssign = isMaster && pbpOn && !isCurrent;

        return (
          <li
            key={entry.entity_id}
            className={`initiative-entry ${showCombatDetails ? "initiative-entry--combat" : ""} ${isCurrent ? "is-current" : ""} ${entry.is_active === false ? "is-inactive" : ""} ${canAssign ? "is-assignable" : ""}`}
          >
            {canAssign ? (
              <Tooltip content={`Dar turno a ${displayName}`}>
                <button
                  type="button"
                  className="initiative-entry__assign"
                  disabled={isTurnBusy}
                  aria-label={`Dar turno a ${displayName}`}
                  onClick={() => {
                    void onAssignTurn(entry.entity_id).catch(() => undefined);
                  }}
                >
                <span className="initiative-entry__marker" aria-hidden>
                  ·
                </span>
                <span className="initiative-entry__name">
                  {statusMarker ? `${statusMarker} ` : ""}
                  {displayName}
                </span>
                {entry.initiative_score != null && (
                  <span className="initiative-entry__score">{entry.initiative_score}</span>
                )}
                {entityType && <span className="initiative-entry__tag">{entityType}</span>}
                {hpLabel && <span className="initiative-entry__hp">{hpLabel} PV</span>}
              </button>
              </Tooltip>
            ) : (
              <>
                <span className="initiative-entry__marker" aria-hidden>
                  {isCurrent ? "►" : "·"}
                </span>
                <span className="initiative-entry__name">
                  {statusMarker ? `${statusMarker} ` : ""}
                  {displayName}
                </span>
                {entry.initiative_score != null && (
                  <span className="initiative-entry__score">{entry.initiative_score}</span>
                )}
                {entityType && <span className="initiative-entry__tag">{entityType}</span>}
                {hpLabel && <span className="initiative-entry__hp">{hpLabel} PV</span>}
              </>
            )}
          </li>
        );
      })}
    </ol>
  );
}

function CombatInitiativePanel({
  combat,
  sceneState,
  entities,
  manageButton,
  pbpControls,
  turnBanner,
  masterTurnControls,
  isMaster,
  pbpOn,
  isTurnBusy,
  onAssignTurn,
}: {
  combat: ReturnType<typeof getCombatState>;
  sceneState: SceneStateInput;
  entities: CampaignEntity[];
  manageButton: ReactNode;
  pbpControls: ReactNode;
  turnBanner: ReactNode;
  masterTurnControls: ReactNode;
  isMaster: boolean;
  pbpOn: boolean;
  isTurnBusy: boolean;
  onAssignTurn: (entityId: string) => Promise<void>;
}) {
  const currentIndex = getCurrentCombatTurnIndex(combat);
  const combatHpById = new Map(
    combat.initiative_order.map((entry) => [
      entry.entity_id,
      { current: entry.hp_current, max: entry.hp_max },
    ]),
  );

  return (
    <aside className="initiative-panel initiative-panel--combat" aria-label="Iniciativa de combate">
      <div className="initiative-panel__head">
        <h3 className="initiative-panel__title">Iniciativa — Ronda {combat.round}</h3>
        {manageButton}
      </div>
      {pbpControls}
      {turnBanner}
      <EntityTurnList
        entries={combat.initiative_order}
        entities={entities}
        sceneState={sceneState}
        currentIndex={currentIndex}
        isMaster={isMaster}
        pbpOn={pbpOn}
        isTurnBusy={isTurnBusy}
        onAssignTurn={onAssignTurn}
        showCombatDetails
        combatHpById={combatHpById}
      />
      {masterTurnControls}
    </aside>
  );
}

const INITIATIVE_AUTOSAVE_MS = 400;

function initiativeEntriesMatch(
  a: CombatInitiativeEntry[],
  b: CombatInitiativeEntry[],
): boolean {
  if (a.length !== b.length) return false;
  return a.every((entry, index) => {
    const other = b[index];
    return (
      entry.entity_id === other.entity_id && entry.initiative_score === other.initiative_score
    );
  });
}

type InitiativeManageModalProps = {
  entries: CombatInitiativeEntry[];
  entities: CampaignEntity[];
  sceneState: SceneStateInput;
  isMaster: boolean;
  onClose: () => void;
  onRollAll: (entityIds: string[]) => Promise<void>;
  onSave: (entries: CombatInitiativeEntry[]) => Promise<unknown>;
  isSaving?: boolean;
  isRolling?: boolean;
  saveError?: string | null;
};

function InitiativeManageModal({
  entries,
  entities,
  sceneState,
  isMaster,
  onClose,
  onRollAll,
  onSave,
  isSaving = false,
  isRolling = false,
  saveError = null,
}: InitiativeManageModalProps) {
  const [localEntries, setLocalEntries] = useState(entries);
  const [showSaved, setShowSaved] = useState(false);
  const isBusy = isSaving || isRolling;
  const onSaveRef = useRef(onSave);
  const skipAutoSaveRef = useRef(false);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const savedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const entriesRef = useRef(entries);
  const localEntriesRef = useRef(localEntries);

  onSaveRef.current = onSave;
  entriesRef.current = entries;
  localEntriesRef.current = localEntries;

  useEffect(() => {
    setLocalEntries(entries);
    skipAutoSaveRef.current = true;
  }, [entries]);

  useEffect(() => {
    return () => {
      if (savedTimerRef.current) clearTimeout(savedTimerRef.current);
    };
  }, []);

  const flushPendingSave = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    const pending = localEntriesRef.current;
    if (!initiativeEntriesMatch(pending, entriesRef.current)) {
      void onSaveRef.current(pending)
        .then(() => {
          setShowSaved(true);
          if (savedTimerRef.current) clearTimeout(savedTimerRef.current);
          savedTimerRef.current = setTimeout(() => setShowSaved(false), 2000);
        })
        .catch(() => undefined);
    }
  }, []);

  useEffect(() => {
    if (skipAutoSaveRef.current) {
      skipAutoSaveRef.current = false;
      return;
    }
    if (initiativeEntriesMatch(localEntries, entries)) return;

    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(() => {
      debounceTimerRef.current = null;
      void onSaveRef.current(localEntries)
        .then(() => {
          setShowSaved(true);
          if (savedTimerRef.current) clearTimeout(savedTimerRef.current);
          savedTimerRef.current = setTimeout(() => setShowSaved(false), 2000);
        })
        .catch(() => undefined);
    }, INITIATIVE_AUTOSAVE_MS);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = null;
      }
    };
  }, [localEntries, entries]);

  useEffect(() => () => flushPendingSave(), [flushPendingSave]);

  function handleClose() {
    flushPendingSave();
    onClose();
  }

  function moveEntry(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= localEntries.length) return;
    const next = [...localEntries];
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item);
    setLocalEntries(next);
  }

  function updateInitiativeScore(index: number, rawValue: string) {
    const score = rawValue === "" ? null : Number.parseInt(rawValue, 10);
    const next = localEntries.map((entry, entryIndex) =>
      entryIndex === index
        ? {
            ...entry,
            initiative_score: score == null || Number.isNaN(score) ? null : score,
          }
        : entry,
    );
    setLocalEntries(next);
  }

  const sceneNotInTrack = useMemo(
    () =>
      getSceneRosterNotInInitiative(
        sceneState,
        entities,
        isMaster,
        localEntries.map((entry) => entry.entity_id),
      ),
    [sceneState, entities, isMaster, localEntries],
  );

  function addEntryFromScene(rosterEntry: SceneRosterEntry) {
    setLocalEntries((current) => [...current, rosterEntryToInitiativeEntry(rosterEntry)]);
  }

  function removeEntry(index: number) {
    setLocalEntries((current) => current.filter((_, entryIndex) => entryIndex !== index));
  }

  const saveStatusLabel = isSaving ? "Guardando…" : showSaved ? "Guardado" : null;

  return (
    <Modal
      title="Gestionar iniciativa"
      titleId="initiative-modal-title"
      onClose={handleClose}
      size="md"
      footer={
        <>
          <p className="muted initiative-modal__note">
            Los cambios se guardan solos. Tirar iniciativa ordena por valor (mayor primero); usa las
            flechas para ajustar el orden.
          </p>
          {saveStatusLabel && (
            <p className="initiative-modal__save-status muted" role="status" aria-live="polite">
              {saveStatusLabel}
            </p>
          )}
          {saveError && <p className="error">{saveError}</p>}
          <div className="ui-modal__actions">
            <Button type="button" variant="secondary" onClick={handleClose} disabled={isBusy}>
              Cerrar
            </Button>
          </div>
        </>
      }
    >
      <div className="initiative-modal__toolbar">
        <Button
          type="button"
          variant="secondary"
          disabled={isBusy || localEntries.length === 0}
          onClick={() => {
            void onRollAll(localEntries.map((entry) => entry.entity_id)).catch(() => undefined);
          }}
        >
          {isRolling ? "Tirando…" : "Tirar iniciativa de todos"}
        </Button>
      </div>

      {localEntries.length === 0 ? (
        <p className="muted">
          {sceneNotInTrack.length > 0
            ? "Nadie en el track aún. Añade entidades de la escena abajo."
            : "No hay entidades en escena. Añade PNJs o PCs presentes."}
        </p>
      ) : (
        <ol className="initiative-manage-list">
          {localEntries.map((entry, index) => {
            const { label: displayName, entityType } = resolveInitiativeEntryDisplay(
              entry,
              entities,
              sceneState,
              isMaster,
            );

            return (
              <li key={entry.entity_id} className="initiative-manage-item">
                <span className="initiative-manage-item__name">{displayName}</span>
                <div className="initiative-manage-item__meta">
                  <input
                    type="number"
                    className="initiative-manage-item__score"
                    value={entry.initiative_score ?? ""}
                    placeholder="—"
                    disabled={isBusy}
                    aria-label={`Iniciativa de ${displayName}`}
                    onChange={(event) => updateInitiativeScore(index, event.target.value)}
                  />
                  {entityType && <span className="initiative-entry__tag">{entityType}</span>}
                </div>
                <div className="initiative-manage-item__actions">
                  <Button
                    type="button"
                    variant="secondary"
                    className="initiative-manage-item__move"
                    disabled={index === 0 || isBusy}
                    onClick={() => moveEntry(index, -1)}
                    aria-label={`Subir ${displayName}`}
                  >
                    ↑
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    className="initiative-manage-item__move"
                    disabled={index === localEntries.length - 1 || isBusy}
                    onClick={() => moveEntry(index, 1)}
                    aria-label={`Bajar ${displayName}`}
                  >
                    ↓
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    className="initiative-manage-item__remove"
                    disabled={isBusy}
                    onClick={() => removeEntry(index)}
                    aria-label={`Quitar ${displayName} del track`}
                  >
                    Quitar
                  </Button>
                </div>
              </li>
            );
          })}
        </ol>
      )}

      {sceneNotInTrack.length > 0 && (
        <section className="initiative-modal__add-section" aria-label="En escena, fuera del track">
          <h4 className="initiative-modal__add-heading">En escena, fuera del track</h4>
          <ul className="initiative-manage-list initiative-manage-list--add">
            {sceneNotInTrack.map((rosterEntry) => (
              <li key={rosterEntry.id} className="initiative-manage-item initiative-manage-item--add">
                <span className="initiative-manage-item__name">{rosterEntry.label}</span>
                <div className="initiative-manage-item__meta">
                  <span className="initiative-entry__tag">{rosterEntry.entityType}</span>
                </div>
                <Button
                  type="button"
                  variant="secondary"
                  className="initiative-manage-item__add"
                  disabled={isBusy}
                  onClick={() => addEntryFromScene(rosterEntry)}
                  aria-label={`Añadir ${rosterEntry.label} al track`}
                >
                  + Añadir
                </Button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </Modal>
  );
}
