import { useQuery } from "@tanstack/react-query";

import { api } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import type { Scene } from "../../api/types";
import { CollapsibleSection } from "../../components/ui";
import { getSceneObjective } from "./sceneState";

type MasterCheatSheetProps = {
  campaignId: string;
  scene: Scene;
};

export function MasterCheatSheet({ campaignId, scene }: MasterCheatSheetProps) {
  const { data: briefing, isLoading, error } = useQuery({
    queryKey: queryKeys.scenes.masterBriefing(campaignId, scene.id),
    queryFn: () => api.getMasterBriefing(campaignId, scene.id),
    enabled: Boolean(campaignId && scene.id),
  });

  const objective = getSceneObjective(scene.scene_state) ?? briefing?.scene_objective;
  const notes = scene.scene_state.context.master_prep_notes ?? briefing?.master_prep_notes;

  return (
    <CollapsibleSection
      title="Chuleta del máster"
      description="Contexto, secretos y notas de la escena activa"
      defaultOpen={false}
    >
      {isLoading && <p className="muted">Cargando briefing…</p>}
      {error && <p className="muted">No se pudo cargar el briefing.</p>}
      {briefing && (
        <div className="master-cheat-sheet">
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
          {notes && (
            <section>
              <h4>Notas</h4>
              <p>{notes}</p>
            </section>
          )}
          {briefing.npcs.length > 0 && (
            <section>
              <h4>NPCs</h4>
              <ul>
                {briefing.npcs.map((npc) => (
                  <li key={npc.entity_id}>
                    <strong>{npc.name}</strong>
                    {npc.voice_and_tone && <span className="muted"> — {npc.voice_and_tone}</span>}
                    {npc.secret_lore_master && <p className="muted">{npc.secret_lore_master}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </CollapsibleSection>
  );
}
