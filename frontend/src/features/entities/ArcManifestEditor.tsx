import { FormEvent, useState } from "react";

import { ApiError } from "../../api/http";
import { Button, ErrorBanner, Input } from "../../components/ui";
import { useUpdateEntityMutation } from "../../hooks/mutations/useEntityMutations";
import { newQuestId, type CampaignEntity } from "./entityDefaults";

type QuestFormRow = {
  questId: string;
  title: string;
  description: string;
  secretDmNotes: string;
};

type ArcManifestEditorProps = {
  campaignId: string;
  entity: CampaignEntity;
  onSaved: () => void;
  onCancel: () => void;
};

function buildQuestRows(entity: CampaignEntity): QuestFormRow[] {
  const quests = entity.document.active_quests;
  if (!Array.isArray(quests) || quests.length === 0) {
    return [];
  }
  return quests.map((raw) => {
    const quest = raw as Record<string, unknown>;
    return {
      questId: String(quest.quest_id ?? newQuestId()),
      title: String(quest.title ?? ""),
      description: String(quest.description ?? ""),
      secretDmNotes: String(quest.secret_dm_notes ?? ""),
    };
  });
}

function buildFormState(entity: CampaignEntity) {
  const plotLine = entity.document.plot_line as Record<string, unknown> | undefined;
  const stateFlags = entity.document.state_flags as Record<string, unknown> | undefined;
  return {
    title: String(plotLine?.title ?? ""),
    globalSummary: String(plotLine?.global_summary ?? ""),
    currentAct: Number(plotLine?.current_act ?? 1),
    narrativeTone: String(plotLine?.narrative_tone ?? ""),
    worldThreatLevel: Number(stateFlags?.world_threat_level ?? 1),
    plotDerailed: Boolean(stateFlags?.is_main_plot_derailed ?? false),
    quests: buildQuestRows(entity),
  };
}

export function ArcManifestEditor({ campaignId, entity, onSaved, onCancel }: ArcManifestEditorProps) {
  const mutation = useUpdateEntityMutation(campaignId);
  const [form, setForm] = useState(() => buildFormState(entity));
  const apiError = mutation.error instanceof ApiError ? mutation.error.message : null;

  function updateQuest(index: number, patch: Partial<QuestFormRow>) {
    setForm((current) => ({
      ...current,
      quests: current.quests.map((quest, questIndex) =>
        questIndex === index ? { ...quest, ...patch } : quest,
      ),
    }));
  }

  function addQuest() {
    setForm((current) => ({
      ...current,
      quests: [
        ...current.quests,
        { questId: newQuestId(), title: "", description: "", secretDmNotes: "" },
      ],
    }));
  }

  function removeQuest(index: number) {
    setForm((current) => ({
      ...current,
      quests: current.quests.filter((_, questIndex) => questIndex !== index),
    }));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const document = structuredClone(entity.document);
    document.plot_line = {
      title: form.title.trim() || "Arco principal",
      global_summary: form.globalSummary.trim(),
      current_act: Math.max(1, form.currentAct),
      narrative_tone: form.narrativeTone.trim() || "Aventura",
    };
    document.active_quests = form.quests
      .filter((quest) => quest.title.trim() || quest.description.trim())
      .map((quest) => ({
        quest_id: quest.questId,
        title: quest.title.trim(),
        description: quest.description.trim(),
        required_triggers: [],
        secret_dm_notes: quest.secretDmNotes.trim(),
      }));
    document.state_flags = {
      is_main_plot_derailed: form.plotDerailed,
      world_threat_level: Math.min(10, Math.max(0, form.worldThreatLevel)),
    };

    mutation.mutate({ entityId: entity.id, document }, { onSuccess: () => onSaved() });
  }

  return (
    <form className="auth-form arc-manifest-form" onSubmit={handleSubmit}>
      <Input
        label="Título del arco"
        value={form.title}
        onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
        required
      />
      <label className="form-field">
        <span>Resumen global (macrotrama)</span>
        <textarea
          value={form.globalSummary}
          onChange={(event) => setForm((current) => ({ ...current, globalSummary: event.target.value }))}
          rows={4}
        />
      </label>
      <Input
        label="Acto actual"
        type="number"
        min={1}
        value={form.currentAct}
        onChange={(event) => setForm((current) => ({ ...current, currentAct: Number(event.target.value) }))}
      />
      <Input
        label="Tono narrativo"
        value={form.narrativeTone}
        onChange={(event) => setForm((current) => ({ ...current, narrativeTone: event.target.value }))}
      />
      <Input
        label="Nivel de amenaza mundial (0-10)"
        type="number"
        min={0}
        max={10}
        value={form.worldThreatLevel}
        onChange={(event) =>
          setForm((current) => ({ ...current, worldThreatLevel: Number(event.target.value) }))
        }
      />
      <label className="form-field">
        <span>
          <input
            type="checkbox"
            checked={form.plotDerailed}
            onChange={(event) => setForm((current) => ({ ...current, plotDerailed: event.target.checked }))}
          />{" "}
          Trama principal desviada
        </span>
      </label>

      <section className="arc-manifest-quests">
        <div className="arc-manifest-quests__head">
          <h4>Misiones activas</h4>
          <Button type="button" variant="secondary" onClick={addQuest}>
            Añadir misión
          </Button>
        </div>
        {form.quests.length === 0 && (
          <p className="muted">Sin misiones activas. Añade al menos una para guiar a Shadow Master.</p>
        )}
        {form.quests.map((quest, index) => (
          <div key={quest.questId} className="arc-manifest-quest">
            <Input
              label={`Misión ${index + 1} — título`}
              value={quest.title}
              onChange={(event) => updateQuest(index, { title: event.target.value })}
            />
            <label className="form-field">
              <span>Descripción (objetivo visible)</span>
              <textarea
                value={quest.description}
                onChange={(event) => updateQuest(index, { description: event.target.value })}
                rows={2}
              />
            </label>
            <label className="form-field sheet-secret-field">
              <span>Notas secretas del Máster</span>
              <textarea
                value={quest.secretDmNotes}
                onChange={(event) => updateQuest(index, { secretDmNotes: event.target.value })}
                rows={2}
              />
            </label>
            <Button type="button" variant="secondary" onClick={() => removeQuest(index)}>
              Quitar misión
            </Button>
          </div>
        ))}
      </section>

      {apiError && <ErrorBanner message={apiError} />}
      <div className="form-actions">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={mutation.isPending || !form.title.trim()}>
          {mutation.isPending ? "Guardando..." : "Guardar arco narrativo"}
        </Button>
      </div>
    </form>
  );
}
