"use client";

import { usePathname } from "next/navigation";
import { ProjectProvider } from "@/context/ProjectContext";
import { AppShell } from "@/components/layout/AppShell";

export function AppProviders({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublicPage = pathname?.startsWith("/p/");

  // Public pages stay lightweight — no project context, no admin shell.
  if (isPublicPage) {
    return <>{children}</>;
  }

  return (
    <ProjectProvider>
      <AppShell>{children}</AppShell>
    </ProjectProvider>
  );
}
