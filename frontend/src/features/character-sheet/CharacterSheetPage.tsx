import { FormEvent, useEffect, useMemo, useState } from "react";

import { useParams } from "react-router-dom";



import { ApiError } from "../../api/http";

import type { SheetRollRequest } from "../../api/types";

import { Scroll, User } from "../../components/icons";

import { Button, CollapsibleSection, ErrorBanner, Input, Panel, PanelHeader } from "../../components/ui";

import { gameSystemLabel, getGameSystemProfile, hasSheetTemplate } from "../campaign/gameSystems";

import { useUpsertMySheetMutation, useRollFromSheetMutation } from "../../hooks/mutations/useMySheetMutations";

import { useCampaignQuery } from "../../hooks/queries/useCampaignQueries";

import { useMySheetQuery } from "../../hooks/queries/useMySheetQueries";

import { useEntitiesQuery } from "../../hooks/queries/useEntityQueries";
import { EntityRefFields } from "../entities/EntityRefFields";
import type { CampaignEntity } from "../entities/entityDefaults";
import { getEntityDisplayName, normalizeEntityRefId } from "../entities/entityDefaults";
import { extractAvatarUrl } from "../entities/entityAvatar";
import { extractIllustrationUrl } from "../entities/entityIllustration";

import { useAuthStore } from "../../stores/authStore";

import {

  buildCharacterSheetUpsert,

  defaultSheetForGameSystem,

  documentToCharacterSheetUpsert,

  extractSheetFromEntity,

  mergeSheetIntoDocument,

  type GameSheet,

} from "./pcDocument";
import { clearedLocationIdFromSave, readSaveWarnings } from "./saveWarnings";

import { EntityAvatarField } from "./EntityAvatarField";
import { EntityIllustrationField } from "../entities/EntityIllustrationField";

import { CyberpunkSheetForm } from "./systems/cyberpunk_red/CyberpunkSheetForm";

import { parseCyberpunkRedSheet } from "./systems/cyberpunk_red/schema";

import { Dnd5eSheetForm } from "./systems/dnd5e/Dnd5eSheetForm";

import { parseDnd5eSheet } from "./systems/dnd5e/schema";

import { VtmSheetForm } from "./systems/vtm_v5/VtmSheetForm";

import { parseVtmV5Sheet } from "./systems/vtm_v5/schema";



function parseSheetForSystem(systemId: string, raw: unknown): GameSheet {

  switch (systemId) {

    case "dnd5e":

      return parseDnd5eSheet(raw);

    case "cyberpunk_red":

      return parseCyberpunkRedSheet(raw);

    case "vtm_v5":

      return parseVtmV5Sheet(raw);

    default:

      return defaultSheetForGameSystem(systemId);

  }

}



export function CharacterSheetPage() {

  const { campaignId = "" } = useParams();

  const currentUser = useAuthStore((state) => state.user);

  const { data: campaign } = useCampaignQuery(campaignId);

  const { data: myPc, isLoading, isError, error } = useMySheetQuery(campaignId);

  const { data: entities = [] } = useEntitiesQuery(campaignId);

  const upsertMutation = useUpsertMySheetMutation(campaignId);

  const rollMutation = useRollFromSheetMutation(campaignId);



  const [createName, setCreateName] = useState("");

  const [createConcept, setCreateConcept] = useState("");

  const [createDescription, setCreateDescription] = useState("");

  const [createFactionId, setCreateFactionId] = useState("");

  const [createLocationId, setCreateLocationId] = useState("");

  const [formError, setFormError] = useState<string | null>(null);
  const [formWarning, setFormWarning] = useState<string | null>(null);

  const [rollSummary, setRollSummary] = useState<string | null>(null);

  // Narrative edit state (shown when PC exists)
  const [name, setName] = useState("");
  const [concept, setConcept] = useState("");
  const [publicDescription, setPublicDescription] = useState("");
  const [factionId, setFactionId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [illustrationUrl, setIllustrationUrl] = useState("");
  const [playerNotes, setPlayerNotes] = useState("");

  const factionOptions = useMemo(
    () => entities.filter((item) => item.entity_type === "FACTION"),
    [entities],
  );
  const locationOptions = useMemo(
    () => entities.filter((item) => item.entity_type === "LOCATION"),
    [entities],
  );

  useEffect(() => {
    if (!myPc) return;
    const identity = myPc.document.identity as { name?: string; concept?: string; faction_id?: string | null; current_location_id?: string } | undefined;
    const publicProfile = myPc.document.public_profile as { description?: string; player_notes?: string } | undefined;
    setName(identity?.name ?? "");
    setConcept(identity?.concept ?? "");
    setPublicDescription(publicProfile?.description ?? "");
    setPlayerNotes(publicProfile?.player_notes ?? "");
    setFactionId(normalizeEntityRefId(identity?.faction_id));
    setLocationId(normalizeEntityRefId(identity?.current_location_id));
    setAvatarUrl(extractAvatarUrl(myPc) ?? "");
    setIllustrationUrl(extractIllustrationUrl(myPc) ?? "");
  }, [myPc?.id, myPc?.updated_at]);



  const gameSystem = campaign?.game_system ?? "generic";

  const profile = getGameSystemProfile(gameSystem);

  const supportsSheet = hasSheetTemplate(gameSystem);

  const hasSheetEditor = supportsSheet && gameSystem !== "generic";



  function applySaveResult(saved: CampaignEntity) {
    const warning = readSaveWarnings(saved);
    setFormWarning(warning);
    if (warning && clearedLocationIdFromSave(saved)) {
      setLocationId("");
    }
  }

  async function handleCreatePc(event: FormEvent) {

    event.preventDefault();

    if (!createName.trim() || !currentUser) return;

    setFormError(null);
    setFormWarning(null);



    const payload = buildCharacterSheetUpsert({

      name: createName,

      concept: createConcept,

      description: createDescription,

      systemId: gameSystem,

      factionId: createFactionId,

      locationId: createLocationId,

    });



    try {

      await upsertMutation.mutateAsync(payload);

    } catch (err) {

      setFormError(err instanceof ApiError ? err.message : "No se pudo crear el personaje");

    }

  }



  async function handleNarrativeSubmit(event: FormEvent) {
    event.preventDefault();
    if (!myPc) return;
    setFormError(null);
    setFormWarning(null);

    const baseDocument = myPc.document;
    const updatedDocument = {
      ...baseDocument,
      identity: {
        ...(baseDocument.identity as Record<string, unknown>),
        name: name.trim(),
        concept: concept.trim(),
        faction_id: factionId || null,
        current_location_id: locationId || null,
      },
      public_profile: {
        ...(baseDocument.public_profile as Record<string, unknown>),
        description: publicDescription.trim(),
        player_notes: playerNotes.trim(),
        avatar_url: avatarUrl.trim() || undefined,
        illustration_url: illustrationUrl.trim() || undefined,
      },
    };

    const payload = documentToCharacterSheetUpsert(updatedDocument);

    try {
      const saved = await upsertMutation.mutateAsync(payload);
      applySaveResult(saved);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "No se pudo guardar los datos narrativos");
    }
  }

  async function handleSaveSheet(sheet: GameSheet) {

    if (!myPc) return;

    setFormError(null);
    setFormWarning(null);



    const document = mergeSheetIntoDocument(myPc.document, gameSystem, sheet as Record<string, unknown>);

    const payload = documentToCharacterSheetUpsert(document);



    try {

      const saved = await upsertMutation.mutateAsync(payload);
      applySaveResult(saved);

    } catch (err) {

      setFormError(err instanceof ApiError ? err.message : "No se pudo guardar la ficha");

    }

  }



  async function handleRoll(payload: SheetRollRequest) {
    setFormError(null);
    setRollSummary(null);

    try {
      const result = await rollMutation.mutateAsync(payload);
      setRollSummary(result.chat_summary || `Resultado: ${result.final_result ?? "—"}`);
      return result;
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "No se pudo tirar los dados");
    }
  }



  const extracted = myPc ? extractSheetFromEntity(myPc.document) : null;

  const sheetDefaults = parseSheetForSystem(gameSystem, extracted?.sheet);

  return (

    <div className="character-sheet-page">

      <Panel>

        <PanelHeader

          icon={Scroll}

          iconTone="violet"

          title="Mi ficha"

          description={

            profile

              ? `${profile.label} — ${profile.previewSummary}`

              : `${gameSystemLabel(gameSystem)} — ficha mecánica`

          }

        />



        {formError && <ErrorBanner message={formError} />}
        {formWarning && <p className="muted">{formWarning}</p>}

        {rollSummary && <p className="sheet-roll-summary">{rollSummary}</p>}



        {isLoading && <p className="muted">Cargando ficha...</p>}



        {isError && !myPc && !(error instanceof ApiError && error.status === 404) && (

          <ErrorBanner message={error instanceof Error ? error.message : "Error al cargar la ficha"} />

        )}



        {!isLoading && !myPc && (

          <SectionCreatePc

            gameSystem={gameSystem}

            supportsSheet={supportsSheet}

            entities={entities}

            createName={createName}

            createConcept={createConcept}

            createDescription={createDescription}

            createFactionId={createFactionId}

            createLocationId={createLocationId}

            onNameChange={setCreateName}

            onConceptChange={setCreateConcept}

            onDescriptionChange={setCreateDescription}

            onFactionChange={setCreateFactionId}

            onLocationChange={setCreateLocationId}

            onSubmit={handleCreatePc}

            isPending={upsertMutation.isPending}

          />

        )}



        {myPc && (
          <CollapsibleSection
            icon={User}
            iconTone="violet"
            title="Datos narrativos"
            description="Nombre, concepto, descripción, facción, localización e imágenes."
            defaultOpen={false}
            className="sheet-narrative-collapsible"
          >
            <form className="auth-form sheet-narrative-form" onSubmit={handleNarrativeSubmit}>
              <Input label="Nombre" value={name} onChange={(e) => setName(e.target.value)} required />
              <Input label="Concepto" value={concept} onChange={(e) => setConcept(e.target.value)} />

              <label className="form-field">
                <span>Facción (opcional)</span>
                <select value={factionId} onChange={(e) => setFactionId(e.target.value)}>
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
                <select value={locationId} onChange={(e) => setLocationId(e.target.value)}>
                  <option value="">Sin localización</option>
                  {locationOptions.map((item) => (
                    <option key={item.id} value={item.id}>
                      {getEntityDisplayName(item, entities)}
                    </option>
                  ))}
                </select>
              </label>

              <label className="form-field">
                <span>Descripción pública</span>
                <textarea
                  value={publicDescription}
                  onChange={(e) => setPublicDescription(e.target.value)}
                  rows={3}
                />
              </label>

              <label className="form-field">
                <span>Apuntes del jugador</span>
                <textarea
                  value={playerNotes}
                  onChange={(e) => setPlayerNotes(e.target.value)}
                  rows={4}
                  placeholder="Notas personales sobre tu personaje o la campaña"
                />
              </label>

              <EntityAvatarField
                campaignId={campaignId}
                entityId={myPc.id}
                entityName={name}
                avatarUrl={avatarUrl}
                onAvatarUrlChange={setAvatarUrl}
                disabled={upsertMutation.isPending}
              />

              <EntityIllustrationField
                campaignId={campaignId}
                entity={myPc}
                entityName={name}
                illustrationUrl={illustrationUrl}
                onIllustrationUrlChange={setIllustrationUrl}
                disabled={upsertMutation.isPending}
              />

              <div className="actions">
                <Button type="submit" disabled={upsertMutation.isPending || !name.trim()}>
                  {upsertMutation.isPending ? "Guardando..." : "Guardar datos narrativos"}
                </Button>
              </div>
            </form>
          </CollapsibleSection>
        )}

        {myPc && hasSheetEditor && (

          <>

            {gameSystem === "dnd5e" && (

              <Dnd5eSheetForm

                key={myPc.updated_at}

                defaultValues={sheetDefaults as ReturnType<typeof parseDnd5eSheet>}

                onSubmit={handleSaveSheet}

                onRoll={handleRoll}

                isSaving={upsertMutation.isPending}

                isRolling={rollMutation.isPending}

              />

            )}

            {gameSystem === "cyberpunk_red" && (

              <CyberpunkSheetForm

                key={myPc.updated_at}

                defaultValues={sheetDefaults as ReturnType<typeof parseCyberpunkRedSheet>}

                onSubmit={handleSaveSheet}

                onRoll={handleRoll}

                isSaving={upsertMutation.isPending}

                isRolling={rollMutation.isPending}

              />

            )}

            {gameSystem === "vtm_v5" && (

              <VtmSheetForm

                key={myPc.updated_at}

                defaultValues={sheetDefaults as ReturnType<typeof parseVtmV5Sheet>}

                onSubmit={handleSaveSheet}

                onRoll={handleRoll}

                isSaving={upsertMutation.isPending}

                isRolling={rollMutation.isPending}

              />

            )}

          </>

        )}



        {myPc && !hasSheetEditor && (

          <p className="muted">

            Esta campaña usa un sistema sin plantilla mecánica. Edita los datos narrativos desde Mundo.

          </p>

        )}

      </Panel>

    </div>

  );

}



type SectionCreatePcProps = {

  gameSystem: string;

  supportsSheet: boolean;

  entities: CampaignEntity[];

  createName: string;

  createConcept: string;

  createDescription: string;

  createFactionId: string;

  createLocationId: string;

  onNameChange: (value: string) => void;

  onConceptChange: (value: string) => void;

  onDescriptionChange: (value: string) => void;

  onFactionChange: (value: string) => void;

  onLocationChange: (value: string) => void;

  onSubmit: (event: FormEvent) => void;

  isPending: boolean;

};



function SectionCreatePc({

  gameSystem,

  supportsSheet,

  entities,

  createName,

  createConcept,

  createDescription,

  createFactionId,

  createLocationId,

  onNameChange,

  onConceptChange,

  onDescriptionChange,

  onFactionChange,

  onLocationChange,

  onSubmit,

  isPending,

}: SectionCreatePcProps) {

  const profile = getGameSystemProfile(gameSystem);



  return (

    <section className="sheet-create">

      <p className="muted">

        Aún no tienes un personaje jugador en esta campaña.

        {profile && (

          <>

            {" "}

            Se creará con la plantilla <strong>{profile.sheetTemplateId}</strong> ({profile.previewSummary}).

          </>

        )}

      </p>

      {!supportsSheet && (

        <p className="muted">

          Este sistema no tiene plantilla mecánica; se creará una ficha narrativa básica.

        </p>

      )}

      <form className="auth-form" onSubmit={onSubmit}>

        <Input label="Nombre del personaje" value={createName} onChange={(e) => onNameChange(e.target.value)} required />

        <Input label="Concepto" value={createConcept} onChange={(e) => onConceptChange(e.target.value)} placeholder="Ej. mercenario callejero" />

        <EntityRefFields
          entities={entities}
          factionId={createFactionId}
          locationId={createLocationId}
          onFactionChange={onFactionChange}
          onLocationChange={onLocationChange}
        />

        <Input

          label="Descripción pública"

          value={createDescription}

          onChange={(e) => onDescriptionChange(e.target.value)}

          placeholder="Lo que ven los demás jugadores"

        />

        <Button type="submit" disabled={isPending || !createName.trim()}>

          {isPending ? "Creando..." : "Crear personaje"}

        </Button>

      </form>

    </section>

  );

}

