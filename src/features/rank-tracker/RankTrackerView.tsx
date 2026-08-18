"use client";

import { filterByProject, rankRows } from "@/data/mock";
import { useProject } from "@/context/ProjectContext";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { DataTable } from "@/components/ui/DataTable";
import { formatDate, rankChange } from "@/lib/format";

export function RankTrackerView() {
  const { selectedId } = useProject();
  const rows = filterByProject(rankRows, selectedId);

  return (
    <PageScaffold>
      <div className="surface-card">
        <DataTable
          rows={rows}
          rowKey={(row) => row.id}
          searchPlaceholder="Search keywords"
          searchText={(row) => `${row.keyword} ${row.targetUrl}`}
          columns={[
            { key: "keyword", header: "Keyword" },
            {
              key: "targetUrl",
              header: "Target URL",
              render: (row) => row.targetUrl.replace("https://", ""),
            },
            {
              key: "currentPosition",
              header: "Current",
              render: (row) => row.currentPosition ?? "—",
            },
            {
              key: "previousPosition",
              header: "Previous",
              render: (row) => row.previousPosition ?? "—",
            },
            {
              key: "change",
              header: "Change",
              render: (row) => {
                const change = rankChange(row.currentPosition, row.previousPosition);
                const color =
                  change.direction === "up"
                    ? "text-success"
                    : change.direction === "down"
                      ? "text-danger"
                      : "text-muted";
                return <span className={color}>{change.label}</span>;
              },
            },
            {
              key: "trend",
              header: "Trend",
              render: (row) => {
                const change = rankChange(row.currentPosition, row.previousPosition);
                const icon =
                  change.direction === "up"
                    ? "bi-arrow-up-right"
                    : change.direction === "down"
                      ? "bi-arrow-down-right"
                      : change.direction === "new"
                        ? "bi-plus"
                        : "bi-dash";
                return <i className={`bi ${icon}`} aria-label={change.direction} />;
              },
            },
            {
              key: "lastChecked",
              header: "Last checked",
              render: (row) => formatDate(row.lastChecked),
            },
          ]}
        />
      </div>
    </PageScaffold>
  );
}
