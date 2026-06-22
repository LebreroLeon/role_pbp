import { useState } from "react";

import type { ScenePickerItem } from "../../api/types";
import { Button, Modal } from "../../components/ui";

type NextSceneModalProps = {
  preparedScenes: ScenePickerItem[];
  loading?: boolean;
  onPickPrepared: (sceneId: string) => void;
  onCreateNew: (displayName: string, objective: string) => void;
  onCancel: () => void;
};

export function NextSceneModal({
  preparedScenes,
  loading,
  onPickPrepared,
  onCreateNew,
  onCancel,
}: NextSceneModalProps) {
  const [newName, setNewName] = useState("");
  const [newObjective, setNewObjective] = useState("");
  const [mode, setMode] = useState<"pick" | "create">(preparedScenes.length > 0 ? "pick" : "create");

  return (
    <Modal
      title="Siguiente escena"
      titleId="next-scene-title"
      size="md"
      onClose={onCancel}
      footer={
        <div className="ui-modal__actions">
          <Button variant="secondary" onClick={onCancel} disabled={loading}>
            Más tarde
          </Button>
        </div>
      }
    >
      <p className="muted">Elige una escena preparada o crea una nueva desde cero.</p>

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
            <li key={scene.id}>
              <button
                type="button"
                className="next-scene-modal__option"
                onClick={() => onPickPrepared(scene.id)}
                disabled={loading}
              >
                <strong>
                  Escena {scene.scene_number}
                  {scene.display_name ? `: ${scene.display_name}` : ""}
                </strong>
                {scene.scene_objective && <span className="muted">{scene.scene_objective}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}

      {(mode === "create" || preparedScenes.length === 0) && (
        <div className="next-scene-modal__create">
          <label className="field-label" htmlFor="next-scene-name">
            Nombre
          </label>
          <input
            id="next-scene-name"
            type="text"
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
            placeholder='Ej. "La cámara del trono"'
            maxLength={200}
            disabled={loading}
          />
          <label className="field-label" htmlFor="next-scene-objective">
            Objetivo
          </label>
          <textarea
            id="next-scene-objective"
            value={newObjective}
            onChange={(event) => setNewObjective(event.target.value)}
            rows={2}
            placeholder="Qué debe ocurrir en esta escena"
            disabled={loading}
          />
          <Button
            onClick={() => onCreateNew(newName.trim(), newObjective.trim())}
            disabled={loading || !newObjective.trim()}
          >
            Crear e iniciar
          </Button>
        </div>
      )}
    </Modal>
  );
}
