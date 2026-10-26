import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import useApi from '../hooks/useApi';
import { api } from '../services/api';

const STORAGE_KEY = 'devflow-user';

const SessionContext = createContext(null);

function readStoredUser() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (stored?.name) return stored;
  } catch {
    /* storage unavailable or corrupted */
  }
  return null;
}

/** "Alex Vance" → "AV"; falls back to the first letter of a single word. */
export function initialsFor(name) {
  const words = name.trim().split(/\s+/).filter(Boolean);
  const letters = words.length > 1 ? words[0][0] + words[words.length - 1][0] : (words[0]?.[0] ?? '');
  return letters.toUpperCase();
}

/** "jane.doe@acme.corp" → "Jane Doe" */
function nameFromEmail(email) {
  return email
    .split('@')[0]
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(' ');
}

/**
 * Shares the signed-in user (or null for guests) and the active workspace app-wide.
 * The prototype has no real auth: the signed-in user is persisted in localStorage.
 */
export function SessionProvider({ children }) {
  const state = useApi(api.getSession);
  const [user, setUser] = useState(readStoredUser);

  useEffect(() => {
    try {
      if (user) localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
      else localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
  }, [user]);

  const demoUser = state.data?.user ?? null;

  /** Sign in with an email; the demo account keeps its profile, other emails get a derived name. */
  const signIn = useCallback(
    ({ email }) => {
      const name = demoUser && demoUser.email === email ? demoUser.name : nameFromEmail(email) || email;
      setUser({ name, email, initials: initialsFor(name) });
    },
    [demoUser],
  );

  const signUp = useCallback(({ name, email }) => {
    setUser({ name, email, initials: initialsFor(name) });
  }, []);

  const signOut = useCallback(() => setUser(null), []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      workspace: state.data?.workspace ?? null,
      loading: state.loading,
      error: state.error,
      signIn,
      signUp,
      signOut,
    }),
    [user, state.data, state.loading, state.error, signIn, signUp, signOut],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) throw new Error('useSession must be used inside <SessionProvider>');
  return context;
}
