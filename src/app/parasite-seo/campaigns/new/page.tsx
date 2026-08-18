"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { LoadingState } from "@/components/ui/AsyncState";
import { BacklinkCampaignWizard } from "@/features/parasite-seo/BacklinkCampaignWizard";
import { CreateBacklinkCampaignFlow } from "@/features/parasite-seo/CreateBacklinkCampaignFlow";

function NewCampaignInner() {
  const search = useSearchParams();
  if (search.get("wizard") === "1") return <BacklinkCampaignWizard />;
  return <CreateBacklinkCampaignFlow />;
}

export default function NewBacklinkCampaignPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading…" />}>
      <NewCampaignInner />
    </Suspense>
  );
}
