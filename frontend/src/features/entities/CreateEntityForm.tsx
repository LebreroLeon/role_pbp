import { FormEvent, useState } from "react";

import type { CampaignMember } from "../../api/types";
import { ApiError } from "../../api/http";
import { MapPin } from "../../components/icons";
import { Button, ErrorBanner, Input, Panel, PanelHeader } from "../../components/ui";
import { hasSheetTemplate } from "../campaign/gameSystems";
import { useCreateEntityMutation } from "../../hooks/mutations/useEntityMutations";
import {
  buildFactionDocument,
  buildLocationDocument,
  buildNpcDocument,
  buildPcDocument,
  buildRelationshipDocument,
  ENTITY_TYPE_LABELS,
  type CampaignEntity,
  type EntityType,
  getEntityDisplayName,
} from "./entityDefaults";
import { buildNpcDocumentForGameSystem } from "./npcDocument";

const CREATABLE_TYPES: EntityType[] = ["NPC", "LOCATION", "PC", "FACTION", "RELATIONSHIP"];

type CreateEntityFormProps = {
  campaignId: string;
  members: CampaignMember[];
  entities?: CampaignEntity[];
  gameSystem?: string;
  onNpcCreated?: (entity: CampaignEntity) => void;
};

export function CreateEntityForm({
  campaignId,
  members,
  entities = [],
  gameSystem = "generic",
  onNpcCreated,
}: CreateEntityFormProps) {
  const [entityType, setEntityType] = useState<EntityType>("NPC");
  const [name, setName] = useState("");
  const [concept, setConcept] = useState("");
  const [publicText, setPublicText] = useState("");
  const [secretLore, setSecretLore] = useState("");
  const [voiceAndTone, setVoiceAndTone] = useState("");
  const [personalityTraits, setPersonalityTraits] = useState("");
  const [locationType, setLocationType] = useState("ciudad");
  const [ambientTone, setAmbientTone] = useState("");
  const [factionType, setFactionType] = useState("organización");
  const [goals, setGoals] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [bondType, setBondType] = useState("alianza");
  const [publicStatus, setPublicStatus] = useState("");
  const [secretNuance, setSecretNuance] = useState("");
  const [tensionLevel, setTensionLevel] = useState(3);
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
    if (entityType !== "RELATIONSHIP" && !name.trim()) return;
    if (entityType === "RELATIONSHIP" && (!sourceId || !targetId)) return;

    let document: Record<string, unknown>;
    if (entityType === "NPC") {
      document = hasSheetTemplate(gameSystem)
        ? buildNpcDocumentForGameSystem({
            name,
            concept,
            publicDescription: publicText,
            secretLore,
            voiceAndTone,
            personalityTraits,
            systemId: gameSystem,
          })
        : buildNpcDocument({
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
    } else if (entityType === "FACTION") {
      document = buildFactionDocument({
        name,
        factionType,
        publicDescription: publicText,
        secretLore,
        goals,
      });
    } else if (entityType === "RELATIONSHIP") {
      if (!sourceId || !targetId) return;
      document = buildRelationshipDocument({
        sourceId,
        targetId,
        bondType,
        publicStatus: publicStatus || publicText,
        secretNuance: secretNuance || secretLore,
        tensionLevel,
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
      {
        onSuccess: (created) => {
          resetForm();
          if (entityType === "NPC") {
            onNpcCreated?.(created);
          }
        },
      },
    );
  }

  const players = members.filter((member) => member.role === "PLAYER");

  const relationshipCandidates = entities.filter((entity) =>
    ["NPC", "PC", "FACTION", "LOCATION"].includes(entity.entity_type),
  );

  return (
    <Panel>
      <PanelHeader
        icon={MapPin}
        iconTone="teal"
        title="Nueva entidad del mundo"
        description="Añade un NPC, una ubicación o el PJ de un jugador."
      />
      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="form-field">
          <span>Tipo</span>
          <select value={entityType} onChange={(event) => setEntityType(event.target.value as EntityType)}>
            {CREATABLE_TYPES.map((type) => (
              <option key={type} value={type}>
                {ENTITY_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </label>

        <Input label="Nombre" value={name} onChange={(event) => setName(event.target.value)} required />

        {entityType === "FACTION" && (
          <>
            <Input
              label="Tipo de facción"
              value={factionType}
              onChange={(event) => setFactionType(event.target.value)}
            />
            <Input label="Objetivos (separados por coma)" value={goals} onChange={(event) => setGoals(event.target.value)} />
          </>
        )}

        {entityType === "RELATIONSHIP" && (
          <>
            <label className="form-field">
              <span>Entidad origen</span>
              <select value={sourceId} onChange={(event) => setSourceId(event.target.value)} required>
                <option value="">Selecciona origen</option>
                {relationshipCandidates.map((entity) => (
                  <option key={entity.id} value={entity.id}>
                    {getEntityDisplayName(entity)} ({entity.entity_type})
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>Entidad destino</span>
              <select value={targetId} onChange={(event) => setTargetId(event.target.value)} required>
                <option value="">Selecciona destino</option>
                {relationshipCandidates.map((entity) => (
                  <option key={entity.id} value={entity.id}>
                    {getEntityDisplayName(entity)} ({entity.entity_type})
                  </option>
                ))}
              </select>
            </label>
            <Input label="Tipo de vínculo" value={bondType} onChange={(event) => setBondType(event.target.value)} />
            <Input
              label="Estado público del vínculo"
              value={publicStatus}
              onChange={(event) => setPublicStatus(event.target.value)}
            />
            <Input
              label="Nivel de tensión (0-10)"
              type="number"
              min={0}
              max={10}
              value={tensionLevel}
              onChange={(event) => setTensionLevel(Number(event.target.value))}
            />
          </>
        )}

        {entityType !== "LOCATION" && entityType !== "RELATIONSHIP" && (
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

        {entityType !== "PC" && entityType !== "RELATIONSHIP" && (
          <label className="form-field">
            <span>Lore secreto (solo Máster)</span>
            <textarea
              value={secretLore}
              onChange={(event) => setSecretLore(event.target.value)}
              rows={3}
            />
          </label>
        )}

        {entityType === "RELATIONSHIP" && (
          <label className="form-field">
            <span>Matices secretos del vínculo</span>
            <textarea
              value={secretNuance}
              onChange={(event) => setSecretNuance(event.target.value)}
              rows={3}
            />
          </label>
        )}

        {apiError && <ErrorBanner message={apiError} />}
        <Button
          type="submit"
          disabled={
            mutation.isPending ||
            !name.trim() ||
            (entityType === "PC" && !playerUserId) ||
            (entityType === "RELATIONSHIP" && (!sourceId || !targetId))
          }
        >
          {mutation.isPending ? "Creando..." : "Crear entidad"}
        </Button>
      </form>
    </Panel>
  );
}
