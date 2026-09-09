import * as SecureStore from "expo-secure-store";

// Tokens are auth secrets, not app preferences — expo-secure-store backs
// onto Keychain (iOS) / Keystore-backed EncryptedSharedPreferences
// (Android), unlike AsyncStorage which is plain unencrypted disk.
const ACCESS_TOKEN_KEY = "parts_sorting_access_token";
const REFRESH_TOKEN_KEY = "parts_sorting_refresh_token";

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
}

export async function saveTokens(tokens: TokenPair): Promise<void> {
  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, tokens.accessToken);
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refreshToken);
}

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

export async function clearTokens(): Promise<void> {
  await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
}
