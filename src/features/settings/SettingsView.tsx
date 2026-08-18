"use client";

import { useState } from "react";
import { publishingChannels, userProfile } from "@/data/mock";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { StatusBadge } from "@/components/ui/StatusBadge";

const tabs = [
  "profile",
  "ai-provider",
  "api-keys",
  "publishing-channels",
  "seo-providers",
  "storage",
  "affiliate",
  "notifications",
  "security",
] as const;

type Tab = (typeof tabs)[number];

export function SettingsView() {
  const [tab, setTab] = useState<Tab>("profile");

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
            {tab === "profile" && (
              <Section title="Profile">
                <Field label="Name" value={userProfile.name} />
                <Field label="Email" value={userProfile.email} />
                <Field label="Role" value={userProfile.role} />
                <Field label="Organization" value={userProfile.organization} />
                <Field label="Timezone" value={userProfile.timezone} />
              </Section>
            )}
            {tab === "ai-provider" && (
              <Section title="AI provider">
                <Field label="Default model" value="Workspace-managed (not connected in this phase)" />
                <Field label="Fallback" value="Disabled until a provider key is added" />
                <p className="small text-muted mb-0">Provider calls are out of scope for the frontend prototype.</p>
              </Section>
            )}
            {tab === "api-keys" && (
              <Section title="API keys">
                <p className="small text-muted">
                  Keys are stored locally in this mock UI and are never sent anywhere. Replace this panel with a secrets
                  vault in a later phase.
                </p>
                <Field label="OpenAI" value="sk-••••••••••••••••" />
                <Field label="Anthropic" value="Not set" />
              </Section>
            )}
            {tab === "publishing-channels" && (
              <Section title="Publishing channels">
                {publishingChannels.map((channel) => (
                  <div key={channel.id} className="d-flex justify-content-between py-2 border-bottom">
                    <div>
                      <div>{channel.name}</div>
                      <div className="small text-muted">{channel.account}</div>
                    </div>
                    <StatusBadge value={channel.authorized ? "active" : "inactive"} />
                  </div>
                ))}
              </Section>
            )}
            {tab === "seo-providers" && (
              <Section title="SEO providers">
                <Field label="Search Console" value="Connected (read-only mock)" />
                <Field label="Rank source" value="Manual / third-party placeholder" />
              </Section>
            )}
            {tab === "storage" && (
              <Section title="Storage">
                <Field label="Asset bucket" value="workspace-media (mock)" />
                <Field label="Export formats" value="PDF, HTML, Markdown" />
              </Section>
            )}
            {tab === "affiliate" && (
              <Section title="Affiliate configuration">
                <Field label="Default attribute" value="sponsored" />
                <Field label="Allowed domains" value="partners.energyreview.co, workstack.io, pawcover.com" />
                <p className="small text-muted mb-0">
                  Affiliate links are only applied to authorized content destinations.
                </p>
              </Section>
            )}
            {tab === "notifications" && (
              <Section title="Notifications">
                <div className="form-check mb-2">
                  <input className="form-check-input" type="checkbox" id="pub" defaultChecked />
                  <label className="form-check-label" htmlFor="pub">
                    Publishing failures
                  </label>
                </div>
                <div className="form-check mb-2">
                  <input className="form-check-input" type="checkbox" id="rank" defaultChecked />
                  <label className="form-check-label" htmlFor="rank">
                    Rank drops greater than 3 positions
                  </label>
                </div>
                <div className="form-check">
                  <input className="form-check-input" type="checkbox" id="agent" defaultChecked />
                  <label className="form-check-label" htmlFor="agent">
                    Agent errors
                  </label>
                </div>
              </Section>
            )}
            {tab === "security" && (
              <Section title="Security">
                <Field label="SSO" value="Not configured" />
                <Field label="2FA" value="Recommended before production" />
                <Field label="Session" value="Local prototype — no auth backend" />
              </Section>
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

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="h5 mb-3">{title}</h2>
      {children}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="mb-3">
      <label className="form-label">{label}</label>
      <input className="form-control" defaultValue={value} />
    </div>
  );
}
