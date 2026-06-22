import { ChangeEvent, useRef, useState } from "react";

import { ApiError } from "../../api/http";
import { api } from "../../api/client";
import { Button, Input } from "../../components/ui";
import { useUploadEntityIllustrationMutation } from "../../hooks/mutations/useEntityIllustrationMutations";
import type { CampaignEntity } from "./entityDefaults";
import { EntityIllustrationImage } from "./EntityIllustrationImage";

const ACCEPTED_TYPES = "image/jpeg,image/png,image/webp";

type EntityIllustrationFieldProps = {
  campaignId: string;
  entity: CampaignEntity;
  entityName: string;
  illustrationUrl: string;
  onIllustrationUrlChange: (value: string) => void;
  disabled?: boolean;
};

function readIllustrationUrlFromEntity(entity: CampaignEntity): string {
  const document = entity.document;
  if (entity.entity_type === "PC") {
    return (document.public_profile as { illustration_url?: string } | undefined)?.illustration_url ?? "";
  }
  if (entity.entity_type === "NPC") {
    return (document.ai_narrative_profile as { illustration_url?: string } | undefined)?.illustration_url ?? "";
  }
  if (entity.entity_type === "LOCATION" || entity.entity_type === "FACTION") {
    return (document.narrative_profile as { illustration_url?: string } | undefined)?.illustration_url ?? "";
  }
  if (entity.entity_type === "RELATIONSHIP") {
    return (document.narrative_bond as { illustration_url?: string } | undefined)?.illustration_url ?? "";
  }
  return "";
}

export function EntityIllustrationField({
  campaignId,
  entity,
  entityName,
  illustrationUrl,
  onIllustrationUrlChange,
  disabled = false,
}: EntityIllustrationFieldProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadEntityIllustrationMutation(campaignId);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setUploadError(null);
    try {
      const updated = await uploadMutation.mutateAsync({ entityId: entity.id, file });
      onIllustrationUrlChange(readIllustrationUrlFromEntity(updated));
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "No se pudo subir la imagen");
    }
  }

  async function handleClear() {
    setUploadError(null);
    if (illustrationUrl.endsWith("/illustration")) {
      try {
        await api.removeEntityIllustration(entity.id);
      } catch (err) {
        setUploadError(err instanceof ApiError ? err.message : "No se pudo quitar la imagen");
        return;
      }
    }
    onIllustrationUrlChange("");
  }

  return (
    <div className="form-field entity-illustration-field">
      <span>Ilustración de entidad</span>
      <p className="muted entity-illustration-field__hint">
        Imagen completa para la ficha (distinta del avatar de chat). JPG, PNG o WebP.
      </p>
      <div className="entity-illustration-field__row">
        {illustrationUrl ? (
          <div className="entity-illustration-field__preview">
            <EntityIllustrationImage
              illustrationUrl={illustrationUrl}
              alt={`Ilustración de ${entityName}`}
              className="entity-illustration-field__preview-image"
            />
          </div>
        ) : (
          <div className="entity-illustration-field__placeholder muted">Sin ilustración</div>
        )}
        <div className="entity-illustration-field__controls">
          <Input
            label="URL de imagen (opcional)"
            value={illustrationUrl}
            onChange={(event) => onIllustrationUrlChange(event.target.value)}
            placeholder="https://… o sube un archivo"
            disabled={disabled || uploadMutation.isPending}
          />
          <div className="entity-illustration-field__actions">
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_TYPES}
              hidden
              onChange={handleFileChange}
              disabled={disabled || uploadMutation.isPending}
            />
            <Button
              type="button"
              variant="secondary"
              disabled={disabled || uploadMutation.isPending}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploadMutation.isPending ? "Subiendo…" : "Subir ilustración"}
            </Button>
            {illustrationUrl && (
              <Button
                type="button"
                variant="secondary"
                disabled={disabled || uploadMutation.isPending}
                onClick={() => void handleClear()}
              >
                Quitar
              </Button>
            )}
          </div>
          {uploadError && <small className="error">{uploadError}</small>}
        </div>
      </div>
    </div>
  );
}
