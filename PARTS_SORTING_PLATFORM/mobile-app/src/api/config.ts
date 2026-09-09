import Constants from "expo-constants";

interface AppExtra {
  apiGatewayUrl?: string;
  authUrl?: string;
}

const extra = (Constants.expoConfig?.extra ?? {}) as AppExtra;

// Falls back to the same localhost placeholders as app.config.ts in case
// `extra` isn't populated (e.g. certain test runners).
export const API_GATEWAY_URL = extra.apiGatewayUrl ?? "http://localhost:8000";
export const AUTH_URL = extra.authUrl ?? "http://localhost:8001";
