import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Email no válido"),
  password: z.string().min(8, "Mínimo 8 caracteres"),
});

export const registerSchema = loginSchema.extend({
  displayName: z.string().min(2, "Mínimo 2 caracteres").max(100),
});

export const displayNameSchema = z
  .string()
  .trim()
  .min(2, "Mínimo 2 caracteres")
  .max(32, "Máximo 32 caracteres");

export const updateDisplayNameSchema = z.object({
  displayName: displayNameSchema,
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type RegisterFormValues = z.infer<typeof registerSchema>;
export type UpdateDisplayNameFormValues = z.infer<typeof updateDisplayNameSchema>;
