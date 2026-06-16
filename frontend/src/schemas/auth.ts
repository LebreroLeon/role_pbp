import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Email no válido"),
  password: z.string().min(8, "Mínimo 8 caracteres"),
});

export const registerSchema = loginSchema.extend({
  displayName: z.string().min(2, "Mínimo 2 caracteres").max(100),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type RegisterFormValues = z.infer<typeof registerSchema>;
