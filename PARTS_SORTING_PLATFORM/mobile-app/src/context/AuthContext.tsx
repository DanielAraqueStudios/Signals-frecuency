import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import * as authApi from "../api/auth";
import { onSessionExpired } from "../api/client";
import {
  saveTokens,
  clearTokens,
  getAccessToken,
} from "../api/tokenStore";

interface AuthContextValue {
  isLoggedIn: boolean;
  isLoading: boolean;
  email: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    // On cold start, treat a stored access token as "possibly logged in" —
    // client.ts will transparently refresh it on the first 401.
    getAccessToken()
      .then((token) => setIsLoggedIn(!!token))
      .finally(() => setIsLoading(false));

    onSessionExpired(() => {
      setIsLoggedIn(false);
      setEmail(null);
    });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isLoggedIn,
      isLoading,
      email,
      login: async (emailValue, password) => {
        const tokens = await authApi.login(emailValue, password);
        await saveTokens({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
        });
        setEmail(emailValue);
        setIsLoggedIn(true);
      },
      register: async (emailValue, password) => {
        await authApi.register(emailValue, password);
        // auth-service returns the created user, not a token yet — log
        // in right after, per the documented flow.
        const tokens = await authApi.login(emailValue, password);
        await saveTokens({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
        });
        setEmail(emailValue);
        setIsLoggedIn(true);
      },
      logout: async () => {
        await clearTokens();
        setIsLoggedIn(false);
        setEmail(null);
      },
    }),
    [isLoggedIn, isLoading, email]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
