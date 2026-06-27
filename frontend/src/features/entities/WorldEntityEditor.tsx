import { FormEvent, useMemo, useState } from "react";

import { ApiError } from "../../api/http";
import { Button, ErrorBanner, Input, MasterOnlyField } from "../../components/ui";
import { useUpdateEntityMutation } from "../../hooks/mutations/useEntityMutations";
import {
  ENTITY_TYPE_LABELS,
  type CampaignEntity,
  getEntityDisplayName,
} from "./entityDefaults";
import { extractIllustrationUrl } from "./entityIllustration";
import { EntityIllustrationField } from "./EntityIllustrationField";
import { CompendiumTierField } from "./CompendiumTierField";
import { getCompendiumTier, withCompendiumTier, type CompendiumTier } from "./compendiumTier";

type WorldEntityEditorProps = {
  campaignId: string;
  entity: CampaignEntity;
  entities: CampaignEntity[];
  onSaved: () => void;
  onCancel: () => void;
};

const RELATIONSHIP_CANDIDATE_TYPES = new Set(["NPC", "PC", "FACTION", "LOCATION"]);

export function WorldEntityEditor({
  campaignId,
  entity,
  entities,
  onSaved,
  onCancel,
}: WorldEntityEditorProps) {
  const mutation = useUpdateEntityMutation(campaignId);
  const apiError = mutation.error instanceof ApiError ? mutation.error.message : null;

  const relationshipCandidates = useMemo(
    () => entities.filter((item) => RELATIONSHIP_CANDIDATE_TYPES.has(item.entity_type)),
    [entities],
  );

  const [form, setForm] = useState(() => buildFormState(entity));
  const [illustrationUrl, setIllustrationUrl] = useState(() => extractIllustrationUrl(entity) ?? "");

  function updateField<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate(
      { entityId: entity.id, document: buildDocumentFromForm(entity, form, illustrationUrl) },
      { onSuccess: () => onSaved() },
    );
  }

  const title = ENTITY_TYPE_LABELS[entity.entity_type];

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      {entity.entity_type === "LOCATION" && (
        <>
          <Input label="Nombre" value={form.name} onChange={(e) => updateField("name", e.target.value)} required />
          <Input
            label="Tipo de localización"
            value={form.locationType}
            onChange={(e) => updateField("locationType", e.target.value)}
          />
          <label className="form-field">
            <span>Localización padre (opcional)</span>
            <select
              value={form.parentLocationId}
              onChange={(e) => updateField("parentLocationId", e.target.value)}
            >
              <option value="">Sin padre</option>
              {entities
                .filter((item) => item.entity_type === "LOCATION" && item.id !== entity.id)
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {getEntityDisplayName(item)}
                  </option>
                ))}
            </select>
          </label>
          <Input
            label="Tono ambiental"
            value={form.ambientTone}
            onChange={(e) => updateField("ambientTone", e.target.value)}
          />
          <Input
            label="Rasgos notables (separados por coma)"
            value={form.notableFeatures}
            onChange={(e) => updateField("notableFeatures", e.target.value)}
          />
          <label className="form-field">
            <span>Descripción pública</span>
            <textarea
              value={form.publicDescription}
              onChange={(e) => updateField("publicDescription", e.target.value)}
              rows={3}
              required
            />
          </label>
          <MasterOnlyField label="Lore secreto" htmlFor={`location-secret-${entity.id}`}>
            <textarea
              id={`location-secret-${entity.id}`}
              value={form.secretLore}
              onChange={(e) => updateField("secretLore", e.target.value)}
              rows={3}
            />
          </MasterOnlyField>
          <label className="form-field">
            <span>
              <input
                type="checkbox"
                checked={form.isAccessible}
                onChange={(e) => updateField("isAccessible", e.target.checked)}
              />{" "}
              Accesible para el grupo
            </span>
          </label>
          <Input
            label="Nivel de peligro (0-10)"
            type="number"
            min={0}
            max={10}
            value={form.dangerLevel}
            onChange={(e) => updateField("dangerLevel", Number(e.target.value))}
          />
        </>
      )}

      {entity.entity_type === "FACTION" && (
        <>
          <Input label="Nombre" value={form.name} onChange={(e) => updateField("name", e.target.value)} required />
          <Input
            label="Tipo de facción"
            value={form.factionType}
            onChange={(e) => updateField("factionType", e.target.value)}
          />
          <label className="form-field">
            <span>Cuartel general (opcional)</span>
            <select
              value={form.headquartersLocationId}
              onChange={(e) => updateField("headquartersLocationId", e.target.value)}
            >
              <option value="">Sin sede definida</option>
              {entities
                .filter((item) => item.entity_type === "LOCATION")
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {getEntityDisplayName(item)}
                  </option>
                ))}
            </select>
          </label>
          <Input
            label="Objetivos (separados por coma)"
            value={form.goals}
            onChange={(e) => updateField("goals", e.target.value)}
          />
          <label className="form-field">
            <span>Descripción pública</span>
            <textarea
              value={form.publicDescription}
              onChange={(e) => updateField("publicDescription", e.target.value)}
              rows={3}
              required
            />
          </label>
          <MasterOnlyField label="Lore secreto" htmlFor={`location-secret-${entity.id}`}>
            <textarea
              id={`location-secret-${entity.id}`}
              value={form.secretLore}
              onChange={(e) => updateField("secretLore", e.target.value)}
              rows={3}
            />
          </MasterOnlyField>
          <Input
            label="Actitud hacia el grupo"
            value={form.attitude}
            onChange={(e) => updateField("attitude", e.target.value)}
          />
          <Input
            label="Nivel de influencia (0-10)"
            type="number"
            min={0}
            max={10}
            value={form.influenceLevel}
            onChange={(e) => updateField("influenceLevel", Number(e.target.value))}
          />
        </>
      )}

      {entity.entity_type === "RELATIONSHIP" && (
        <>
          <label className="form-field">
            <span>Entidad origen</span>
            <select
              value={form.sourceId}
              onChange={(e) => updateField("sourceId", e.target.value)}
              required
            >
              <option value="">Selecciona origen</option>
              {relationshipCandidates.map((item) => (
                <option key={item.id} value={item.id}>
                  {getEntityDisplayName(item, entities)} ({item.entity_type})
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>Entidad destino</span>
            <select
              value={form.targetId}
              onChange={(e) => updateField("targetId", e.target.value)}
              required
            >
              <option value="">Selecciona destino</option>
              {relationshipCandidates.map((item) => (
                <option key={item.id} value={item.id}>
                  {getEntityDisplayName(item, entities)} ({item.entity_type})
                </option>
              ))}
            </select>
          </label>
          <Input
            label="Tipo de vínculo"
            value={form.bondType}
            onChange={(e) => updateField("bondType", e.target.value)}
          />
          <Input
            label="Estado público del vínculo"
            value={form.publicStatus}
            onChange={(e) => updateField("publicStatus", e.target.value)}
          />
          <Input
            label="Nivel de tensión (0-10)"
            type="number"
            min={0}
            max={10}
            value={form.tensionLevel}
            onChange={(e) => updateField("tensionLevel", Number(e.target.value))}
          />
          <MasterOnlyField label="Matices secretos del vínculo" htmlFor={`bond-secret-${entity.id}`}>
            <textarea
              id={`bond-secret-${entity.id}`}
              value={form.secretNuance}
              onChange={(e) => updateField("secretNuance", e.target.value)}
              rows={3}
            />
          </MasterOnlyField>
          <label className="form-field">
            <span>
              <input
                type="checkbox"
                checked={form.isBidirectional}
                onChange={(e) => updateField("isBidirectional", e.target.checked)}
              />{" "}
              Vínculo bidireccional
            </span>
          </label>
        </>
      )}

      {(entity.entity_type === "LOCATION" ||
        entity.entity_type === "FACTION" ||
        entity.entity_type === "RELATIONSHIP") && (
        <>
          <CompendiumTierField
            id={`compendium-tier-${entity.id}`}
            value={form.compendiumTier}
            onChange={(tier) => updateField("compendiumTier", tier)}
            disabled={mutation.isPending}
          />
          <EntityIllustrationField
          campaignId={campaignId}
          entity={entity}
          entityName={form.name || getEntityDisplayName(entity, entities)}
          illustrationUrl={illustrationUrl}
          onIllustrationUrlChange={setIllustrationUrl}
          disabled={mutation.isPending}
        />
        </>
      )}

      {apiError && <ErrorBanner message={apiError} />}
      <div className="form-actions">
        <Button type="button" className="secondary" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={mutation.isPending || !canSubmit(entity.entity_type, form)}>
          {mutation.isPending ? "Guardando..." : `Guardar ${title.toLowerCase()}`}
        </Button>
      </div>
    </form>
  );
}

type FormState = {
  name: string;
  locationType: string;
  parentLocationId: string;
  ambientTone: string;
  notableFeatures: string;
  factionType: string;
  headquartersLocationId: string;
  goals: string;
  publicDescription: string;
  secretLore: string;
  isAccessible: boolean;
  dangerLevel: number;
  attitude: string;
  influenceLevel: number;
  sourceId: string;
  targetId: string;
  bondType: string;
  publicStatus: string;
  secretNuance: string;
  tensionLevel: number;
  isBidirectional: boolean;
  compendiumTier: CompendiumTier;
};

function buildFormState(entity: CampaignEntity): FormState {
  const identity = entity.document.identity as Record<string, unknown> | undefined;
  const narrativeProfile = entity.document.narrative_profile as Record<string, unknown> | undefined;
  const connection = entity.document.connection as Record<string, unknown> | undefined;
  const bond = entity.document.narrative_bond as Record<string, unknown> | undefined;
  const stateFlags = entity.document.state_flags as Record<string, unknown> | undefined;

  return {
    name: String(identity?.name ?? ""),
    locationType: String(identity?.location_type ?? "lugar"),
    parentLocationId: String(identity?.parent_location_id ?? ""),
    ambientTone: String(narrativeProfile?.ambient_tone ?? ""),
    notableFeatures: Array.isArray(narrativeProfile?.notable_features)
      ? (narrativeProfile.notable_features as string[]).join(", ")
      : "",
    factionType: String(identity?.faction_type ?? "organización"),
    headquartersLocationId: String(identity?.headquarters_location_id ?? ""),
    goals: Array.isArray(narrativeProfile?.goals) ? (narrativeProfile.goals as string[]).join(", ") : "",
    publicDescription: String(narrativeProfile?.public_description ?? ""),
    secretLore: String(narrativeProfile?.secret_lore_master ?? ""),
    isAccessible: Boolean(stateFlags?.is_accessible_to_party ?? true),
    dangerLevel: Number(stateFlags?.danger_level ?? 3),
    attitude: String(stateFlags?.attitude_towards_party ?? "neutral"),
    influenceLevel: Number(stateFlags?.influence_level ?? 5),
    sourceId: String(connection?.source_id ?? ""),
    targetId: String(connection?.target_id ?? ""),
    bondType: String(bond?.bond_type ?? "alianza"),
    publicStatus: String(bond?.public_status ?? ""),
    secretNuance: String(bond?.secret_nuance ?? ""),
    tensionLevel: Number(bond?.tension_level ?? 3),
    isBidirectional: Boolean(connection?.is_bidirectional ?? true),
    compendiumTier: getCompendiumTier(entity),
  };
}

function canSubmit(entityType: CampaignEntity["entity_type"], form: FormState): boolean {
  if (entityType === "RELATIONSHIP") {
    return Boolean(form.sourceId && form.targetId);
  }
  return Boolean(form.name.trim() && form.publicDescription.trim());
}

function buildDocumentFromForm(
  entity: CampaignEntity,
  form: FormState,
  illustrationUrl: string,
): Record<string, unknown> {
  const document = structuredClone(entity.document);

  function applyIllustrationUrl(profile: Record<string, unknown>) {
    const trimmed = illustrationUrl.trim();
    if (trimmed) {
      profile.illustration_url = trimmed;
    } else {
      delete profile.illustration_url;
    }
  }

  if (entity.entity_type === "LOCATION") {
    const identity = document.identity as Record<string, unknown>;
    const profile = document.narrative_profile as Record<string, unknown>;
    const flags = document.state_flags as Record<string, unknown>;
    identity.name = form.name.trim();
    identity.location_type = form.locationType.trim() || "lugar";
    identity.parent_location_id = form.parentLocationId || null;
    profile.public_description = form.publicDescription.trim();
    profile.secret_lore_master = form.secretLore.trim();
    profile.ambient_tone = form.ambientTone.trim() || null;
    profile.notable_features = form.notableFeatures
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    applyIllustrationUrl(profile);
    flags.is_accessible_to_party = form.isAccessible;
    flags.danger_level = Math.min(10, Math.max(0, form.dangerLevel));
  }

  if (entity.entity_type === "FACTION") {
    const identity = document.identity as Record<string, unknown>;
    const profile = document.narrative_profile as Record<string, unknown>;
    const flags = document.state_flags as Record<string, unknown>;
    identity.name = form.name.trim();
    identity.faction_type = form.factionType.trim() || "organización";
    identity.headquarters_location_id = form.headquartersLocationId || null;
    profile.public_description = form.publicDescription.trim();
    profile.secret_lore_master = form.secretLore.trim();
    profile.goals = form.goals
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    applyIllustrationUrl(profile);
    flags.attitude_towards_party = form.attitude.trim() || "neutral";
    flags.influence_level = Math.min(10, Math.max(0, form.influenceLevel));
  }

  if (entity.entity_type === "RELATIONSHIP") {
    const connection = document.connection as Record<string, unknown>;
    const bond = document.narrative_bond as Record<string, unknown>;
    const metadata = document.metadata as Record<string, unknown>;
    connection.source_id = form.sourceId;
    connection.target_id = form.targetId;
    connection.is_bidirectional = form.isBidirectional;
    bond.bond_type = form.bondType.trim() || "alianza";
    bond.public_status = form.publicStatus.trim();
    bond.secret_nuance = form.secretNuance.trim();
    bond.tension_level = Math.min(10, Math.max(0, form.tensionLevel));
    applyIllustrationUrl(bond);
    metadata.last_updated = new Date().toISOString();
  }

  return withCompendiumTier(document, form.compendiumTier);
}
