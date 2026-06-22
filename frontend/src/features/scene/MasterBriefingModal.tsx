import type { MasterBriefingResponse } from "../../api/types";
import { Button, Modal } from "../../components/ui";

type MasterBriefingModalProps = {
  briefing: MasterBriefingResponse;
  activating?: boolean;
  sendOpening: boolean;
  onSendOpeningChange: (value: boolean) => void;
  onActivate: () => void;
  onCancel: () => void;
};

export function MasterBriefingModal({
  briefing,
  activating,
  sendOpening,
  onSendOpeningChange,
  onActivate,
  onCancel,
}: MasterBriefingModalProps) {
  const plotLine = briefing.arc_manifest?.plot_line as { title?: string; global_summary?: string } | undefined;
  const activeQuests = (briefing.arc_manifest?.active_quests as Array<{ title?: string; description?: string }>) ?? [];

  return (
    <Modal
      title={`Briefing — ${briefing.display_name ?? `Escena ${briefing.scene_id.slice(0, 8)}`}`}
      titleId="master-briefing-title"
      size="lg"
      onClose={onCancel}
      footer={
        <div className="ui-modal__actions">
          <Button variant="secondary" onClick={onCancel} disabled={activating}>
            Cancelar
          </Button>
          <Button onClick={onActivate} disabled={activating}>
            {activating ? "Activando…" : "Activar escena"}
          </Button>
        </div>
      }
    >
      <div className="master-briefing-modal__body">
        {briefing.last_scene_summary && (
          <section>
            <h3>Resumen anterior</h3>
            <p>{briefing.last_scene_summary}</p>
          </section>
        )}

        {briefing.scene_objective && (
          <section>
            <h3>Objetivo</h3>
            <p>{briefing.scene_objective}</p>
          </section>
        )}

        {briefing.location && (
          <section>
            <h3>Ubicación</h3>
            <p>{briefing.location.name}</p>
          </section>
        )}

        {plotLine && (
          <section>
            <h3>Arco narrativo</h3>
            <p>
              <strong>{plotLine.title}</strong>
              {plotLine.global_summary ? ` — ${plotLine.global_summary}` : ""}
            </p>
          </section>
        )}

        {activeQuests.length > 0 && (
          <section>
            <h3>Misiones activas</h3>
            <ul>
              {activeQuests.map((quest) => (
                <li key={quest.title ?? quest.description}>
                  <strong>{quest.title}</strong>
                  {quest.description ? `: ${quest.description}` : ""}
                </li>
              ))}
            </ul>
          </section>
        )}

        {briefing.npcs.length > 0 && (
          <section>
            <h3>NPCs en escena</h3>
            <ul className="master-briefing-modal__npc-list">
              {briefing.npcs.map((npc) => (
                <li key={npc.entity_id}>
                  <strong>{npc.name}</strong>
                  <span className="muted"> ({npc.player_visibility})</span>
                  {npc.voice_and_tone && <p className="muted">Voz: {npc.voice_and_tone}</p>}
                  {npc.secret_lore_master && <p>Secreto: {npc.secret_lore_master}</p>}
                </li>
              ))}
            </ul>
          </section>
        )}

        {briefing.master_prep_notes && (
          <section>
            <h3>Notas del máster</h3>
            <p>{briefing.master_prep_notes}</p>
          </section>
        )}

        {briefing.opening_narration && (
          <section>
            <h3>Apertura</h3>
            <p className="master-briefing-modal__opening">{briefing.opening_narration}</p>
            <label className="master-briefing-modal__opening-check">
              <input
                type="checkbox"
                checked={sendOpening}
                onChange={(event) => onSendOpeningChange(event.target.checked)}
                disabled={activating}
              />
              Enviar apertura al chat al activar
            </label>
          </section>
        )}
      </div>
    </Modal>
  );
}
