"use client";

import { useParams, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { LoadingState } from "@/components/ui/AsyncState";
import { BacklinkCampaignDetail } from "@/features/parasite-seo/BacklinkCampaignDetail";
import { BacklinkCampaignWizard } from "@/features/parasite-seo/BacklinkCampaignWizard";

function CampaignPageInner() {
  const params = useParams<{ id: string }>();
  const search = useSearchParams();
  const id = params.id;
  if (search.get("wizard") === "1") {
    return <BacklinkCampaignWizard campaignId={id} />;
  }
  return <BacklinkCampaignDetail campaignId={id} />;
}

export default function BacklinkCampaignPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading campaign…" />}>
      <CampaignPageInner />
    </Suspense>
  );
}
