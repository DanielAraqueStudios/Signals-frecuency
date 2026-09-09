import { AUTH_URL } from "./config";

// Shapes match auth-service's documented responses exactly
// (services/auth-service/README.md): register returns the created user
// (no token yet), login/refresh return an access+refresh JWT pair.

export interface AuthUser {
  id: string;
  email: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

async function parseJsonOrThrow(response: Response): Promise<any> {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      body?.detail ?? body?.message ?? `Request failed (${response.status})`;
    throw new Error(typeof message === "string" ? message : "Request failed");
  }
  return body;
}

export async function register(
  email: string,
  password: string
): Promise<AuthUser> {
  const response = await fetch(`${AUTH_URL}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseJsonOrThrow(response);
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const response = await fetch(`${AUTH_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseJsonOrThrow(response);
}

export async function refresh(refreshToken: string): Promise<TokenResponse> {
  const response = await fetch(`${AUTH_URL}/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  return parseJsonOrThrow(response);
}
