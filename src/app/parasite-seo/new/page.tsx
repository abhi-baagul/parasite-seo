"use client";

import { Suspense } from "react";
import { LoadingState } from "@/components/ui/AsyncState";
import { ParasiteSeoWorkflow } from "@/features/parasite-seo/ParasiteSeoWorkflow";

export default function ParasiteSeoNewPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading…" />}>
      <ParasiteSeoWorkflow />
    </Suspense>
  );
}
