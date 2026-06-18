import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { ApiError } from "../../api/http";
import { Button, ErrorBanner, Input, Modal } from "../../components/ui";
import { useUpdateDisplayNameMutation } from "../../hooks/mutations/useAuthMutations";
import { updateDisplayNameSchema, type UpdateDisplayNameFormValues } from "../../schemas/auth";

type PlayerNameModalProps = {
  currentName: string;
  onClose: () => void;
};

export function PlayerNameModal({ currentName, onClose }: PlayerNameModalProps) {
  const mutation = useUpdateDisplayNameMutation();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UpdateDisplayNameFormValues>({
    resolver: zodResolver(updateDisplayNameSchema),
    defaultValues: { displayName: currentName },
  });

  const apiError = mutation.error instanceof ApiError ? mutation.error.message : null;

  return (
    <Modal
      title="Cambiar nombre visible"
      titleId="player-name-modal-title"
      onClose={onClose}
      size="md"
      bodyClassName="ui-modal__body--form"
      footer={
        <div className="ui-modal__actions">
          <Button type="button" variant="secondary" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="submit" form="player-name-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Guardando…" : "Guardar"}
          </Button>
        </div>
      }
    >
      <form
        id="player-name-form"
        onSubmit={handleSubmit((values) =>
          mutation.mutate(values.displayName.trim(), {
            onSuccess: () => onClose(),
          }),
        )}
      >
        <p className="muted">Este nombre aparece en el chat, turnos y listas de jugadores.</p>
        <Input
          label="Nombre visible"
          autoComplete="nickname"
          autoFocus
          error={errors.displayName?.message}
          {...register("displayName")}
        />
        {apiError && <ErrorBanner message={apiError} />}
      </form>
    </Modal>
  );
}
