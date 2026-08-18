"use client";

import { use } from "react";
import { ProjectDetailView } from "@/features/projects/ProjectDetailView";

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ProjectDetailView id={id} />;
}
