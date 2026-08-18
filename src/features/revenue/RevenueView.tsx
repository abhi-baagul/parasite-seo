"use client";

import { expenseTrend, revenueStreams, revenueSummary } from "@/data/mock";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { StatCard } from "@/components/ui/StatCard";
import { BarChart } from "@/components/ui/Charts";
import { formatCurrency, formatNumber } from "@/lib/format";

export function RevenueView() {
  return (
    <PageScaffold>
      <div className="row g-3 mb-4">
        <div className="col-6 col-lg-2">
          <StatCard label="Affiliate clicks" value={formatNumber(revenueSummary.affiliateClicks)} icon="bi-box-arrow-up-right" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="Conversions" value={formatNumber(revenueSummary.conversions)} icon="bi-bullseye" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="Revenue" value={formatCurrency(revenueSummary.revenue)} icon="bi-currency-dollar" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="Expenses" value={formatCurrency(revenueSummary.expenses)} icon="bi-receipt" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="Profit" value={formatCurrency(revenueSummary.profit)} icon="bi-graph-up-arrow" />
        </div>
        <div className="col-6 col-lg-2">
          <StatCard label="ROI" value={`${revenueSummary.roi.toFixed(1)}%`} icon="bi-percent" />
        </div>
      </div>
      <div className="row g-3">
        <div className="col-lg-5">
          <div className="surface-card p-3 h-100">
            <h2 className="section-title mb-3">Monthly expenses</h2>
            <BarChart
              labels={expenseTrend.map((p) => p.label)}
              values={expenseTrend.map((p) => p.value)}
              label="Expenses"
            />
          </div>
        </div>
        <div className="col-lg-7">
          <div className="surface-card h-100">
            <div className="p-3 border-bottom">
              <h2 className="section-title mb-0">Revenue by authorized offer</h2>
            </div>
            <div className="table-responsive">
              <table className="table table-clean">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Clicks</th>
                    <th>Conversions</th>
                    <th>Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {revenueStreams.map((row) => (
                    <tr key={row.source}>
                      <td>{row.source}</td>
                      <td>{formatNumber(row.clicks)}</td>
                      <td>{formatNumber(row.conversions)}</td>
                      <td>{formatCurrency(row.revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </PageScaffold>
  );
}
