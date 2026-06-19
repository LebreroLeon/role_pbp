import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { formatHttpError } from "../../api/http";
import { UserPlus } from "../../components/icons";
import { Button, ErrorBanner, Input, Panel, PanelHeader } from "../../components/ui";
import { useRegisterMutation } from "../../hooks/mutations/useAuthMutations";
import { registerSchema, type RegisterFormValues } from "../../schemas/auth";

export function RegisterForm() {
  const mutation = useRegisterMutation();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  const apiError = formatHttpError(mutation.error);

  return (
    <Panel>
      <PanelHeader
        icon={UserPlus}
        iconTone="violet"
        title="Crear cuenta"
        description="Regístrate para crear o unirte a campañas."
      />
      <form
        className="auth-form"
        onSubmit={handleSubmit((values) =>
          mutation.mutate({
            email: values.email,
            password: values.password,
            display_name: values.displayName,
          }),
        )}
      >
        <Input
          label="Nombre visible"
          autoComplete="name"
          error={errors.displayName?.message}
          {...register("displayName")}
        />
        <Input label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
        <Input
          label="Contraseña"
          type="password"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register("password")}
        />
        {apiError && <ErrorBanner message={apiError} />}
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Creando cuenta..." : "Registrarse"}
        </Button>
      </form>
      <p className="muted auth-footer">
        ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
      </p>
    </Panel>
  );
}
