import { StatusBadge } from "../../components/ui";
import { gameSystemLabel } from "../campaign/gameSystems";
import { useSystemManualStatusQuery } from "../../hooks/queries/useSystemManualQueries";

type SystemManualsPanelProps = {
  gameSystem?: string | null;
};

function statusLabel(indexed: boolean, onDisk: boolean): { text: string; ok: boolean } {
  if (!onDisk) return { text: "No encontrado", ok: false };
  if (indexed) return { text: "Indexado", ok: true };
  return { text: "Pendiente", ok: false };
}

export function SystemManualsPanel({ gameSystem }: SystemManualsPanelProps) {
  const systemId = gameSystem ?? undefined;
  const { data, isLoading, isError, error } = useSystemManualStatusQuery(systemId);

  if (!systemId) {
    return <p className="muted">Esta campaña no tiene sistema de juego definido.</p>;
  }

  if (isLoading) {
    return <p className="muted">Cargando manuales de {gameSystemLabel(systemId)}…</p>;
  }

  if (isError) {
    return (
      <p className="muted">
        No se pudo cargar el estado de manuales: {error instanceof Error ? error.message : "error"}
      </p>
    );
  }

  const files = data?.files ?? [];
  const indexedCount = files.filter((file) => file.indexed).length;
  const hasRules = indexedCount > 0;

  return (
    <section className="system-manuals-panel">
      <header className="system-manuals-panel__head">
        <h3>Reglas oficiales — {gameSystemLabel(systemId)}</h3>
        <StatusBadge
          label=""
          value={hasRules ? "Disponibles para la IA" : "Sin indexar"}
          ok={hasRules}
        />
      </header>
      <p className="muted system-manuals-panel__hint">
        Copia PDFs licenciados en <code>data/manuals/{systemId}/</code> y ejecuta{" "}
        <code>python backend/scripts/index_system_manuals.py --system {systemId}</code>. Ver{" "}
        <code>data/manuals/{systemId}/README.md</code>.
      </p>
      {files.length === 0 ? (
        <p className="muted">No hay PDFs en la carpeta del sistema.</p>
      ) : (
        <ul className="system-manuals-list">
          {files.map((file) => {
            const onDisk = Boolean(file.path);
            const status = statusLabel(file.indexed, onDisk);
            return (
              <li key={file.filename} className="system-manuals-list__item">
                <span className="system-manuals-list__name">{file.filename}</span>
                <StatusBadge label="" value={status.text} ok={status.ok} />
                {file.indexed && file.chunk_count > 0 && (
                  <span className="muted">{file.chunk_count} fragmentos</span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
