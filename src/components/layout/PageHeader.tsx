import { matchPageMeta } from "@/lib/navigation";
import Link from "next/link";

export function Breadcrumbs({ pathname }: { pathname: string }) {
  const meta = matchPageMeta(pathname);
  return (
    <nav className="breadcrumb-nav" aria-label="Breadcrumb">
      {meta.crumbs.map((crumb, index) => (
        <span key={`${crumb.label}-${index}`}>
          {index > 0 ? <span className="mx-1">/</span> : null}
          {crumb.href ? <Link href={crumb.href}>{crumb.label}</Link> : <span>{crumb.label}</span>}
        </span>
      ))}
    </nav>
  );
}

export function PageHeader({
  pathname,
  actions,
}: {
  pathname: string;
  actions?: React.ReactNode;
}) {
  const meta = matchPageMeta(pathname);
  return (
    <div className="page-header d-flex flex-column flex-md-row justify-content-between align-items-md-end gap-3 mb-4">
      <div>
        <Breadcrumbs pathname={pathname} />
        <h1>{meta.title}</h1>
        {meta.description ? <p>{meta.description}</p> : null}
      </div>
      {actions ? <div className="d-flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}
