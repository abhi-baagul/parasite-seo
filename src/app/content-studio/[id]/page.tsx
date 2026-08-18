"use client";

import { use } from "react";
import { ContentStudioEditorPage } from "@/features/content-studio/ContentStudioEditorPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ContentStudioEditorPage id={id} />;
}
