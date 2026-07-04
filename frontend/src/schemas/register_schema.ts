/**
 * Validation schema for the registration form.
 *
 * First and last name are collected as separate fields to match the
 * design, then joined into a single full_name string before the API
 * call, since the backend stores one combined field. Country is
 * required and must resolve to a 2-letter ISO code, matching the
 * server-side validator. Currency is optional and defaults to USD.
 */
import { z } from "zod";

const MADHAB_OPTIONS = ["hanafi", "shafi", "maliki", "hanbali", "jafari"] as const;
const CURRENCY_OPTIONS = ["USD", "SGD", "GBP", "EUR", "PKR", "MYR", "INR", "AED", "SAR"] as const;

export const registerSchema = z
  .object({
    first_name: z.string().min(1, "First name is required"),
    last_name: z.string().min(1, "Last name is required"),
    email: z.string().min(1, "Email is required").email("Enter a valid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Please confirm your password"),
    madhab: z.enum(MADHAB_OPTIONS).default("shafi"),
    location_country: z.string().length(2, "Select a country").toUpperCase(),
    currency: z.enum(CURRENCY_OPTIONS).default("USD"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type RegisterFormInput = z.input<typeof registerSchema>;
export type RegisterFormValues = z.output<typeof registerSchema>;