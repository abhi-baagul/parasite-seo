"use client";

import type { StudioOutlineItem } from "@/services/studio-service";

export function StudioOutlineNav({
  items,
  activeAnchor,
  onJump,
}: {
  items: StudioOutlineItem[];
  activeAnchor?: string | null;
  onJump: (anchor: string) => void;
}) {
  if (!items.length) {
    return <p className="small text-muted mb-0">No headings yet. Add H1–H3 in the editor.</p>;
  }
  return (
    <ul className="list-unstyled studio-outline mb-0">
      {items.map((item) => (
        <li key={item.anchor} style={{ paddingLeft: `${(item.level - 1) * 12}px` }}>
          <button
            type="button"
            className={`btn btn-link btn-sm text-start px-0 ${activeAnchor === item.anchor ? "fw-semibold" : ""}`}
            onClick={() => onJump(item.anchor)}
          >
            <span className="text-muted me-1">H{item.level}</span>
            {item.text}
          </button>
        </li>
      ))}
    </ul>
  );
}
