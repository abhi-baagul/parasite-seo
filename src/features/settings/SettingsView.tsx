"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useSession } from "@/context/SessionContext";
import { useProject } from "@/context/ProjectContext";
import { ApiClientError } from "@/services/api-client";
import { changePassword, type NotificationPrefs } from "@/services/account-service";
import { listPublishingChannels } from "@/services/publishing-service";
import type { PublishingChannelDto } from "@/services/types";

const tabs = [
  "profile",
  "notifications",
  "security",
  "ai-provider",
  "publishing-channels",
  "storage",
] as const;

type Tab = (typeof tabs)[number];

export function SettingsView() {
  const search = useSearchParams();
  const { user, saveProfile, logout, error: sessionError } = useSession();
  const { selectedId } = useProject();
  const initialTab = (search.get("tab") as Tab | null) ?? "profile";
  const [tab, setTab] = useState<Tab>(tabs.includes(initialTab) ? initialTab : "profile");
  const [form, setForm] = useState({
    name: "",
    email: "",
    organization: "",
    job_title: "",
    timezone: "Asia/Kolkata",
    website: "",
    bio: "",
  });
  const [prefs, setPrefs] = useState<NotificationPrefs>({
    publishing: true,
    generation: true,
    campaign: true,
    agent: true,
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [channels, setChannels] = useState<PublishingChannelDto[]>([]);

  useEffect(() => {
    if (!user) return;
    setForm({
      name: user.name,
      email: user.email,
      organization: user.organization,
      job_title: user.job_title,
      timezone: user.timezone,
      website: user.website,
      bio: user.bio,
    });
    setPrefs(user.notification_prefs);
  }, [user]);

  useEffect(() => {
    void listPublishingChannels(selectedId === "all" ? undefined : selectedId)
      .then((result) => setChannels(result.items))
      .catch(() => setChannels([]));
  }, [selectedId]);

  async function onSaveProfile(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await saveProfile(form);
      setMessage("Profile saved.");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to save profile");
    } finally {
      setSaving(false);
    }
  }

  async function onSavePrefs(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await saveProfile({ notification_prefs: prefs });
      setMessage("Notification preferences saved.");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to save preferences");
    } finally {
      setSaving(false);
    }
  }

  async function onChangePassword(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setMessage("Password updated.");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to update password");
    } finally {
      setSaving(false);
    }
  }

  return (
    <PageScaffold>
      <div className="row g-3">
        <div className="col-lg-3">
          <nav className="surface-card p-2 settings-nav">
            {tabs.map((item) => (
              <button
                key={item}
                type="button"
                className={`nav-link w-100 text-start ${tab === item ? "active" : ""}`}
                onClick={() => setTab(item)}
              >
                {label(item)}
              </button>
            ))}
          </nav>
        </div>
        <div className="col-lg-9">
          <div className="surface-card p-4">
            {sessionError || error ? <div className="alert alert-danger py-2">{error || sessionError}</div> : null}
            {message ? <div className="alert alert-success py-2">{message}</div> : null}

            {tab === "profile" && (
              <form onSubmit={onSaveProfile}>
                <h2 className="h5 mb-3">Profile</h2>
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="profile-name">
                      Name
                    </label>
                    <input
                      id="profile-name"
                      className="form-control"
                      value={form.name}
                      onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                      required
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="profile-email">
                      Email
                    </label>
                    <input
                      id="profile-email"
                      className="form-control"
                      type="email"
                      value={form.email}
                      onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                      required
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="profile-org">
                      Organization
                    </label>
                    <input
                      id="profile-org"
                      className="form-control"
                      value={form.organization}
                      onChange={(event) => setForm((current) => ({ ...current, organization: event.target.value }))}
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="profile-title">
                      Job title
                    </label>
                    <input
                      id="profile-title"
                      className="form-control"
                      value={form.job_title}
                      onChange={(event) => setForm((current) => ({ ...current, job_title: event.target.value }))}
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="profile-tz">
                      Timezone
                    </label>
                    <select
                      id="profile-tz"
                      className="form-select"
                      value={form.timezone}
                      onChange={(event) => setForm((current) => ({ ...current, timezone: event.target.value }))}
                    >
                      <option value="Asia/Kolkata">Asia/Kolkata</option>
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">America/New_York</option>
                      <option value="America/Los_Angeles">America/Los_Angeles</option>
                      <option value="Europe/London">Europe/London</option>
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label className="form-label" htmlFor="profile-web">
                      Website
                    </label>
                    <input
                      id="profile-web"
                      className="form-control"
                      value={form.website}
                      onChange={(event) => setForm((current) => ({ ...current, website: event.target.value }))}
                    />
                  </div>
                  <div className="col-12">
                    <label className="form-label" htmlFor="profile-bio">
                      Bio
                    </label>
                    <textarea
                      id="profile-bio"
                      className="form-control"
                      rows={3}
                      value={form.bio}
                      onChange={(event) => setForm((current) => ({ ...current, bio: event.target.value }))}
                    />
                  </div>
                </div>
                <div className="d-flex flex-wrap gap-2 mt-3">
                  <button className="btn btn-accent" type="submit" disabled={saving}>
                    {saving ? "Saving…" : "Save profile"}
                  </button>
                  <button
                    className="btn btn-ghost"
                    type="button"
                    onClick={() => {
                      if (!window.confirm("Sign out of this workspace?")) return;
                      void logout();
                    }}
                  >
                    Log out
                  </button>
                </div>
              </form>
            )}

            {tab === "notifications" && (
              <form onSubmit={onSavePrefs}>
                <h2 className="h5 mb-3">Notifications</h2>
                <p className="text-muted small">These control which workspace events appear in the bell menu.</p>
                {(
                  [
                    ["publishing", "Publishing and live public pages"],
                    ["generation", "Content generation updates"],
                    ["campaign", "Backlink campaigns that need action"],
                    ["agent", "Failed generations and agent errors"],
                  ] as const
                ).map(([key, caption]) => (
                  <div className="form-check mb-2" key={key}>
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id={`pref-${key}`}
                      checked={prefs[key]}
                      onChange={(event) => setPrefs((current) => ({ ...current, [key]: event.target.checked }))}
                    />
                    <label className="form-check-label" htmlFor={`pref-${key}`}>
                      {caption}
                    </label>
                  </div>
                ))}
                <button className="btn btn-accent mt-3" type="submit" disabled={saving}>
                  Save preferences
                </button>
              </form>
            )}

            {tab === "security" && (
              <form onSubmit={onChangePassword}>
                <h2 className="h5 mb-3">Security</h2>
                <div className="mb-3">
                  <label className="form-label" htmlFor="current-password">
                    Current password
                  </label>
                  <input
                    id="current-password"
                    className="form-control"
                    type="password"
                    value={currentPassword}
                    onChange={(event) => setCurrentPassword(event.target.value)}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label" htmlFor="new-password">
                    New password
                  </label>
                  <input
                    id="new-password"
                    className="form-control"
                    type="password"
                    minLength={8}
                    value={newPassword}
                    onChange={(event) => setNewPassword(event.target.value)}
                    required
                  />
                </div>
                <button className="btn btn-accent" type="submit" disabled={saving}>
                  Update password
                </button>
              </form>
            )}

            {tab === "ai-provider" && (
              <div>
                <h2 className="h5 mb-3">AI provider</h2>
                <p className="text-muted">
                  OpenRouter is configured on the backend with <code>OPENROUTER_API_KEY</code>. The default model is set
                  by <code>DEFAULT_AI_MODEL</code>.
                </p>
              </div>
            )}

            {tab === "publishing-channels" && (
              <div>
                <h2 className="h5 mb-3">Publishing channels</h2>
                {channels.length === 0 ? (
                  <p className="text-muted mb-0">No channels yet. Add them from Publishing.</p>
                ) : (
                  channels.map((channel) => (
                    <div key={channel.id} className="d-flex justify-content-between py-2 border-bottom">
                      <div>
                        <div>{channel.name}</div>
                        <div className="small text-muted">{channel.channel_type}</div>
                      </div>
                      <StatusBadge value={channel.is_active ? "active" : "inactive"} />
                    </div>
                  ))
                )}
              </div>
            )}

            {tab === "storage" && (
              <div>
                <h2 className="h5 mb-3">Storage</h2>
                <p className="text-muted mb-0">
                  Uploads currently use local disk on the API host. Configure S3 later with <code>AWS_S3_BUCKET</code>.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </PageScaffold>
  );
}

function label(tab: Tab) {
  return tab.split("-").join(" ").replace(/\b\w/g, (c) => c.toUpperCase());
}
