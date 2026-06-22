import { useEffect, useMemo, useState, type ReactNode } from "react";

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
  isConflictModeActive,
  isPbpEnabled,
  normalizeSceneState,
  resolveCurrentTurnLabel,
  type SceneStateInput,
} from "../scene/sceneState";
import { buildSceneRoster, enrichInitiativeEntry, resolveInitiativeEntryDisplay } from "./sceneRoster";

type InitiativeOrderPanelProps = {
  sceneId: string;
  campaignId: string;
  sceneState: SceneStateInput;
  entities: CampaignEntity[];
  members: MemberLookup;
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

  async function handleTogglePbp(enabled: boolean) {
    await updateTurnManagement.mutateAsync({ sceneId, pbp_enabled: enabled });
  }

  async function handleAdvanceTurn() {
    await advancePbpTurn.mutateAsync({ sceneId });
  }

  async function handleAssignTurn(entityId: string) {
    await updateTurnManagement.mutateAsync({ sceneId, current_turn_entity_id: entityId });
  }

  const masterTurnControls = isMaster && pbpOn && displayEntries.length > 0 ? (
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
      onSave={(entries) =>
        updateTurnManagement
          .mutateAsync({
            sceneId,
            order_source: "manual",
            initiative_order: entries,
            current_turn_entity_id: entries[0]?.entity_id ?? null,
            resort: false,
          })
          .then(() => setManageOpen(false))
      }
      isSaving={updateTurnManagement.isPending || rollInitiative.isPending}
      saveError={
        (updateTurnManagement.error ?? rollInitiative.error) instanceof Error
          ? (updateTurnManagement.error ?? rollInitiative.error)?.message ?? null
          : null
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
          masterTurnControls={masterTurnControls}
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
        {masterTurnControls}
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
        const statusMarker = stateFlags?.is_dead
          ? "☠"
          : stateFlags?.is_incapacitated
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

type InitiativeManageModalProps = {
  entries: CombatInitiativeEntry[];
  entities: CampaignEntity[];
  sceneState: SceneStateInput;
  isMaster: boolean;
  onClose: () => void;
  onRollAll: (entityIds: string[]) => Promise<void>;
  onSave: (entries: CombatInitiativeEntry[]) => Promise<void>;
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
  const isBusy = isSaving || isRolling;

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
    <Modal
      title="Gestionar iniciativa"
      titleId="initiative-modal-title"
      onClose={onClose}
      size="md"
      footer={
        <>
          <p className="muted initiative-modal__note">
            Tirar iniciativa ordena por valor (mayor primero). El Máster puede ajustar el orden con
            las flechas y guardar.
          </p>
          {saveError && <p className="error">{saveError}</p>}
          <div className="ui-modal__actions">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isBusy}>
              Cerrar
            </Button>
            <Button
              type="button"
              disabled={isBusy || localEntries.length === 0}
              onClick={() => {
                void onSave(localEntries).catch(() => undefined);
              }}
            >
              {isSaving ? "Guardando…" : "Guardar orden"}
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
        <p className="muted">No hay entidades en escena. Añade PNJs o PCs presentes.</p>
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
                {entry.initiative_score != null && (
                  <span className="initiative-entry__score">{entry.initiative_score}</span>
                )}
                {entityType && <span className="initiative-entry__tag">{entityType}</span>}
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
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </Modal>
  );
}
