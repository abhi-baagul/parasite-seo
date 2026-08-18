interface StatCardProps {
  label: string;
  value: string;
  icon: string;
  hint?: string;
}

export function StatCard({ label, value, icon, hint }: StatCardProps) {
  return (
    <div className="surface-card stat-card">
      <div className="d-flex justify-content-between align-items-start">
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value">{value}</div>
          {hint ? <div className="small text-muted mt-1">{hint}</div> : null}
        </div>
        <i className={`bi ${icon}`} aria-hidden="true" />
      </div>
    </div>
  );
}
