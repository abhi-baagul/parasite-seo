import { apiGetData, apiMutateData } from "@/services/api-client";

export type NotificationPrefs = {
  publishing: boolean;
  generation: boolean;
  campaign: boolean;
  agent: boolean;
};

export type AccountProfile = {
  id: string;
  email: string;
  name: string;
  is_verified: boolean;
  timezone: string;
  organization: string;
  job_title: string;
  website: string;
  bio: string;
  role: string;
  notification_prefs: NotificationPrefs;
};

export type WorkspaceNotification = {
  id: string;
  kind: string;
  title: string;
  body: string;
  href: string | null;
  read: boolean;
  at: string | null;
  source_key: string;
};

const TOKEN_KEY = "ps_access_token";
const SIGNED_OUT_KEY = "ps_signed_out";

export function getStoredAccessToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function isSignedOut() {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(SIGNED_OUT_KEY) === "1";
}

export function setSignedOut(value: boolean) {
  if (typeof window === "undefined") return;
  if (value) window.localStorage.setItem(SIGNED_OUT_KEY, "1");
  else window.localStorage.removeItem(SIGNED_OUT_KEY);
}

export function storeAccessToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export async function loginAccount(email: string, password: string) {
  const data = await apiMutateData<{
    access_token: string;
    refresh_token: string;
    user: AccountProfile;
  }>("/api/v1/auth/login", "POST", { email, password });
  storeAccessToken(data.access_token);
  setSignedOut(false);
  return data;
}

export async function logoutAccount() {
  try {
    await apiMutateData<{ signed_out: boolean }>("/api/v1/auth/logout", "POST");
  } catch {
    // still clear the local session
  }
  storeAccessToken(null);
  setSignedOut(true);
}

export async function getMe() {
  return apiGetData<AccountProfile>("/api/v1/me");
}

export async function updateMe(payload: Partial<AccountProfile> & { notification_prefs?: Partial<NotificationPrefs> }) {
  return apiMutateData<AccountProfile>("/api/v1/me", "PATCH", payload);
}

export async function changePassword(current_password: string, new_password: string) {
  return apiMutateData<{ updated: boolean }>("/api/v1/me/password", "POST", {
    current_password,
    new_password,
  });
}

export async function listNotifications() {
  return apiGetData<WorkspaceNotification[]>("/api/v1/me/notifications");
}

export async function markNotificationRead(id: string) {
  return apiMutateData<WorkspaceNotification>(`/api/v1/me/notifications/${id}/read`, "POST");
}

export async function markAllNotificationsRead() {
  return apiMutateData<{ updated: number }>("/api/v1/me/notifications/read-all", "POST");
}
