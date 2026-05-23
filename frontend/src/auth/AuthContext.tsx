import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { API_BASE } from '../api/config';
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from './authStorage';

export interface AuthUser {
  id: number;
  username: string;
  display_name: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
  user: AuthUser;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function fetchMe(token: string): Promise<AuthUser> {
  const res = await fetch(`${API_BASE}/auth/me/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<AuthUser>;
}

async function refreshAccessToken(refresh: string): Promise<string> {
  const res = await fetch(`${API_BASE}/auth/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = (await res.json()) as { access: string };
  saveTokens({ access: data.access, refresh });
  return data.access;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      const access = getAccessToken();
      const refresh = getRefreshToken();
      if (!access && !refresh) {
        if (!cancelled) setLoading(false);
        return;
      }

      try {
        let token = access;
        if (token) {
          const me = await fetchMe(token);
          if (!cancelled) setUser(me);
          return;
        }
      } catch {
        // fall through to refresh
      }

      if (refresh) {
        try {
          const newAccess = await refreshAccessToken(refresh);
          const me = await fetchMe(newAccess);
          if (!cancelled) setUser(me);
          return;
        } catch {
          clearTokens();
        }
      }

      if (!cancelled) setUser(null);
    }

    restoreSession().finally(() => {
      if (!cancelled) setLoading(false);
    });

    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      throw new Error('invalid_credentials');
    }

    const data = (await res.json()) as LoginResponse;
    saveTokens({ access: data.access, refresh: data.refresh });
    setUser(data.user);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      loading,
      login,
      logout,
    }),
    [user, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export function handleUnauthorized(): void {
  clearTokens();
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}
