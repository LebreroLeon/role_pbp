import { FormEvent, useState } from "react";

import { ApiError } from "../../api/http";
import { Button, ErrorBanner, Input, Panel, PanelHeader } from "../../components/ui";
import { useInviteMemberMutation } from "../../hooks/mutations/useCampaignMutations";

type InviteMemberFormProps = {
  campaignId: string;
  hideHeader?: boolean;
};

export function InviteMemberForm({ campaignId, hideHeader = false }: InviteMemberFormProps) {
  const [email, setEmail] = useState("");
  const mutation = useInviteMemberMutation(campaignId);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!email.trim()) return;
    mutation.mutate(
      { email: email.trim(), role: "PLAYER" },
      {
        onSuccess: () => setEmail(""),
      },
    );
  }

  const apiError = mutation.error instanceof ApiError ? mutation.error.message : null;

  const form = (
    <form className="auth-form" onSubmit={handleSubmit}>
      <Input
        label="Email del jugador"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        required
      />
      {apiError && <ErrorBanner message={apiError} />}
        <Button type="submit" disabled={mutation.isPending || !email.trim()}>
        {mutation.isPending ? "Invitando..." : "Añadir jugador"}
      </Button>
    </form>
  );

  if (hideHeader) return form;

  return (
    <Panel>
      <PanelHeader
        title="Invitar jugador"
        description="El usuario debe estar registrado con ese email."
      />
      {form}
    </Panel>
  );
}
