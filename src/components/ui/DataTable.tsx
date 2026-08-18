"use client";

import { useMemo, useState } from "react";
import { EmptyState } from "@/components/ui/EmptyState";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  rows: T[];
  columns: Column<T>[];
  rowKey: (row: T) => string;
  searchable?: boolean;
  searchPlaceholder?: string;
  searchText?: (row: T) => string;
  emptyTitle?: string;
  emptyBody?: string;
}

export function DataTable<T>({
  rows,
  columns,
  rowKey,
  searchable = true,
  searchPlaceholder = "Filter rows",
  searchText,
  emptyTitle = "No records",
  emptyBody = "Nothing matches the current filters.",
}: DataTableProps<T>) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((row) => {
      const haystack = searchText
        ? searchText(row)
        : columns
            .map((col) => {
              const value = (row as Record<string, unknown>)[col.key];
              return String(value ?? "");
            })
            .join(" ");
      return haystack.toLowerCase().includes(q);
    });
  }, [rows, query, columns, searchText]);

  return (
    <div>
      {searchable ? (
        <div className="p-3 border-bottom">
          <div className="search-field" style={{ maxWidth: 320 }}>
            <i className="bi bi-funnel" />
            <input
              className="form-control"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={searchPlaceholder}
              aria-label={searchPlaceholder}
            />
          </div>
        </div>
      ) : null}
      <div className="table-responsive">
        <table className="table table-clean align-middle">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} className={col.className}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={rowKey(row)}>
                {columns.map((col) => (
                  <td key={col.key} className={col.className}>
                    {col.render
                      ? col.render(row)
                      : String((row as Record<string, unknown>)[col.key] ?? "—")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {filtered.length === 0 ? <EmptyState icon="bi-inbox" title={emptyTitle} body={emptyBody} /> : null}
    </div>
  );
}
