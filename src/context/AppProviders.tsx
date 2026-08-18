"use client";

import { usePathname } from "next/navigation";
import { ProjectProvider } from "@/context/ProjectContext";
import { SessionProvider, useSession } from "@/context/SessionContext";
import { AppShell } from "@/components/layout/AppShell";
import { SignInScreen } from "@/features/settings/SignInScreen";

export function AppProviders({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublicPage = pathname?.startsWith("/p/");

  if (isPublicPage) {
    return <>{children}</>;
  }

  return (
    <SessionProvider>
      <AuthedShell>{children}</AuthedShell>
    </SessionProvider>
  );
}

function AuthedShell({ children }: { children: React.ReactNode }) {
  const { signedOut, loading } = useSession();
  if (loading) {
    return <div className="p-4 text-muted">Loading workspace…</div>;
  }
  if (signedOut) {
    return <SignInScreen />;
  }
  return (
    <ProjectProvider>
      <AppShell>{children}</AppShell>
    </ProjectProvider>
  );
}
