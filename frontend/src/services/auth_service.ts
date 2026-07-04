/**
 * Auth API service.
 *
 * Single source of truth for all /auth network calls. Both the auth
 * store and the login/register pages call into these functions rather
 * than hitting axios directly, so token response shapes and error
 * parsing stay defined in one place.
 */
import { AxiosError } from "axios";
import { api } from "./api";
import type {
  AuthTokens,
  LoginRequest,
  RegisterRequest,
  RegisterResponse,
  User,
} from "../types";

export async function login(email: string, password: string): Promise<AuthTokens> {
  const payload: LoginRequest = { email, password };
  const { data } = await api.post<AuthTokens>("/auth/login", payload);
  return data;
}

// Backend returns a nested shape: { user, tokens }, not a flat object.
export async function register(payload: RegisterRequest): Promise<RegisterResponse> {
  const { data } = await api.post<RegisterResponse>("/auth/register", payload);
  return data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}

export async function refreshAccessToken(refresh_token: string): Promise<AuthTokens> {
  const { data } = await api.post<AuthTokens>("/auth/refresh", { refresh_token });
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

/**
 * Normalized shape for any error thrown by the functions above.
 * fieldErrors maps a form field name to its message, for 422 responses
 * FastAPI can map back to a specific input.
 */
export interface ParsedApiError {
  status: number | null;
  message: string;
  fieldErrors: Record<string, string>;
}

/**
 * Converts a raw Axios error into a ParsedApiError. Strips the
 * "Value error, " prefix FastAPI adds to custom Pydantic validator
 * messages, and applies sensible defaults for 429 and network errors.
 */
export function parseApiError(error: unknown): ParsedApiError {
  const fieldErrors: Record<string, string> = {};

  if (!(error instanceof AxiosError) || !error.response) {
    return {
      status: null,
      message: "Something went wrong. Please try again.",
      fieldErrors,
    };
  }

  const status = error.response.status;
  const data = error.response.data as { detail?: unknown; error?: string } | undefined;
  const detail = data?.detail;

  if (status === 422 && Array.isArray(detail)) {
    let generalMessage = "Please check the fields below and try again.";

    for (const err of detail) {
      const rawMsg: string = err.msg ?? "Invalid value";
      const msg = rawMsg.startsWith("Value error, ")
        ? rawMsg.slice("Value error, ".length)
        : rawMsg;

      const loc = Array.isArray(err.loc) ? err.loc : [];
      const field = loc.length > 0 ? loc[loc.length - 1] : undefined;

      if (typeof field === "string") {
        fieldErrors[field] = msg;
      } else {
        generalMessage = msg;
      }
    }

    return { status, message: generalMessage, fieldErrors };
  }

  if (status === 429) {
    return {
      status,
      message: "Too many attempts. Please wait a minute before trying again.",
      fieldErrors,
    };
  }

  if (typeof detail === "string") {
    return { status, message: detail, fieldErrors };
  }

  return {
    status,
    message: "Something went wrong. Please try again.",
    fieldErrors,
  };
}