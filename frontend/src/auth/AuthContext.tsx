import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { User } from '../types';

export const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';
const TOKEN_KEY = 'neurodetect_auth_token';

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  signIn: (token: string, user: User) => void;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) { setLoading(false); return; }
    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then(setUser)
      .catch(() => { localStorage.removeItem(TOKEN_KEY); setToken(null); setUser(null); })
      .finally(() => setLoading(false));
  }, [token]);

  const value = useMemo(() => ({
    user, token, loading,
    signIn: (nextToken: string, nextUser: User) => {
      localStorage.setItem(TOKEN_KEY, nextToken); setToken(nextToken); setUser(nextUser);
    },
    signOut: () => { localStorage.removeItem(TOKEN_KEY); setToken(null); setUser(null); },
  }), [user, token, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
