import { useState } from "react";

import type { ScenePickerItem } from "../../api/types";
import { Button, ConfirmDialog, Modal, MasterOnlyField } from "../../components/ui";
import { formatPreparedScenePickerLabel } from "../campaign";

type NextSceneModalProps = {
  preparedScenes: ScenePickerItem[];
  loading?: boolean;
  onPickPrepared: (sceneId: string) => void;
  onCreateNew: (displayName: string, objective: string) => void;
  onCancel: () => void;
  onCloseOnly?: () => void;
  closedSceneSummary?: string | null;
};

export function NextSceneModal({
  preparedScenes,
  loading,
  onPickPrepared,
  onCreateNew,
  onCancel,
  onCloseOnly,
  closedSceneSummary,
}: NextSceneModalProps) {
  const [newName, setNewName] = useState("");
  const [newObjective, setNewObjective] = useState("");
  const [mode, setMode] = useState<"pick" | "create">(preparedScenes.length > 0 ? "pick" : "create");
  const [pendingScene, setPendingScene] = useState<ScenePickerItem | null>(null);
  const [createConfirmOpen, setCreateConfirmOpen] = useState(false);

  function requestCreate() {
    if (!newObjective.trim()) return;
    setCreateConfirmOpen(true);
  }

  return (
    <>
      <Modal
        title="Escena cerrada"
        titleId="next-scene-title"
        size="md"
        onClose={onCancel}
        footer={
          <div className="ui-modal__actions">
            {onCloseOnly && (
              <Button variant="secondary" onClick={onCloseOnly} disabled={loading}>
                Solo cerrar
              </Button>
            )}
            <Button variant="secondary" onClick={onCancel} disabled={loading}>
              Más tarde
            </Button>
          </div>
        }
      >
        {closedSceneSummary && (
          <section className="next-scene-modal__summary">
            <h3>Resumen generado</h3>
            <p>{closedSceneSummary}</p>
          </section>
        )}

        <p className="muted">
          {preparedScenes.length > 0
            ? "Elige una escena preparada para continuar o crea una nueva desde cero."
            : "No hay escenas preparadas. Puedes crear una nueva escena o volver más tarde."}
        </p>

        {preparedScenes.length > 0 && (
          <div className="next-scene-modal__tabs" role="tablist">
            <button
              type="button"
              className={mode === "pick" ? "is-active" : ""}
              onClick={() => setMode("pick")}
              disabled={loading}
            >
              Preparadas ({preparedScenes.length})
            </button>
            <button
              type="button"
              className={mode === "create" ? "is-active" : ""}
              onClick={() => setMode("create")}
              disabled={loading}
            >
              Nueva
            </button>
          </div>
        )}

        {mode === "pick" && preparedScenes.length > 0 && (
          <ul className="next-scene-modal__list">
            {preparedScenes.map((scene) => (
              <li key={scene.id} className="next-scene-modal__item">
                <div className="next-scene-modal__item-main">
                  <strong>{formatPreparedScenePickerLabel(scene)}</strong>
                  {scene.scene_objective && <span className="muted">{scene.scene_objective}</span>}
                </div>
                <Button type="button" onClick={() => setPendingScene(scene)} disabled={loading}>
                  Seleccionar escena siguiente
                </Button>
              </li>
            ))}
          </ul>
        )}

        {(mode === "create" || preparedScenes.length === 0) && (
          <div className="next-scene-modal__create">
            <label className="form-field" htmlFor="next-scene-name">
              <span>Nombre</span>
              <input
                id="next-scene-name"
                type="text"
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                placeholder='Ej. "La cámara del trono"'
                maxLength={200}
                disabled={loading}
              />
            </label>
            <MasterOnlyField label="Objetivo" htmlFor="next-scene-objective">
              <textarea
                id="next-scene-objective"
                value={newObjective}
                onChange={(event) => setNewObjective(event.target.value)}
                rows={2}
                placeholder="Qué quieres que ocurra (solo para ti)"
                disabled={loading}
              />
            </MasterOnlyField>
            <Button onClick={requestCreate} disabled={loading || !newObjective.trim()}>
              Crear e iniciar
            </Button>
          </div>
        )}
      </Modal>

      {pendingScene && (
        <ConfirmDialog
          title="Activar escena preparada"
          description={
            <>
              <p>
                Vas a activar <strong>{formatPreparedScenePickerLabel(pendingScene)}</strong>. Esta acción es
                irreversible: la escena recibirá el siguiente número disponible y pasará a estar en juego.
              </p>
              <p className="muted">Se mostrará el briefing completo antes de confirmar la activación.</p>
            </>
          }
          confirmLabel="Continuar"
          onConfirm={() => {
            const sceneId = pendingScene.id;
            setPendingScene(null);
            onPickPrepared(sceneId);
          }}
          onCancel={() => setPendingScene(null)}
          confirming={loading}
        />
      )}

      {createConfirmOpen && (
        <ConfirmDialog
          title="Crear e iniciar escena"
          description={
            <>
              <p>
                Se creará una escena nueva{newName.trim() ? ` («${newName.trim()}»)` : ""} y se activará de inmediato.
                Esta acción es irreversible.
              </p>
              <p className="muted">El objetivo de la escena solo es visible para el máster.</p>
            </>
          }
          confirmLabel="Crear e iniciar"
          onConfirm={() => {
            setCreateConfirmOpen(false);
            onCreateNew(newName.trim(), newObjective.trim());
          }}
          onCancel={() => setCreateConfirmOpen(false)}
          confirming={loading}
        />
      )}
    </>
  );
}
