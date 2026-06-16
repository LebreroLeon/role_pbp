import { FormEvent, useState } from "react";

import type { CampaignMember } from "../../api/types";
import { ApiError } from "../../api/http";
import { Button, ErrorBanner, Input, Panel, PanelHeader } from "../../components/ui";
import { useCreateEntityMutation } from "../../hooks/mutations/useEntityMutations";
import {
  buildLocationDocument,
  buildNpcDocument,
  buildPcDocument,
  type EntityType,
} from "./entityDefaults";

const CREATABLE_TYPES: EntityType[] = ["NPC", "LOCATION", "PC"];

type CreateEntityFormProps = {
  campaignId: string;
  members: CampaignMember[];
};

export function CreateEntityForm({ campaignId, members }: CreateEntityFormProps) {
  const [entityType, setEntityType] = useState<EntityType>("NPC");
  const [name, setName] = useState("");
  const [concept, setConcept] = useState("");
  const [publicText, setPublicText] = useState("");
  const [secretLore, setSecretLore] = useState("");
  const [voiceAndTone, setVoiceAndTone] = useState("");
  const [personalityTraits, setPersonalityTraits] = useState("");
  const [locationType, setLocationType] = useState("ciudad");
  const [ambientTone, setAmbientTone] = useState("");
  const [playerUserId, setPlayerUserId] = useState(members.find((m) => m.role === "PLAYER")?.user_id ?? "");

  const mutation = useCreateEntityMutation(campaignId);
  const apiError = mutation.error instanceof ApiError ? mutation.error.message : null;

  function resetForm() {
    setName("");
    setConcept("");
    setPublicText("");
    setSecretLore("");
    setVoiceAndTone("");
    setPersonalityTraits("");
    setAmbientTone("");
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;

    let document: Record<string, unknown>;
    if (entityType === "NPC") {
      document = buildNpcDocument({
        name,
        concept,
        publicDescription: publicText,
        secretLore,
        voiceAndTone,
        personalityTraits,
      });
    } else if (entityType === "LOCATION") {
      document = buildLocationDocument({
        name,
        locationType,
        publicDescription: publicText,
        secretLore,
        ambientTone,
      });
    } else {
      if (!playerUserId) return;
      document = buildPcDocument({
        name,
        concept,
        description: publicText,
        userId: playerUserId,
      });
    }

    mutation.mutate(
      { entity_type: entityType, document },
      { onSuccess: () => resetForm() },
    );
  }

  const players = members.filter((member) => member.role === "PLAYER");

  return (
    <Panel>
      <PanelHeader
        title="Nueva entidad del mundo"
        description="Añade un NPC, una ubicación o el PJ de un jugador."
      />
      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="form-field">
          <span>Tipo</span>
          <select value={entityType} onChange={(event) => setEntityType(event.target.value as EntityType)}>
            {CREATABLE_TYPES.map((type) => (
              <option key={type} value={type}>
                {type === "NPC" ? "Personaje no jugador (NPC)" : type === "LOCATION" ? "Ubicación" : "Personaje jugador (PC)"}
              </option>
            ))}
          </select>
        </label>

        <Input label="Nombre" value={name} onChange={(event) => setName(event.target.value)} required />

        {entityType !== "LOCATION" && (
          <Input label="Concepto" value={concept} onChange={(event) => setConcept(event.target.value)} />
        )}

        {entityType === "LOCATION" && (
          <>
            <Input
              label="Tipo de ubicación"
              value={locationType}
              onChange={(event) => setLocationType(event.target.value)}
            />
            <Input
              label="Tono ambiental"
              value={ambientTone}
              onChange={(event) => setAmbientTone(event.target.value)}
            />
          </>
        )}

        {entityType === "NPC" && (
          <>
            <Input
              label="Rasgos de personalidad (separados por coma)"
              value={personalityTraits}
              onChange={(event) => setPersonalityTraits(event.target.value)}
            />
            <Input
              label="Voz y tono"
              value={voiceAndTone}
              onChange={(event) => setVoiceAndTone(event.target.value)}
            />
          </>
        )}

        {entityType === "PC" && (
          <label className="form-field">
            <span>Jugador vinculado</span>
            <select value={playerUserId} onChange={(event) => setPlayerUserId(event.target.value)} required>
              <option value="">Selecciona jugador</option>
              {players.map((player) => (
                <option key={player.user_id} value={player.user_id}>
                  {player.display_name} ({player.email})
                </option>
              ))}
            </select>
          </label>
        )}

        <label className="form-field">
          <span>{entityType === "PC" ? "Descripción pública del PJ" : "Descripción pública"}</span>
          <textarea
            value={publicText}
            onChange={(event) => setPublicText(event.target.value)}
            rows={3}
            required
          />
        </label>

        {entityType !== "PC" && (
          <label className="form-field">
            <span>Lore secreto (solo Máster)</span>
            <textarea
              value={secretLore}
              onChange={(event) => setSecretLore(event.target.value)}
              rows={3}
            />
          </label>
        )}

        {apiError && <ErrorBanner message={apiError} />}
        <Button type="submit" disabled={mutation.isPending || !name.trim() || (entityType === "PC" && !playerUserId)}>
          {mutation.isPending ? "Creando..." : "Crear entidad"}
        </Button>
      </form>
    </Panel>
  );
}
