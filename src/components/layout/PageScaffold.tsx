"use client";

import { usePathname } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";

export function PageScaffold({
  actions,
  children,
}: {
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  return (
    <>
      <PageHeader pathname={pathname} actions={actions} />
      {children}
    </>
  );
}
