import { FormEvent, useState } from "react";
import { useParams } from "react-router-dom";

import { ApiError } from "../../api/http";
import { RoleGate } from "../../components/auth/RoleGate";
import { Users } from "../../components/icons";
import { Button, ErrorBanner, Input, Panel, PanelHeader } from "../../components/ui";
import { getGameSystemProfile, hasSheetTemplate } from "../campaign/gameSystems";
import { getEntityDisplayName, buildPcDocumentForGameSystem } from "../entities/entityDefaults";
import { useCreateEntityMutation } from "../../hooks/mutations/useEntityMutations";
import { useCampaignMembersQuery, useCampaignQuery } from "../../hooks/queries/useCampaignQueries";
import { useCampaignSheetsQuery } from "../../hooks/queries/useCampaignSheetsQueries";
import { EntitySheetEditor } from "./EntitySheetEditor";

export function CampaignSheetsPage() {
  const { campaignId = "" } = useParams();
  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: sheets = [], isLoading, isError, error } = useCampaignSheetsQuery(campaignId);
  const createMutation = useCreateEntityMutation(campaignId);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createConcept, setCreateConcept] = useState("");
  const [createDescription, setCreateDescription] = useState("");
  const [createPlayerId, setCreatePlayerId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const gameSystem = campaign?.game_system ?? "generic";
  const profile = getGameSystemProfile(gameSystem);
  const supportsSheet = hasSheetTemplate(gameSystem);
  const selected = sheets.find((sheet) => sheet.id === selectedId) ?? null;
  const players = members.filter((member) => member.role === "PLAYER");
  const playersWithoutSheet = players.filter(
    (player) =>
      !sheets.some(
        (sheet) =>
          (sheet.document.player_binding as { user_id?: string } | undefined)?.user_id === player.user_id,
      ),
  );

  async function handleCreatePc(event: FormEvent) {
    event.preventDefault();
    if (!createName.trim() || !createPlayerId) return;
    setFormError(null);

    const document = buildPcDocumentForGameSystem({
      name: createName,
      concept: createConcept,
      description: createDescription,
      userId: createPlayerId,
      systemId: gameSystem,
    });

    try {
      const created = await createMutation.mutateAsync({ entity_type: "PC", document });
      setShowCreate(false);
      setCreateName("");
      setCreateConcept("");
      setCreateDescription("");
      setSelectedId(created.id);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "No se pudo crear el personaje");
    }
  }

  function playerNameForSheet(userId: string | undefined): string {
    if (!userId) return "Sin jugador";
    const member = members.find((item) => item.user_id === userId);
    return member?.display_name ?? userId.slice(0, 8);
  }

  return (
    <RoleGate role="MASTER">
      <div className="campaign-sheets-page">
        <Panel>
          <PanelHeader
            icon={Users}
            iconTone="violet"
            title="Fichas de jugadores"
            description="Control total de todos los PJs: datos narrativos, mecánicas y secretos visibles solo para el Máster."
          />

          {formError && <ErrorBanner message={formError} />}
          {isError && (
            <ErrorBanner message={error instanceof Error ? error.message : "Error al cargar fichas"} />
          )}

          <div className="campaign-sheets-layout">
            <aside className="campaign-sheets-list">
              <div className="campaign-sheets-list__header">
                <h3>Personajes ({sheets.length})</h3>
                {playersWithoutSheet.length > 0 && (
                  <Button type="button" variant="secondary" onClick={() => setShowCreate((value) => !value)}>
                    {showCreate ? "Cancelar" : "Crear PJ"}
                  </Button>
                )}
              </div>

              {isLoading && <p className="muted">Cargando fichas...</p>}
              {!isLoading && sheets.length === 0 && (
                <p className="muted">No hay personajes jugadores en esta campaña.</p>
              )}

              <ul className="sheet-picker">
                {sheets.map((sheet) => {
                  const userId = (sheet.document.player_binding as { user_id?: string } | undefined)?.user_id;
                  return (
                    <li key={sheet.id}>
                      <button
                        type="button"
                        className={`sheet-picker__item ${selectedId === sheet.id ? "is-active" : ""}`}
                        onClick={() => setSelectedId(sheet.id)}
                      >
                        <strong>{getEntityDisplayName(sheet)}</strong>
                        <span className="muted">{playerNameForSheet(userId)}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>

              {showCreate && (
                <form className="auth-form sheet-create-inline" onSubmit={handleCreatePc}>
                  <p className="muted">
                    Crear ficha para un jugador sin PJ.
                    {profile && (
                      <>
                        {" "}
                        Plantilla <strong>{profile.sheetTemplateId}</strong> ({profile.previewSummary}).
                      </>
                    )}
                    {!supportsSheet && " Sistema sin plantilla mecánica."}
                  </p>
                  <label className="form-field">
                    <span>Jugador</span>
                    <select
                      value={createPlayerId}
                      onChange={(event) => setCreatePlayerId(event.target.value)}
                      required
                    >
                      <option value="">Selecciona jugador</option>
                      {playersWithoutSheet.map((player) => (
                        <option key={player.user_id} value={player.user_id}>
                          {player.display_name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <Input
                    label="Nombre del personaje"
                    value={createName}
                    onChange={(event) => setCreateName(event.target.value)}
                    required
                  />
                  <Input
                    label="Concepto"
                    value={createConcept}
                    onChange={(event) => setCreateConcept(event.target.value)}
                  />
                  <Input
                    label="Descripción pública"
                    value={createDescription}
                    onChange={(event) => setCreateDescription(event.target.value)}
                  />
                  <Button type="submit" disabled={createMutation.isPending || !createName.trim() || !createPlayerId}>
                    {createMutation.isPending ? "Creando..." : "Crear personaje"}
                  </Button>
                </form>
              )}
            </aside>

            <section className="campaign-sheets-editor">
              {selected ? (
                <EntitySheetEditor
                  campaignId={campaignId}
                  entity={selected}
                  gameSystem={gameSystem}
                  members={members}
                  onCancel={() => setSelectedId(null)}
                />
              ) : (
                <p className="muted">Selecciona un personaje para ver y editar su ficha completa.</p>
              )}
            </section>
          </div>
        </Panel>
      </div>
    </RoleGate>
  );
}
