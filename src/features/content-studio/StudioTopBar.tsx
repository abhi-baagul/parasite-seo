"use client";

import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function StudioTopBar({
  title,
  status,
  saveLabel,
  busy,
  onPreview,
  onExport,
  onApprove,
  onSave,
  onCreateWebPage,
}: {
  title: string;
  status: string;
  saveLabel: string;
  busy: boolean;
  onPreview: () => void;
  onExport: () => void;
  onApprove: () => void;
  onSave: () => void;
  onCreateWebPage?: () => void;
}) {
  return (
    <div className="studio-topbar surface-card p-3 mb-3">
      <div className="d-flex flex-wrap align-items-center gap-2 justify-content-between">
        <div className="d-flex flex-wrap align-items-center gap-3 min-w-0">
          <Link href="/content-studio" className="btn btn-ghost btn-sm">
            ← Content
          </Link>
          <div className="min-w-0">
            <div className="fw-semibold text-truncate" style={{ maxWidth: "42vw" }}>
              {title || "Untitled"}
            </div>
            <div className="small text-muted d-flex align-items-center gap-2">
              <StatusBadge value={status} />
              <span>{saveLabel}</span>
            </div>
          </div>
        </div>
        <div className="d-flex flex-wrap gap-2">
          <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={onSave}>
            Save
          </button>
          <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={onPreview}>
            Preview
          </button>
          <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={onExport}>
            Export
          </button>
          {onCreateWebPage ? (
            <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={onCreateWebPage}>
              Create web page
            </button>
          ) : null}
          <button type="button" className="btn btn-accent btn-sm" disabled={busy} onClick={onApprove}>
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
