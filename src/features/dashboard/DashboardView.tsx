"use client";

import Link from "next/link";
import {
  aiRecommendations,
  campaignStatusMix,
  campaigns,
  contentAssets,
  contentPerformance,
  dashboardKpis,
  managedLinks,
  publishingActivity,
  recentPublishing,
} from "@/data/mock";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { BarChart, DoughnutChart, LineChart } from "@/components/ui/Charts";
import { formatCompact, formatCurrency, formatDate, formatNumber } from "@/lib/format";

export function DashboardView() {
  const kpis = [
    { label: "Total projects", value: formatNumber(dashboardKpis.totalProjects), icon: "bi-folder2", hint: "Workspace" },
    { label: "Content assets", value: formatNumber(dashboardKpis.totalContentAssets), icon: "bi-file-earmark-text" },
    { label: "Generated articles", value: formatNumber(dashboardKpis.generatedArticles), icon: "bi-stars" },
    { label: "Published assets", value: formatNumber(dashboardKpis.publishedAssets), icon: "bi-check2-circle" },
    { label: "Active campaigns", value: formatNumber(dashboardKpis.activeCampaigns), icon: "bi-flag" },
    { label: "Managed links", value: formatNumber(dashboardKpis.managedLinks), icon: "bi-link-45deg" },
    { label: "Indexed / monitored URLs", value: formatNumber(dashboardKpis.indexedUrls), icon: "bi-globe2" },
    { label: "Organic traffic", value: formatCompact(dashboardKpis.organicTraffic), icon: "bi-people" },
    { label: "Clicks", value: formatNumber(dashboardKpis.clicks), icon: "bi-cursor" },
    { label: "Conversions", value: formatNumber(dashboardKpis.conversions), icon: "bi-bullseye" },
    { label: "Revenue", value: formatCurrency(dashboardKpis.revenue), icon: "bi-currency-dollar" },
  ];

  return (
    <PageScaffold
      actions={
        <>
          <Link href="/create-content" className="btn btn-accent">
            Create content
          </Link>
          <Link href="/publishing" className="btn btn-ghost">
            Publishing center
          </Link>
        </>
      }
    >
      <div className="surface-card p-4 mb-4">
        <div className="row align-items-center g-3">
          <div className="col-lg-8">
            <div className="small text-uppercase text-muted fw-semibold mb-1">Featured workflow</div>
            <h2 className="section-title mb-2">Parasite SEO AI</h2>
            <p className="text-muted mb-0">
              Create AI-powered web content, optimize it for SEO, add media and contextual links, and generate a
              public web page.
            </p>
          </div>
          <div className="col-lg-4 text-lg-end">
            <Link href="/parasite-seo" className="btn btn-accent">
              Open Parasite SEO AI
            </Link>
          </div>
        </div>
      </div>

      <div className="row g-3 mb-4">
        {kpis.map((kpi) => (
          <div className="col-6 col-lg-4 col-xl-3 col-xxl-2" key={kpi.label}>
            <StatCard {...kpi} />
          </div>
        ))}
      </div>

      <div className="row g-3 mb-4">
        <div className="col-lg-6">
          <div className="surface-card p-3 h-100">
            <h2 className="section-title mb-3">Content performance</h2>
            <LineChart
              labels={contentPerformance.map((p) => p.label)}
              values={contentPerformance.map((p) => p.value)}
              label="Organic sessions"
            />
          </div>
        </div>
        <div className="col-lg-3">
          <div className="surface-card p-3 h-100">
            <h2 className="section-title mb-3">Publishing activity</h2>
            <BarChart
              labels={publishingActivity.map((p) => p.label)}
              values={publishingActivity.map((p) => p.value)}
              label="Publishes"
            />
          </div>
        </div>
        <div className="col-lg-3">
          <div className="surface-card p-3 h-100">
            <h2 className="section-title mb-3">Campaign status</h2>
            <DoughnutChart
              labels={campaignStatusMix.map((p) => p.label)}
              values={campaignStatusMix.map((p) => p.value)}
            />
          </div>
        </div>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-lg-6">
          <div className="surface-card h-100">
            <div className="p-3 border-bottom d-flex justify-content-between">
              <h2 className="section-title">Recent generated content</h2>
              <Link href="/content-studio" className="small">
                View studio
              </Link>
            </div>
            <div className="table-responsive">
              <table className="table table-clean">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {contentAssets.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <Link href={`/content-studio/${item.id}`}>{item.title}</Link>
                        <div className="small text-muted">{item.primaryKeyword}</div>
                      </td>
                      <td>
                        <StatusBadge value={item.status} />
                      </td>
                      <td className="text-muted">{formatDate(item.updatedAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div className="col-lg-6">
          <div className="surface-card h-100">
            <div className="p-3 border-bottom d-flex justify-content-between">
              <h2 className="section-title">Recent publishing activity</h2>
              <Link href="/published-assets" className="small">
                View assets
              </Link>
            </div>
            <div className="table-responsive">
              <table className="table table-clean">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Destination</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentPublishing.map((item) => (
                    <tr key={item.id}>
                      <td>{item.title}</td>
                      <td className="text-muted">{item.destination}</td>
                      <td>
                        <StatusBadge value={item.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div className="row g-3">
        <div className="col-lg-4">
          <div className="surface-card p-3 h-100">
            <h2 className="section-title mb-3">AI recommendations</h2>
            <div className="d-flex flex-column gap-3">
              {aiRecommendations.map((rec) => (
                <div key={rec.id} className="pb-3 border-bottom">
                  <div className="fw-semibold">{rec.title}</div>
                  <div className="small text-muted mt-1">{rec.detail}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="col-lg-4">
          <div className="surface-card p-3 h-100">
            <h2 className="section-title mb-3">Link status</h2>
            {managedLinks.map((link) => (
              <div key={link.id} className="d-flex justify-content-between gap-2 py-2 border-bottom">
                <div>
                  <div className="small">{link.anchorText}</div>
                  <div className="small text-muted">{link.attribute}</div>
                </div>
                <StatusBadge value={link.status} />
              </div>
            ))}
            <Link href="/links" className="small d-inline-block mt-3">
              Open link manager
            </Link>
          </div>
        </div>
        <div className="col-lg-4">
          <div className="surface-card p-3 h-100">
            <h2 className="section-title mb-3">Quick actions</h2>
            <div className="row g-2">
              {[
                { href: "/parasite-seo", icon: "bi-lightning-charge", label: "Parasite SEO AI" },
                { href: "/create-content", icon: "bi-plus-square", label: "New brief" },
                { href: "/campaigns", icon: "bi-flag", label: `Campaigns (${campaigns.length})` },
                { href: "/ai-agents", icon: "bi-cpu", label: "Agent monitor" },
              ].map((action) => (
                <div className="col-6" key={action.href}>
                  <Link href={action.href} className="quick-action">
                    <i className={`bi ${action.icon}`} />
                    <span>{action.label}</span>
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </PageScaffold>
  );
}
