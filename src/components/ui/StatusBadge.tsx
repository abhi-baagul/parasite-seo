import { labelize } from "@/lib/format";

const tone: Record<string, string> = {
  active: "badge-success",
  live: "badge-success",
  indexed: "badge-success",
  verified: "badge-success",
  inserted: "badge-info",
  published: "badge-success",
  approved: "badge-success",
  success: "badge-success",
  generated: "badge-info",
  queued: "badge-info",
  indexing: "badge-info",
  scheduled: "badge-warning",
  planned: "badge-warning",
  paused: "badge-warning",
  inactive: "badge-neutral",
  warning: "badge-warning",
  draft: "badge-neutral",
  idle: "badge-neutral",
  running: "badge-info",
  failed: "badge-danger",
  error: "badge-danger",
  broken: "badge-danger",
  removed: "badge-danger",
  reviewing: "badge-warning",
  review: "badge-warning",
  ready: "badge-info",
  optimizing: "badge-info",
  generating: "badge-info",
  analyzing: "badge-info",
  unpublished: "badge-warning",
  archived: "badge-neutral",
  building: "badge-info",
  authorized_pending: "badge-warning",
  sponsored: "badge-warning",
  ugc: "badge-info",
  nofollow: "badge-neutral",
  standard: "badge-neutral",
};

export function StatusBadge({ value }: { value: string }) {
  const cls = tone[value] ?? "badge-neutral";
  return <span className={`badge-soft ${cls}`}>{labelize(value)}</span>;
}
