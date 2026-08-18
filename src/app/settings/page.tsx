import { SettingsView } from "@/features/settings/SettingsView";
import { Suspense } from "react";

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="p-4 text-muted">Loading settings…</div>}>
      <SettingsView />
    </Suspense>
  );
}
