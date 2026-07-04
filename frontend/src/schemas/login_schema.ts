/**
 * Validation schema for the login form.
 *
 * Password has no minimum-length check here - the server is the
 * source of truth for password correctness, so login only verifies
 * that both fields were filled in with a plausible email format.
 * remember_me controls whether the session survives a page reload.
 */
import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
  remember_me: z.boolean().optional().default(false),
});

export type LoginFormInput = z.input<typeof loginSchema>;
export type LoginFormValues = z.output<typeof loginSchema>;