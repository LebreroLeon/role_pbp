import { FormEvent, useRef, useState } from "react";

import { api } from "../../api/client";
import { ApiError } from "../../api/http";
import type { EntityExportBundle } from "../../api/types";
import { Button, ErrorBanner, Panel, PanelHeader } from "../../components/ui";
import { useImportEntitiesMutation } from "../../hooks/mutations/useEntityImportMutations";
import { EXPORT_FORMAT_HINT, LOCATION_TEMPLATE, NPC_TEMPLATE, downloadJson } from "./entityTemplates";

type ImportExportPanelProps = {
  campaignId: string;
};

export function ImportExportPanel({ campaignId }: ImportExportPanelProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [jsonText, setJsonText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const importMutation = useImportEntitiesMutation(campaignId);

  async function handleExport() {
    setExporting(true);
    setError(null);
    setSuccess(null);
    try {
      const bundle = await api.exportEntities(campaignId);
      downloadJson(`rolepbp-${campaignId.slice(0, 8)}-mundo.json`, bundle);
      setSuccess("Mundo exportado correctamente.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo exportar");
    } finally {
      setExporting(false);
    }
  }

  function parseBundle(raw: string): EntityExportBundle["entities"] {
    const parsed = JSON.parse(raw) as EntityExportBundle | { entities?: EntityExportBundle["entities"] };
    if (Array.isArray(parsed)) return parsed;
    if ("entities" in parsed && Array.isArray(parsed.entities)) return parsed.entities;
    throw new Error("JSON inválido: falta el array entities");
  }

  async function handleImport(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      const entities = parseBundle(jsonText);
      const result = await importMutation.mutateAsync(entities);
      setSuccess(`Importados ${result.created} elementos al mundo.`);
      setJsonText("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : err instanceof Error ? err.message : "Importación fallida");
    }
  }

  function handleFileSelect(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") setJsonText(reader.result);
    };
    reader.readAsText(file);
    event.target.value = "";
  }

  return (
    <Panel>
      <PanelHeader
        title="Importar y exportar mundo"
        description="Copia de seguridad en JSON o carga NPCs y lugares desde otro archivo RolePBP."
      />

      <div className="import-export__actions">
        <Button onClick={handleExport} disabled={exporting}>
          {exporting ? "Exportando..." : "Exportar mundo (JSON)"}
        </Button>
        <Button variant="secondary" onClick={() => downloadJson("plantilla-npc.json", NPC_TEMPLATE)}>
          Plantilla NPC
        </Button>
        <Button variant="secondary" onClick={() => downloadJson("plantilla-ubicacion.json", LOCATION_TEMPLATE)}>
          Plantilla ubicación
        </Button>
      </div>

      <form className="auth-form import-export__form" onSubmit={handleImport}>
        <label className="form-field">
          <span>Pegar JSON o elegir archivo</span>
          <textarea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={8} />
        </label>
        <input ref={fileRef} type="file" accept=".json,application/json" hidden onChange={handleFileSelect} />
        <div className="actions">
          <Button type="button" variant="secondary" onClick={() => fileRef.current?.click()}>
            Elegir archivo JSON
          </Button>
          <Button type="submit" disabled={importMutation.isPending || !jsonText.trim()}>
            {importMutation.isPending ? "Importando..." : "Importar al mundo"}
          </Button>
        </div>
      </form>

      <details className="import-export__hint">
        <summary>Formato esperado</summary>
        <pre>{EXPORT_FORMAT_HINT}</pre>
      </details>

      <p className="muted import-export__note">
        La extracción automática de NPCs desde PDFs de aventuras llegará con la integración de IA.
      </p>

      {error && <ErrorBanner message={error} />}
      {success && <p className="ok">{success}</p>}
    </Panel>
  );
}
