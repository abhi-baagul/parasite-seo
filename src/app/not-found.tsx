import Link from "next/link";

export default function NotFound() {
  return (
    <div className="surface-card p-5 text-center">
      <h1 className="h4">Page not found</h1>
      <p className="text-muted">That route is not part of this prototype.</p>
      <Link href="/" className="btn btn-accent">
        Back to dashboard
      </Link>
    </div>
  );
}
