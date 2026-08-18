"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { useAsyncLoad } from "@/hooks/useAsyncLoad";
import { ApiClientError } from "@/services/api-client";
import {
  getMe,
  isSignedOut,
  listNotifications,
  loginAccount,
  logoutAccount,
  markAllNotificationsRead,
  markNotificationRead,
  type AccountProfile,
  type WorkspaceNotification,
  updateMe,
} from "@/services/account-service";

interface SessionContextValue {
  user: AccountProfile | null;
  notifications: WorkspaceNotification[];
  unreadCount: number;
  signedOut: boolean;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  saveProfile: (payload: Partial<AccountProfile>) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  markRead: (id: string) => Promise<void>;
  markAllRead: () => Promise<void>;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AccountProfile | null>(null);
  const [notifications, setNotifications] = useState<WorkspaceNotification[]>([]);
  const [signedOut, setSignedOut] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (isSignedOut()) {
      setSignedOut(true);
      setUser(null);
      setNotifications([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [me, notes] = await Promise.all([getMe(), listNotifications()]);
      setUser(me);
      setNotifications(notes);
      setSignedOut(false);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 401) {
        setSignedOut(true);
        setUser(null);
        setNotifications([]);
      } else {
        setError(err instanceof ApiClientError ? err.message : "Unable to load account");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useAsyncLoad(() => refresh(), [refresh]);

  const value = useMemo<SessionContextValue>(
    () => ({
      user,
      notifications,
      unreadCount: notifications.filter((item) => !item.read).length,
      signedOut,
      loading,
      error,
      refresh,
      saveProfile: async (payload) => {
        const next = await updateMe(payload);
        setUser(next);
      },
      login: async (email, password) => {
        await loginAccount(email, password);
        await refresh();
      },
      logout: async () => {
        await logoutAccount();
        setUser(null);
        setNotifications([]);
        setSignedOut(true);
      },
      markRead: async (id) => {
        const updated = await markNotificationRead(id);
        setNotifications((current) => current.map((item) => (item.id === id ? updated : item)));
      },
      markAllRead: async () => {
        await markAllNotificationsRead();
        setNotifications((current) => current.map((item) => ({ ...item, read: true })));
      },
    }),
    [user, notifications, signedOut, loading, error, refresh],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
