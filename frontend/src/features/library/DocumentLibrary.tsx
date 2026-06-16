import { FormEvent, useRef, useState } from "react";

import { downloadAuthenticatedFile } from "../../api/download";
import { ApiError } from "../../api/http";
import type { DocumentType } from "../../api/types";
import { Button, ErrorBanner, Panel, PanelHeader } from "../../components/ui";
import {
  useDeleteDocumentMutation,
  useDocumentsQuery,
  useUploadDocumentMutation,
} from "../../hooks/queries/useDocumentQueries";

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  RULES: "Reglas / manual",
  ADVENTURE: "Aventura / módulo",
  NOTES: "Notas del Máster",
  EXPORT: "Exportación",
  OTHER: "Otro",
};

type DocumentLibraryProps = {
  campaignId: string;
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentLibrary({ campaignId }: DocumentLibraryProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [documentType, setDocumentType] = useState<DocumentType>("RULES");
  const [error, setError] = useState<string | null>(null);
  const { data: documents = [], isLoading } = useDocumentsQuery(campaignId);
  const uploadMutation = useUploadDocumentMutation(campaignId);
  const deleteMutation = useDeleteDocumentMutation(campaignId);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setError(null);
    try {
      await uploadMutation.mutateAsync({ file, documentType });
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo subir el archivo");
    }
  }

  async function handleDownload(documentId: string, filename: string) {
    setDownloadingId(documentId);
    setError(null);
    try {
      await downloadAuthenticatedFile(`/api/v1/documents/${documentId}/download`, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo descargar");
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <div className="library-page">
      <Panel>
        <PanelHeader
          title="Subir material"
          description="Manuales, módulos de campaña, notas o JSON de respaldo. La IA los usará más adelante como referencia."
        />
        <form className="auth-form" onSubmit={handleUpload}>
          <label className="form-field">
            <span>Tipo de documento</span>
            <select value={documentType} onChange={(e) => setDocumentType(e.target.value as DocumentType)}>
              {Object.entries(DOCUMENT_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>Archivo (PDF, JSON, TXT, MD, DOCX, ZIP — máx. 20 MB)</span>
            <input ref={fileRef} type="file" accept=".pdf,.json,.txt,.md,.docx,.zip" required />
          </label>
          {error && <ErrorBanner message={error} />}
          <Button type="submit" disabled={uploadMutation.isPending}>
            {uploadMutation.isPending ? "Subiendo..." : "Subir a la biblioteca"}
          </Button>
        </form>
      </Panel>

      <Panel>
        <PanelHeader title="Archivos de la campaña" description={`${documents.length} documentos`} />
        {isLoading && <p className="muted">Cargando biblioteca...</p>}
        {!isLoading && documents.length === 0 && (
          <p className="muted">Aún no hay archivos. Sube manuales o el módulo de tu aventura.</p>
        )}
        {documents.length > 0 && (
          <ul className="document-list">
            {documents.map((doc) => (
              <li key={doc.id} className="document-card">
                <div>
                  <strong>{doc.original_name}</strong>
                  <p className="muted document-card__meta">
                    {DOCUMENT_TYPE_LABELS[doc.document_type]} · {formatSize(doc.size_bytes)}
                  </p>
                </div>
                <div className="actions">
                  <Button
                    variant="secondary"
                    disabled={downloadingId === doc.id}
                    onClick={() => handleDownload(doc.id, doc.original_name)}
                  >
                    {downloadingId === doc.id ? "..." : "Descargar"}
                  </Button>
                  <Button
                    variant="secondary"
                    disabled={deleteMutation.isPending}
                    onClick={() => deleteMutation.mutate(doc.id)}
                  >
                    Eliminar
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
