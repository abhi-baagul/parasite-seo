import Link from "next/link";

interface EmptyStateProps {
  icon: string;
  title: string;
  body: string;
  actionHref?: string;
  actionLabel?: string;
}

export function EmptyState({ icon, title, body, actionHref, actionLabel }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <i className={`bi ${icon} fs-3 d-block mb-2`} />
      <h2 className="h6 text-dark">{title}</h2>
      <p className="mb-3">{body}</p>
      {actionHref && actionLabel ? (
        <Link href={actionHref} className="btn btn-sm btn-accent">
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}
