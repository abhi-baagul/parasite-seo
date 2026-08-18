"use client";

import { use } from "react";
import { ParasiteSeoWorkflow } from "@/features/parasite-seo/ParasiteSeoWorkflow";

export default function ParasiteSeoJobPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ParasiteSeoWorkflow jobId={id} />;
}
