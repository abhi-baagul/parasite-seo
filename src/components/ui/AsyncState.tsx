"use client";

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="surface-card p-4">
      <div className="placeholder-glow">
        <span className="placeholder col-6 mb-2" />
        <span className="placeholder col-12 mb-2" />
        <span className="placeholder col-8" />
      </div>
      <div className="small text-muted mt-3">{label}</div>
    </div>
  );
}

export function EmptyStateBlock({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="surface-card p-5 text-center">
      <h2 className="h5">{title}</h2>
      <p className="text-muted mb-3">{body}</p>
      {action}
    </div>
  );
}

export function ErrorState({
  title,
  message,
  onRetry,
}: {
  title: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="surface-card p-4 border border-danger-subtle">
      <h2 className="h6 text-danger">{title}</h2>
      <p className="text-muted mb-3">{message}</p>
      {onRetry ? (
        <button type="button" className="btn btn-sm btn-accent" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}
