import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import type { CampaignEntity, Scene } from "../../api/types";
import { CollapsibleSection } from "../../components/ui";
import { buildSceneRoster } from "../combat/sceneRoster";
import { useUpdateSceneScratchpadMutation } from "../../hooks/mutations/useSceneMutations";
import { getSceneObjective } from "./sceneState";

type CheatSheetTab = "scratchpad" | "secret-lore";

const CHEAT_SHEET_TABS: { id: CheatSheetTab; label: string }[] = [
  { id: "scratchpad", label: "Anotaciones" },
  { id: "secret-lore", label: "Lore secreto" },
];

type MasterCheatSheetProps = {
  campaignId: string;
  scene: Scene;
  entities: CampaignEntity[];
  onSceneUpdate?: (scene: Scene) => void;
};

type RosterSecretLoreEntry = {
  id: string;
  name: string;
  secret: string | null;
};

function readNpcSecretLore(entity: CampaignEntity): string | null {
  const profile = entity.document.ai_narrative_profile as { secret_lore_master?: string } | undefined;
  const secret = profile?.secret_lore_master?.trim();
  return secret || null;
}

export function MasterCheatSheet({ campaignId, scene, entities, onSceneUpdate }: MasterCheatSheetProps) {
  const [activeTab, setActiveTab] = useState<CheatSheetTab>("scratchpad");
  const [scratchpad, setScratchpad] = useState(scene.scene_state.context.master_scene_scratchpad ?? "");
  const lastSavedRef = useRef(scratchpad);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data: briefing, isLoading, error } = useQuery({
    queryKey: queryKeys.scenes.masterBriefing(campaignId, scene.id),
    queryFn: () => api.getMasterBriefing(campaignId, scene.id),
    enabled: Boolean(campaignId && scene.id),
  });

  const scratchpadMutation = useUpdateSceneScratchpadMutation({ campaignId, onSceneUpdate });
  const saveScratchpad = scratchpadMutation.mutate;

  const objective = getSceneObjective(scene.scene_state) ?? briefing?.scene_objective;

  const rosterSecretLore = useMemo((): RosterSecretLoreEntry[] => {
    const roster = buildSceneRoster(scene.scene_state, entities, true);
    return roster
      .filter((entry) => entry.entityType === "NPC")
      .map((entry) => {
        const entity = entities.find((item) => item.id === entry.id);
        return {
          id: entry.id,
          name: entry.label,
          secret: entity ? readNpcSecretLore(entity) : null,
        };
      });
  }, [scene.scene_state, entities]);

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
    <CollapsibleSection
      title="Chuleta del máster"
      description="Anotaciones en juego y lore secreto del roster"
      defaultOpen={false}
    >
      {isLoading && <p className="muted">Cargando briefing…</p>}
      {error && <p className="muted">No se pudo cargar el briefing.</p>}
      <div className="master-cheat-sheet">
        {briefing && (briefing.last_scene_summary || objective || briefing.location) && (
          <div className="master-cheat-sheet__context">
            {briefing.last_scene_summary && (
              <section>
                <h4>Último resumen</h4>
                <p>{briefing.last_scene_summary}</p>
              </section>
            )}
            {objective && (
              <section>
                <h4>Objetivo</h4>
                <p>{objective}</p>
              </section>
            )}
            {briefing.location && (
              <section>
                <h4>Ubicación</h4>
                <p>{briefing.location.name}</p>
              </section>
            )}
          </div>
        )}

        <div className="world-view-tabs master-cheat-sheet__tabs" role="tablist" aria-label="Chuleta del máster">
            {CHEAT_SHEET_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                className={`world-view-tabs__tab${activeTab === tab.id ? " is-active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === "scratchpad" && (
            <div className="master-cheat-sheet__panel" role="tabpanel">
              <label className="sr-only" htmlFor={`master-scratchpad-${scene.id}`}>
                Anotaciones libres del máster
              </label>
              <textarea
                id={`master-scratchpad-${scene.id}`}
                className="master-cheat-sheet__scratchpad"
                rows={6}
                placeholder="Notas rápidas de la escena en curso (solo máster, no se guardan en el resumen al cerrar)…"
                value={scratchpad}
                onChange={(event) => setScratchpad(event.target.value)}
              />
              {scratchpadMutation.isPending && <p className="muted master-cheat-sheet__save-hint">Guardando…</p>}
            </div>
          )}

          {activeTab === "secret-lore" && (
            <div className="master-cheat-sheet__panel" role="tabpanel">
              {rosterSecretLore.length === 0 ? (
                <p className="muted">No hay NPCs en escena.</p>
              ) : (
                <ul className="master-cheat-sheet__lore-list">
                  {rosterSecretLore.map((entry) => (
                    <li key={entry.id}>
                      <strong>{entry.name}</strong>
                      {entry.secret ? (
                        <p className="master-cheat-sheet__lore-text">{entry.secret}</p>
                      ) : (
                        <p className="muted">Sin lore secreto registrado.</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
      </div>
    </CollapsibleSection>
  );
}
