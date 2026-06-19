import { ChangeEvent, useRef, useState } from "react";

import { ApiError } from "../../api/http";
import { api } from "../../api/client";
import { Button, Input } from "../../components/ui";
import { useUploadEntityAvatarMutation } from "../../hooks/mutations/useEntityAvatarMutations";
import { ChatAvatar } from "../scene/ChatAvatar";

const ACCEPTED_TYPES = "image/jpeg,image/png,image/webp";

type EntityAvatarFieldProps = {
  campaignId: string;
  entityId: string;
  entityName: string;
  avatarUrl: string;
  onAvatarUrlChange: (value: string) => void;
  disabled?: boolean;
};

export function EntityAvatarField({
  campaignId,
  entityId,
  entityName,
  avatarUrl,
  onAvatarUrlChange,
  disabled = false,
}: EntityAvatarFieldProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadEntityAvatarMutation(campaignId);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setUploadError(null);
    try {
      const updated = await uploadMutation.mutateAsync({ entityId, file });
      const profile =
        updated.entity_type === "PC"
          ? (updated.document.public_profile as { avatar_url?: string } | undefined)
          : (updated.document.ai_narrative_profile as { avatar_url?: string } | undefined);
      onAvatarUrlChange(profile?.avatar_url ?? "");
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "No se pudo subir la imagen");
    }
  }

  async function handleClear() {
    setUploadError(null);
    if (avatarUrl.endsWith("/avatar")) {
      try {
        await api.removeEntityAvatar(entityId);
      } catch (err) {
        setUploadError(err instanceof ApiError ? err.message : "No se pudo quitar la imagen");
        return;
      }
    }
    onAvatarUrlChange("");
  }

  return (
    <div className="form-field entity-avatar-field">
      <span>Imagen de avatar</span>
      <div className="entity-avatar-field__row">
        <ChatAvatar name={entityName || "??"} avatarUrl={avatarUrl || undefined} />
        <div className="entity-avatar-field__controls">
          <Input
            label="URL de imagen (opcional)"
            value={avatarUrl}
            onChange={(event) => onAvatarUrlChange(event.target.value)}
            placeholder="https://… o sube un archivo"
            disabled={disabled || uploadMutation.isPending}
          />
          <div className="entity-avatar-field__actions">
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
              {uploadMutation.isPending ? "Subiendo…" : "Subir imagen"}
            </Button>
            {avatarUrl && (
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
          <p className="muted entity-avatar-field__hint">JPG, PNG o WebP. También puedes pegar una URL externa.</p>
          {uploadError && <small className="error">{uploadError}</small>}
        </div>
      </div>
    </div>
  );
}
