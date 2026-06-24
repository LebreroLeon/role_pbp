import { useEffect, useRef, useState } from "react";

import type { Scene } from "../../api/types";
import { CollapsibleSection } from "../../components/ui";
import { useUpdateSceneScratchpadMutation } from "../../hooks/mutations/useSceneMutations";

type MasterCheatSheetProps = {
  campaignId: string;
  scene: Scene;
  onSceneUpdate?: (scene: Scene) => void;
};

export function MasterCheatSheet({ campaignId, scene, onSceneUpdate }: MasterCheatSheetProps) {
  const [scratchpad, setScratchpad] = useState(scene.scene_state.context.master_scene_scratchpad ?? "");
  const lastSavedRef = useRef(scratchpad);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scratchpadMutation = useUpdateSceneScratchpadMutation({ campaignId, onSceneUpdate });
  const saveScratchpad = scratchpadMutation.mutate;

  useEffect(() => {
    const remote = scene.scene_state.context.master_scene_scratchpad ?? "";
    setScratchpad(remote);
    lastSavedRef.current = remote;
  }, [scene.id, scene.scene_state.context.master_scene_scratchpad]);

  useEffect(() => {
    if (scratchpad === lastSavedRef.current) return undefined;

    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      const value = scratchpad.trim() || null;
      lastSavedRef.current = scratchpad;
      saveScratchpad({ sceneId: scene.id, master_scene_scratchpad: value });
    }, 600);

    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, [scratchpad, scene.id, saveScratchpad]);

  return (
    <CollapsibleSection title="Anotaciones del máster" defaultOpen={false}>
      <label className="sr-only" htmlFor={`master-scratchpad-${scene.id}`}>
        Anotaciones libres del máster
      </label>
      <textarea
        id={`master-scratchpad-${scene.id}`}
        className="master-cheat-sheet__scratchpad"
        rows={6}
        placeholder="Notas rápidas de la escena en curso (solo máster)…"
        value={scratchpad}
        onChange={(event) => setScratchpad(event.target.value)}
      />
      {scratchpadMutation.isPending && <p className="muted master-cheat-sheet__save-hint">Guardando…</p>}
    </CollapsibleSection>
  );
}
