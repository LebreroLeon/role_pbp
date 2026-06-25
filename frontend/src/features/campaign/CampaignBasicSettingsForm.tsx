import { FormEvent, useEffect, useId, useState } from "react";

import type { Campaign } from "../../api/types";
import { Button, ErrorBanner, Input, MasterOnlyField } from "../../components/ui";
import { useUpdateCampaignMutation } from "../../hooks/mutations/useCampaignMutations";
import { gameSystemLabel } from "./gameSystems";

type CampaignBasicSettingsFormProps = {
  campaignId: string;
  campaign: Campaign | undefined;
  formId?: string;
  showHeading?: boolean;
  hideSubmitButton?: boolean;
  onSaved?: () => void;
  onPendingChange?: (pending: boolean) => void;
};

export function CampaignBasicSettingsForm({
  campaignId,
  campaign,
  formId,
  showHeading = false,
  hideSubmitButton = false,
  onSaved,
  onPendingChange,
}: CampaignBasicSettingsFormProps) {
  const toneFieldId = useId();
  const mutation = useUpdateCampaignMutation(campaignId);
  const [name, setName] = useState(campaign?.name ?? "");
  const [tone, setTone] = useState(campaign?.tone ?? "");
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    setName(campaign?.name ?? "");
    setTone(campaign?.tone ?? "");
  }, [campaign?.name, campaign?.tone]);

  useEffect(() => {
    onPendingChange?.(mutation.isPending);
  }, [mutation.isPending, onPendingChange]);

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    setSavedMessage(null);
    try {
      await mutation.mutateAsync({
        name: name.trim() || undefined,
        tone: tone.trim(),
      });
      setSavedMessage("Cambios guardados.");
      onSaved?.();
    } catch {
      // mutation.error is surfaced below
    }
  }

  const error = mutation.error instanceof Error ? mutation.error.message : null;

  return (
    <form id={formId} className="auth-form campaign-basic-settings" onSubmit={handleSave}>
      {showHeading && <h3>Datos de la campaña</h3>}
      <p className="muted">
        <strong>Sistema:</strong> {gameSystemLabel(campaign?.game_system)}
      </p>
      <Input label="Nombre" value={name} onChange={(event) => setName(event.target.value)} required autoFocus={!showHeading} />
      <MasterOnlyField
        label="Tono narrativo"
        htmlFor={toneFieldId}
        description="Solo para tu preparación; los jugadores no lo ven en la campaña."
      >
        <input
          id={toneFieldId}
          type="text"
          value={tone}
          onChange={(event) => setTone(event.target.value)}
          placeholder="Ej. intriga urbana, horror cósmico, heroico..."
        />
      </MasterOnlyField>
      {error && <ErrorBanner message={error} />}
      {savedMessage && <p className="muted">{savedMessage}</p>}
      {!hideSubmitButton && (
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Guardando…" : "Guardar cambios"}
        </Button>
      )}
    </form>
  );
}
