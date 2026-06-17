import { FormEvent, useState } from "react";

import { useParams } from "react-router-dom";



import { ApiError } from "../../api/http";

import type { SheetRollRequest } from "../../api/types";

import { Scroll } from "../../components/icons";

import { Button, ErrorBanner, Input, Panel, PanelHeader } from "../../components/ui";

import { gameSystemLabel, getGameSystemProfile, hasSheetTemplate } from "../campaign/gameSystems";

import { useUpsertMySheetMutation, useRollFromSheetMutation } from "../../hooks/mutations/useMySheetMutations";

import { useCampaignQuery } from "../../hooks/queries/useCampaignQueries";

import { useMySheetQuery } from "../../hooks/queries/useMySheetQueries";

import { useAuthStore } from "../../stores/authStore";

import {

  buildCharacterSheetUpsert,

  defaultSheetForGameSystem,

  documentToCharacterSheetUpsert,

  extractSheetFromEntity,

  mergeSheetIntoDocument,

  type GameSheet,

} from "./pcDocument";

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

  const upsertMutation = useUpsertMySheetMutation(campaignId);

  const rollMutation = useRollFromSheetMutation(campaignId);



  const [createName, setCreateName] = useState("");

  const [createConcept, setCreateConcept] = useState("");

  const [createDescription, setCreateDescription] = useState("");

  const [formError, setFormError] = useState<string | null>(null);

  const [rollSummary, setRollSummary] = useState<string | null>(null);



  const gameSystem = campaign?.game_system ?? "generic";

  const profile = getGameSystemProfile(gameSystem);

  const supportsSheet = hasSheetTemplate(gameSystem);

  const hasSheetEditor = supportsSheet && gameSystem !== "generic";



  async function handleCreatePc(event: FormEvent) {

    event.preventDefault();

    if (!createName.trim() || !currentUser) return;

    setFormError(null);



    const payload = buildCharacterSheetUpsert({

      name: createName,

      concept: createConcept,

      description: createDescription,

      systemId: gameSystem,

    });



    try {

      await upsertMutation.mutateAsync(payload);

    } catch (err) {

      setFormError(err instanceof ApiError ? err.message : "No se pudo crear el personaje");

    }

  }



  async function handleSaveSheet(sheet: GameSheet) {

    if (!myPc) return;

    setFormError(null);



    const document = mergeSheetIntoDocument(myPc.document, gameSystem, sheet as Record<string, unknown>);

    const payload = documentToCharacterSheetUpsert(document);



    try {

      await upsertMutation.mutateAsync(payload);

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

    } catch (err) {

      setFormError(err instanceof ApiError ? err.message : "No se pudo tirar los dados");

    }

  }



  const extracted = myPc ? extractSheetFromEntity(myPc.document) : null;

  const sheetDefaults = parseSheetForSystem(gameSystem, extracted?.sheet);

  const pcName =

    (myPc?.document.identity as { name?: string } | undefined)?.name ?? "Sin nombre";



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

        {rollSummary && <p className="sheet-roll-summary">{rollSummary}</p>}



        {isLoading && <p className="muted">Cargando ficha...</p>}



        {isError && !myPc && !(error instanceof ApiError && error.status === 404) && (

          <ErrorBanner message={error instanceof Error ? error.message : "Error al cargar la ficha"} />

        )}



        {!isLoading && !myPc && (

          <SectionCreatePc

            gameSystem={gameSystem}

            supportsSheet={supportsSheet}

            createName={createName}

            createConcept={createConcept}

            createDescription={createDescription}

            onNameChange={setCreateName}

            onConceptChange={setCreateConcept}

            onDescriptionChange={setCreateDescription}

            onSubmit={handleCreatePc}

            isPending={upsertMutation.isPending}

          />

        )}



        {myPc && hasSheetEditor && (

          <>

            <p className="sheet-pc-name">

              <strong>{pcName}</strong>

            </p>

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

  createName: string;

  createConcept: string;

  createDescription: string;

  onNameChange: (value: string) => void;

  onConceptChange: (value: string) => void;

  onDescriptionChange: (value: string) => void;

  onSubmit: (event: FormEvent) => void;

  isPending: boolean;

};



function SectionCreatePc({

  gameSystem,

  supportsSheet,

  createName,

  createConcept,

  createDescription,

  onNameChange,

  onConceptChange,

  onDescriptionChange,

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

