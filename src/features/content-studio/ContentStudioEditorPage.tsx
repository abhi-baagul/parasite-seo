"use client";

import { PageScaffold } from "@/components/layout/PageScaffold";
import { StudioWorkspace } from "@/features/content-studio/StudioWorkspace";

export function ContentStudioEditorPage({ id }: { id: string }) {
  return (
    <PageScaffold>
      <StudioWorkspace contentId={id} />
    </PageScaffold>
  );
}
