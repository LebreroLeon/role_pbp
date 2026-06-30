import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiError } from "../../api/http";
import type { CampaignMember, SheetRollRequest } from "../../api/types";
import { Button, CollapsibleSection, ErrorBanner, Input, MasterOnlyField, Switch } from "../../components/ui";
import { User } from "../../components/icons";
import { gameSystemLabel, hasSheetTemplate } from "../campaign/gameSystems";
import { useRollEntityMutation, useUpdateEntityMutation } from "../../hooks/mutations/useEntityMutations";
import {
  extractSheetFromEntity,
  type GameSheet,
} from "./pcDocument";
import { buildEntityPutDocument } from "./buildEntityPutDocument";
import { clearedLocationIdFromSave, readSaveWarnings } from "./saveWarnings";
import { CyberpunkSheetForm } from "./systems/cyberpunk_red/CyberpunkSheetForm";
import { parseCyberpunkRedSheet } from "./systems/cyberpunk_red/schema";
import { Dnd5eSheetForm } from "./systems/dnd5e/Dnd5eSheetForm";
import { parseDnd5eSheet } from "./systems/dnd5e/schema";
import { VtmSheetForm } from "./systems/vtm_v5/VtmSheetForm";
import { parseVtmV5Sheet } from "./systems/vtm_v5/schema";
import type { CampaignEntity } from "../entities/entityDefaults";
import { getEntityDisplayName, normalizeEntityRefId } from "../entities/entityDefaults";
import type { SpeakerPayload } from "../scene/speakerOptions";
import { ensureNpcTypedMechanics } from "../entities/npcDocument";
import { extractAvatarUrl } from "../entities/entityAvatar";
import { extractIllustrationUrl } from "../entities/entityIllustration";
import { EntityAvatarField } from "./EntityAvatarField";
import { EntityIllustrationField } from "../entities/EntityIllustrationField";
import { CompendiumTierField } from "../entities/CompendiumTierField";
import { getCompendiumTier, withCompendiumTier, type CompendiumTier } from "../entities/compendiumTier";

type EntitySheetEditorProps = {
  campaignId: string;
  entity: CampaignEntity;
  gameSystem: string;
  members?: CampaignMember[];
  entities?: CampaignEntity[];
  mode?: "create" | "edit";
  onSaved?: () => void;
  onCancel?: () => void;
};

function parseSheetForSystem(systemId: string, raw: unknown): GameSheet {
  switch (systemId) {
    case "dnd5e":
      return parseDnd5eSheet(raw);
    case "cyberpunk_red":
      return parseCyberpunkRedSheet(raw);
    case "vtm_v5":
      return parseVtmV5Sheet(raw);
    default:
      return {};
  }
}

function playerLabel(members: CampaignMember[] | undefined, userId: string | undefined): string {
  if (!userId) return "Sin jugador";
  const member = members?.find((item) => item.user_id === userId);
  return member ? `${member.display_name} (${member.email})` : userId.slice(0, 8);
}

function parsePersonalityTraits(raw: string): string[] {
  return raw
    .split(",")
    .map((trait) => trait.trim())
    .filter(Boolean);
}

export function EntitySheetEditor({
  campaignId,
  entity,
  gameSystem,
  members,
  entities = [],
  mode = "edit",
  onSaved,
  onCancel,
}: EntitySheetEditorProps) {
  const updateMutation = useUpdateEntityMutation(campaignId);
  const rollMutation = useRollEntityMutation(campaignId);
  const [formError, setFormError] = useState<string | null>(null);
  const [formWarning, setFormWarning] = useState<string | null>(null);
  const [rollSummary, setRollSummary] = useState<string | null>(null);
  const [rollMasterOnly, setRollMasterOnly] = useState(false);

  const workingDocument = useMemo(() => {
    if (entity.entity_type === "NPC" && hasSheetTemplate(gameSystem)) {
      return ensureNpcTypedMechanics(entity.document, gameSystem);
    }
    return entity.document;
  }, [entity.document, entity.entity_type, gameSystem]);

  const [name, setName] = useState("");
  const [concept, setConcept] = useState("");
  const [publicDescription, setPublicDescription] = useState("");
  const [secretLore, setSecretLore] = useState("");
  const [voiceAndTone, setVoiceAndTone] = useState("");
  const [personalityTraits, setPersonalityTraits] = useState("");
  const [playerNotes, setPlayerNotes] = useState("");
  const [avatarUrl, setAvatarUrl] = useState(() => extractAvatarUrl(entity) ?? "");
  const [illustrationUrl, setIllustrationUrl] = useState(() => extractIllustrationUrl(entity) ?? "");
  const [factionId, setFactionId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [compendiumTier, setCompendiumTier] = useState<CompendiumTier>("story");

  const factionOptions = useMemo(
    () => entities.filter((item) => item.entity_type === "FACTION"),
    [entities],
  );
  const locationOptions = useMemo(
    () => entities.filter((item) => item.entity_type === "LOCATION"),
    [entities],
  );

  const spellPostSpeaker = useMemo<SpeakerPayload | undefined>(() => {
    if (entity.entity_type !== "PC" && entity.entity_type !== "NPC") return undefined;
    return {
      speaker_type: entity.entity_type,
      speaker_entity_id: entity.id,
      speaker_display_name: name.trim() || getEntityDisplayName(entity, entities),
    };
  }, [entity, name, entities]);

  useEffect(() => {
    const identity = workingDocument.identity as { name?: string; concept?: string } | undefined;
    const publicProfile = workingDocument.public_profile as
      | { description?: string; player_notes?: string }
      | undefined;
    const narrativeProfile = workingDocument.ai_narrative_profile as
      | {
          public_description?: string;
          secret_lore_master?: string;
          voice_and_tone?: string;
          personality_traits?: string[];
        }
      | undefined;

    setName(identity?.name ?? "");
    setConcept(identity?.concept ?? "");
    setPublicDescription(
      entity.entity_type === "PC"
        ? (publicProfile?.description ?? "")
        : (narrativeProfile?.public_description ?? ""),
    );
    setPlayerNotes(publicProfile?.player_notes ?? "");
    setSecretLore(narrativeProfile?.secret_lore_master ?? "");
    setVoiceAndTone(narrativeProfile?.voice_and_tone ?? "");
    setPersonalityTraits((narrativeProfile?.personality_traits ?? []).join(", "));
    setAvatarUrl(extractAvatarUrl(entity) ?? "");
    setIllustrationUrl(extractIllustrationUrl(entity) ?? "");
    const identityRefs = workingDocument.identity as
      | { faction_id?: string | null; current_location_id?: string }
      | undefined;
    setFactionId(normalizeEntityRefId(identityRefs?.faction_id));
    setLocationId(normalizeEntityRefId(identityRefs?.current_location_id));
    setCompendiumTier(getCompendiumTier(entity));
    setFormError(null);
  }, [entity.id, entity.updated_at, entity.entity_type, workingDocument]);

  const supportsSheet = hasSheetTemplate(gameSystem);
  const hasSheetEditor = supportsSheet && gameSystem !== "generic";
  const extracted = extractSheetFromEntity(workingDocument);
  const sheetDefaults = parseSheetForSystem(gameSystem, extracted?.sheet);

  const boundUserId =
    entity.entity_type === "PC"
      ? (workingDocument.player_binding as { user_id?: string } | undefined)?.user_id
      : undefined;

  function buildNarrativeFields() {
    const traits = parsePersonalityTraits(personalityTraits);
    return {
      name,
      concept,
      publicDescription,
      playerNotes: entity.entity_type === "PC" ? playerNotes : undefined,
      secretLore,
      voiceAndTone,
      personalityTraits: traits.length > 0 ? traits : ["misterioso"],
      avatarUrl,
      illustrationUrl,
      factionId: factionId || null,
      locationId: locationId || "",
    };
  }

  async function persistDocument(document: Record<string, unknown>) {
    setFormError(null);
    setFormWarning(null);
    try {
      const updated = await updateMutation.mutateAsync({ entityId: entity.id, document });
      const warning = readSaveWarnings(updated);
      setFormWarning(warning);
      if (warning && clearedLocationIdFromSave(updated)) {
        setLocationId("");
      }
      onSaved?.();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "No se pudo guardar la entidad");
    }
  }

  async function handleNarrativeSubmit(event: FormEvent) {
    event.preventDefault();
    const document = withCompendiumTier(
      buildEntityPutDocument({
        entity,
        workingDocument,
        gameSystem,
        narrative: buildNarrativeFields(),
      }),
      compendiumTier,
    );
    await persistDocument(document);
  }

  async function handleSheetRoll(payload: SheetRollRequest) {
    setFormError(null);
    setRollSummary(null);
    try {
      const result = await rollMutation.mutateAsync({
        entityId: entity.id,
        payload: { ...payload, master_only: rollMasterOnly },
      });
      setRollSummary(result.chat_summary ?? `Resultado: ${result.final_result}`);
      return result;
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "No se pudo tirar desde la ficha");
    }
  }

  async function handleSaveSheet(sheet: GameSheet) {
    const document = withCompendiumTier(
      buildEntityPutDocument({
        entity,
        workingDocument,
        gameSystem,
        narrative: buildNarrativeFields(),
        sheet,
      }),
      compendiumTier,
    );
    await persistDocument(document);
  }

  const saveLabel =
    mode === "create" ? "Guardar ficha nueva" : "Guardar datos narrativos";

  return (
    <div className="entity-sheet-editor">
      {formError && <ErrorBanner message={formError} />}
      {formWarning && <p className="muted">{formWarning}</p>}

      <CollapsibleSection
        icon={User}
        iconTone="violet"
        title="Datos narrativos"
        description="Nombre, concepto, descripción, facción, localización e imágenes."
        defaultOpen={mode === "create"}
        className="sheet-narrative-collapsible"
      >
      <form className="auth-form sheet-narrative-form" onSubmit={handleNarrativeSubmit}>
        <Input label="Nombre" value={name} onChange={(event) => setName(event.target.value)} required />
        <Input label="Concepto" value={concept} onChange={(event) => setConcept(event.target.value)} />

        {(entity.entity_type === "NPC" || entity.entity_type === "PC") && (
          <>
            <label className="form-field">
              <span>Facción (opcional)</span>
              <select value={factionId} onChange={(event) => setFactionId(event.target.value)}>
                <option value="">Sin facción</option>
                {factionOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {getEntityDisplayName(item, entities)}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>Localización actual</span>
              <select value={locationId} onChange={(event) => setLocationId(event.target.value)}>
                <option value="">Sin localización</option>
                {locationOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {getEntityDisplayName(item, entities)}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}

        {entity.entity_type === "PC" && (
          <p className="muted sheet-bound-player">
            Jugador vinculado: <strong>{playerLabel(members, boundUserId)}</strong>
          </p>
        )}

        <label className="form-field">
          <span>{entity.entity_type === "PC" ? "Descripción pública" : "Descripción pública (lo que ven los jugadores)"}</span>
          <textarea
            value={publicDescription}
            onChange={(event) => setPublicDescription(event.target.value)}
            rows={3}
          />
        </label>

        {entity.entity_type === "PC" && (
          <label className="form-field">
            <span>Apuntes del jugador</span>
            <textarea
              value={playerNotes}
              onChange={(event) => setPlayerNotes(event.target.value)}
              rows={4}
              placeholder="Notas personales del jugador sobre su personaje o la campaña"
            />
          </label>
        )}

        {(entity.entity_type === "PC" || entity.entity_type === "NPC") && (
          <EntityAvatarField
            campaignId={campaignId}
            entityId={entity.id}
            entityName={name}
            avatarUrl={avatarUrl}
            onAvatarUrlChange={setAvatarUrl}
            disabled={updateMutation.isPending}
          />
        )}

        {(entity.entity_type === "PC" || entity.entity_type === "NPC") && (
          <EntityIllustrationField
            campaignId={campaignId}
            entity={entity}
            entityName={name}
            illustrationUrl={illustrationUrl}
            onIllustrationUrlChange={setIllustrationUrl}
            disabled={updateMutation.isPending}
          />
        )}

        {entity.entity_type === "NPC" && (
          <>
            <CompendiumTierField
              id={`compendium-tier-${entity.id}`}
              value={compendiumTier}
              onChange={setCompendiumTier}
              disabled={updateMutation.isPending}
            />
            <Input
              label="Rasgos de personalidad (separados por coma)"
              value={personalityTraits}
              onChange={(event) => setPersonalityTraits(event.target.value)}
            />
            <Input
              label="Voz y tono"
              value={voiceAndTone}
              onChange={(event) => setVoiceAndTone(event.target.value)}
            />
            <MasterOnlyField label="Lore secreto" htmlFor={`secret-lore-${entity.id}`}>
              <textarea
                id={`secret-lore-${entity.id}`}
                value={secretLore}
                onChange={(event) => setSecretLore(event.target.value)}
                rows={4}
              />
            </MasterOnlyField>
          </>
        )}

        <div className="actions">
          <Button type="submit" disabled={updateMutation.isPending || !name.trim()}>
            {updateMutation.isPending ? "Guardando..." : saveLabel}
          </Button>
          {onCancel && (
            <Button type="button" variant="secondary" onClick={onCancel}>
              Cerrar
            </Button>
          )}
        </div>
      </form>
      </CollapsibleSection>

      {hasSheetEditor ? (
        <>
          {entity.entity_type === "NPC" && (
            <MasterOnlyField
              label="Tirada en secreto"
              description="Las tiradas de este NPC solo las verá el Máster (salvo que esté oculto, que siempre son secretas para jugadores)"
            >
              <Switch
                checked={rollMasterOnly}
                onCheckedChange={setRollMasterOnly}
                label="Activar tirada en secreto"
                tone="rose"
                disabled={rollMutation.isPending}
              />
            </MasterOnlyField>
          )}
          {rollSummary && <p className="sheet-roll-summary">{rollSummary}</p>}
          {gameSystem === "dnd5e" && (
            <Dnd5eSheetForm
              key={`${entity.id}-${entity.updated_at}`}
              campaignId={campaignId}
              defaultValues={sheetDefaults as ReturnType<typeof parseDnd5eSheet>}
              onSubmit={handleSaveSheet}
              onRoll={handleSheetRoll}
              isSaving={updateMutation.isPending}
              isRolling={rollMutation.isPending}
              canGrantInspiration
              spellPostSpeaker={spellPostSpeaker}
            />
          )}
          {gameSystem === "cyberpunk_red" && (
            <CyberpunkSheetForm
              key={`${entity.id}-${entity.updated_at}`}
              defaultValues={sheetDefaults as ReturnType<typeof parseCyberpunkRedSheet>}
              onSubmit={handleSaveSheet}
              onRoll={handleSheetRoll}
              isSaving={updateMutation.isPending}
              isRolling={rollMutation.isPending}
            />
          )}
          {gameSystem === "vtm_v5" && (
            <VtmSheetForm
              key={`${entity.id}-${entity.updated_at}`}
              defaultValues={sheetDefaults as ReturnType<typeof parseVtmV5Sheet>}
              onSubmit={handleSaveSheet}
              onRoll={handleSheetRoll}
              isSaving={updateMutation.isPending}
              isRolling={rollMutation.isPending}
            />
          )}
        </>
      ) : (
        <p className="muted">
          Esta campaña usa un sistema sin plantilla mecánica ({gameSystemLabel(gameSystem)}).
        </p>
      )}
    </div>
  );
}
