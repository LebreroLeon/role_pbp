import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { formatHttpError } from "../../api/http";
import { LogIn } from "../../components/icons";
import { Button, ErrorBanner, Input, Panel, PanelHeader } from "../../components/ui";
import { useLoginMutation } from "../../hooks/mutations/useAuthMutations";
import { loginSchema, type LoginFormValues } from "../../schemas/auth";

export function LoginForm() {
  const mutation = useLoginMutation();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  const apiError = formatHttpError(mutation.error);

  return (
    <Panel>
      <PanelHeader
        icon={LogIn}
        iconTone="rose"
        title="Iniciar sesión"
        description="Accede a tus campañas de rol por turnos."
      />
      <form
        className="auth-form"
        onSubmit={handleSubmit((values) => mutation.mutate(values))}
      >
        <Input label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
        <Input
          label="Contraseña"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register("password")}
        />
        {apiError && <ErrorBanner message={apiError} />}
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Entrando..." : "Entrar"}
        </Button>
      </form>
      <p className="muted auth-footer">
        ¿No tienes cuenta? <Link to="/register">Regístrate</Link>
      </p>
    </Panel>
  );
}
