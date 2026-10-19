import { createContext, useContext } from 'react';
import useApi from '../hooks/useApi';
import { api } from '../services/api';

const SessionContext = createContext(null);

/** Loads the signed-in user + active workspace once and shares it app-wide. */
export function SessionProvider({ children }) {
  const state = useApi(api.getSession);
  return <SessionContext.Provider value={state}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) throw new Error('useSession must be used inside <SessionProvider>');
  return {
    user: context.data?.user ?? null,
    workspace: context.data?.workspace ?? null,
    loading: context.loading,
    error: context.error,
  };
}
