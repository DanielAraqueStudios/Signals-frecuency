import { API_GATEWAY_URL } from "./config";
import {
  getAccessToken,
  getRefreshToken,
  saveTokens,
  clearTokens,
} from "./tokenStore";
import { refresh as refreshTokens } from "./auth";

// Fires when a 401 survives a refresh attempt, so the app-level auth
// context can drop the user back to the Login screen. Screens/api modules
// don't import AuthContext directly to avoid a circular dependency; the
// provider subscribes to this instead.
type SessionExpiredListener = () => void;
let sessionExpiredListener: SessionExpiredListener | null = null;
export function onSessionExpired(listener: SessionExpiredListener): void {
  sessionExpiredListener = listener;
}

// Serializes concurrent refresh attempts so two 401s in flight at once
// don't each call /refresh and race to persist tokens.
let refreshInFlight: Promise<string | null> | null = null;

async function performRefresh(): Promise<string | null> {
  const storedRefreshToken = await getRefreshToken();
  if (!storedRefreshToken) return null;
  try {
    const tokens = await refreshTokens(storedRefreshToken);
    await saveTokens({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
    });
    return tokens.access_token;
  } catch {
    return null;
  }
}

async function getFreshAccessToken(forceRefresh: boolean): Promise<string | null> {
  if (!forceRefresh) {
    const existing = await getAccessToken();
    if (existing) return existing;
  }
  if (!refreshInFlight) {
    refreshInFlight = performRefresh().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

export interface ApiRequestOptions {
  method?: string;
  headers?: Record<string, string>;
  body?: BodyInit;
  /** Skip attaching Authorization — for endpoints that don't need it. */
  skipAuth?: boolean;
}

/**
 * Fetch wrapper for API Gateway calls: attaches the bearer access token,
 * and on a 401 refreshes once via auth-service and retries the request
 * exactly once before giving up and signaling session expiry.
 */
export async function apiRequest(
  path: string,
  options: ApiRequestOptions = {}
): Promise<Response> {
  const { method = "GET", headers = {}, body, skipAuth = false } = options;

  const doFetch = async (accessToken: string | null): Promise<Response> => {
    const finalHeaders: Record<string, string> = { ...headers };
    if (!skipAuth && accessToken) {
      finalHeaders.Authorization = `Bearer ${accessToken}`;
    }
    return fetch(`${API_GATEWAY_URL}${path}`, {
      method,
      headers: finalHeaders,
      body,
    });
  };

  if (skipAuth) {
    return doFetch(null);
  }

  const accessToken = await getFreshAccessToken(false);
  const firstResponse = await doFetch(accessToken);
  if (firstResponse.status !== 401) {
    return firstResponse;
  }

  const refreshedToken = await getFreshAccessToken(true);
  if (!refreshedToken) {
    await clearTokens();
    sessionExpiredListener?.();
    return firstResponse;
  }

  const secondResponse = await doFetch(refreshedToken);
  if (secondResponse.status === 401) {
    await clearTokens();
    sessionExpiredListener?.();
  }
  return secondResponse;
}
