import { FormEvent, useState } from "react";

import { ApiError } from "../../api/http";
import { Button, ErrorBanner, Input, Panel, PanelHeader } from "../../components/ui";
import { useCreateCampaignMutation } from "../../hooks/mutations/useCampaignMutations";

export function CreateCampaignForm() {
  const [name, setName] = useState("");
  const [tone, setTone] = useState("");
  const mutation = useCreateCampaignMutation();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    mutation.mutate(
      { name: name.trim(), tone: tone.trim() || undefined },
      {
        onSuccess: () => {
          setName("");
          setTone("");
        },
      },
    );
  }

  const apiError = mutation.error instanceof ApiError ? mutation.error.message : null;

  return (
    <Panel>
      <PanelHeader title="Nueva campaña" description="Serás el Máster de la campaña que crees." />
      <form className="auth-form" onSubmit={handleSubmit}>
        <Input label="Nombre" value={name} onChange={(event) => setName(event.target.value)} required />
        <Input
          label="Tono (opcional)"
          value={tone}
          onChange={(event) => setTone(event.target.value)}
          placeholder="Ej. grimdark, heroico, intriga urbana..."
        />
        {apiError && <ErrorBanner message={apiError} />}
        <Button type="submit" disabled={mutation.isPending || !name.trim()}>
          {mutation.isPending ? "Creando..." : "Crear campaña"}
        </Button>
      </form>
    </Panel>
  );
}
