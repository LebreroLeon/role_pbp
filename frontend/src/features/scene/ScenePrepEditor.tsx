import { FormEvent, useEffect, useMemo, useState } from "react";

import type { CampaignEntity, PreparedEntityRef, Scene } from "../../api/types";
import { Button, ErrorBanner, MasterOnlyField, PlayerVisibleField, Switch } from "../../components/ui";
import { NpcVisibilityControl } from "../entities/NpcVisibilityControl";
import { getSceneObjective } from "./sceneState";
import { entityLabel } from "./entityLabel";

function normalizePreparedEntityRefs(
  refs: PreparedEntityRef[],
  entities: CampaignEntity[],
): PreparedEntityRef[] {
  const entitiesById = new Map(entities.map((entity) => [entity.id, entity]));
  return refs.map((ref) => {
    const entity = entitiesById.get(ref.entity_id);
    if (entity?.entity_type === "PC") {
      return { ...ref, player_visibility: "visible" };
    }
    return ref;
  });
}

type ScenePrepEditorProps = {
  scene: Scene;
  entities: CampaignEntity[];
  saving?: boolean;
  error?: string | null;
  onSave: (payload: {
    display_name?: string | null;
    scene_objective?: string | null;
    location_id?: string | null;
    opening_narration?: string | null;
    master_prep_notes?: string | null;
    prepared_entity_refs?: PreparedEntityRef[];
  }) => void;
};

export function ScenePrepEditor({ scene, entities, saving, error, onSave }: ScenePrepEditorProps) {
  const [displayName, setDisplayName] = useState(scene.display_name ?? "");
  const [objective, setObjective] = useState(getSceneObjective(scene.scene_state) ?? "");
  const [locationId, setLocationId] = useState(scene.scene_state.context.location_id ?? "");
  const [opening, setOpening] = useState(scene.scene_state.context.opening_narration ?? "");
  const [notes, setNotes] = useState(scene.scene_state.context.master_prep_notes ?? "");
  const [entityRefs, setEntityRefs] = useState<PreparedEntityRef[]>(
    scene.scene_state.context.prepared_entity_refs ?? [],
  );

  useEffect(() => {
    setDisplayName(scene.display_name ?? "");
    setObjective(getSceneObjective(scene.scene_state) ?? "");
    setLocationId(scene.scene_state.context.location_id ?? "");
    setOpening(scene.scene_state.context.opening_narration ?? "");
    setNotes(scene.scene_state.context.master_prep_notes ?? "");
    setEntityRefs(scene.scene_state.context.prepared_entity_refs ?? []);
  }, [scene.id, scene.display_name, scene.scene_state]);

  const locations = useMemo(
    () => entities.filter((entity) => entity.entity_type === "LOCATION"),
    [entities],
  );

  const rosterEntities = useMemo(
    () => entities.filter((entity) => entity.entity_type === "NPC" || entity.entity_type === "PC"),
    [entities],
  );

  const availableToAdd = rosterEntities.filter(
    (entity) => !entityRefs.some((ref) => ref.entity_id === entity.id),
  );

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSave({
      display_name: displayName.trim() || null,
      scene_objective: objective.trim() || null,
      location_id: locationId || null,
      opening_narration: opening.trim() || null,
      master_prep_notes: notes.trim() || null,
      prepared_entity_refs: normalizePreparedEntityRefs(entityRefs, entities),
    });
  }

  function addEntity(entityId: string) {
    setEntityRefs((current) => [
      ...current,
      { entity_id: entityId, player_visibility: "visible", add_to_roster: true },
    ]);
  }

  function updateRef(entityId: string, patch: Partial<PreparedEntityRef>) {
    setEntityRefs((current) =>
      current.map((ref) => (ref.entity_id === entityId ? { ...ref, ...patch } : ref)),
    );
  }

  function removeRef(entityId: string) {
    setEntityRefs((current) => current.filter((ref) => ref.entity_id !== entityId));
  }

  return (
    <form className="scene-prep-editor" onSubmit={handleSubmit}>
      {error && <ErrorBanner message={error} />}

      <label className="form-field" htmlFor="prep-display-name">
        <span>Nombre de escena</span>
        <input
          id="prep-display-name"
          type="text"
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder='Ej. "La taberna del Grifo"'
          maxLength={200}
          disabled={saving}
        />
      </label>

      <MasterOnlyField
        label="Objetivo de escena"
        htmlFor="prep-objective"
        description="Solo para tu preparación; los jugadores no lo ven."
      >
        <textarea
          id="prep-objective"
          value={objective}
          onChange={(event) => setObjective(event.target.value)}
          rows={2}
          placeholder="Qué quieres que ocurra (solo para ti)"
          disabled={saving}
        />
      </MasterOnlyField>

      <MasterOnlyField label="Ubicación" htmlFor="prep-location" description="Referencia de preparación; no se expone a jugadores.">
        <select
          id="prep-location"
          value={locationId}
          onChange={(event) => setLocationId(event.target.value)}
          disabled={saving}
        >
          <option value="">Sin ubicación</option>
          {locations.map((location) => (
            <option key={location.id} value={location.id}>
              {entityLabel(location)}
            </option>
          ))}
        </select>
      </MasterOnlyField>

      <PlayerVisibleField
        label="Apertura narrativa"
        htmlFor="prep-opening"
        description="Opcional. Puedes enviarla al chat al activar la escena."
      >
        <textarea
          id="prep-opening"
          value={opening}
          onChange={(event) => setOpening(event.target.value)}
          rows={4}
          placeholder="Texto narrativo para abrir la escena en el chat"
          disabled={saving}
        />
      </PlayerVisibleField>

      <MasterOnlyField
        label="Notas del máster"
        htmlFor="prep-notes"
        description="Trampas, secretos y pistas — nunca visibles para jugadores."
      >
        <textarea
          id="prep-notes"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={4}
          placeholder="Trampas, secretos, pistas — solo para ti"
          disabled={saving}
        />
      </MasterOnlyField>

      <MasterOnlyField
        label="Entidades planificadas"
        description="NPCs y PJs listos al activar. Solo los NPCs tienen control de visibilidad: define qué ven los jugadores al activar la escena. Los PJs son siempre visibles."
      >
        {entityRefs.length === 0 && <p className="muted">Sin entidades planificadas.</p>}
        <ul className="scene-prep-editor__entity-list">
          {entityRefs.map((ref) => {
            const entity = rosterEntities.find((item) => item.id === ref.entity_id);
            const label = entity ? entityLabel(entity) : ref.entity_id.slice(0, 8);
            const isPc = entity?.entity_type === "PC";
            return (
              <li key={ref.entity_id} className="scene-prep-editor__entity-row">
                <span className="scene-prep-editor__entity-name" title={label}>
                  {label}
                </span>
                {isPc ? (
                  <span className="scene-prep-editor__visibility muted" title="Los PJs siempre son visibles para jugadores">
                    Siempre visible
                  </span>
                ) : (
                  <NpcVisibilityControl
                    compact
                    value={ref.player_visibility}
                    onChange={(visibility) => updateRef(ref.entity_id, { player_visibility: visibility })}
                    disabled={saving}
                  />
                )}
                <Switch
                  checked={ref.add_to_roster}
                  onCheckedChange={(checked) => updateRef(ref.entity_id, { add_to_roster: checked })}
                  label="Roster"
                  disabled={saving}
                  tone="teal"
                  className="sheet-switch--compact scene-prep-editor__roster-switch"
                />
                <Button
                  type="button"
                  variant="secondary"
                  className="scene-prep-editor__remove-btn"
                  onClick={() => removeRef(ref.entity_id)}
                  disabled={saving}
                  aria-label={`Quitar ${label}`}
                >
                  Quitar
                </Button>
              </li>
            );
          })}
        </ul>
        {availableToAdd.length > 0 && (
          <select
            className="scene-prep-editor__add-entity"
            defaultValue=""
            onChange={(event) => {
              if (event.target.value) {
                addEntity(event.target.value);
                event.target.value = "";
              }
            }}
            disabled={saving}
            aria-label="Añadir entidad"
          >
            <option value="">+ Añadir entidad…</option>
            {availableToAdd.map((entity) => (
              <option key={entity.id} value={entity.id}>
                {entityLabel(entity)} ({entity.entity_type})
              </option>
            ))}
          </select>
        )}
      </MasterOnlyField>

      <Button type="submit" disabled={saving}>
        {saving ? "Guardando…" : "Guardar preparación"}
      </Button>
    </form>
  );
}
