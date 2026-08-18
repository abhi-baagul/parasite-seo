"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PageScaffold } from "@/components/layout/PageScaffold";
import { useProject } from "@/context/ProjectContext";
import { ApiClientError } from "@/services/api-client";
import {
  analyzePrompt,
  confirmRequirements,
  type PromptRequirements,
} from "@/services/prompt-service";

const SAMPLE_PROMPT = `As an SEO-content writer, write an informative blog post on

[DIClock Referral Code "WL1Z375N" - Get 40% Off on Annual Plan]

of around 1000 words targeting keyword [DIClock Referral Code].

Also include H1, H2, H3, bullet points, tables, and a clear CTA.

Primary keywords:
DIClock Referral Code For New User
DIClock Referral Code 2026
DIClock Referral Code Latest
DIClock Referral Code Signup`;

const emptyRequirements: PromptRequirements = {
  topic: null,
  main_keyword: null,
  secondary_keywords: [],
  word_count: null,
  content_type: null,
  intent: null,
  tone: null,
  audience: null,
  country: null,
  language: null,
  required_headings: [],
  required_elements: [],
  cta_requirement: null,
  offer_information: null,
  promotional_information: null,
  target_url_if_present: null,
  anchor_text_if_present: null,
  media_requirements: [],
  special_instructions: null,
  uncertain_fields: [],
};

export function CreateContentView() {
  const router = useRouter();
  const { projects, selectedId } = useProject();
  const [prompt, setPrompt] = useState(SAMPLE_PROMPT);
  const [promptId, setPromptId] = useState<string | null>(null);
  const [requirements, setRequirements] = useState<PromptRequirements>(emptyRequirements);
  const [analyzed, setAnalyzed] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const projectId = selectedId === "all" ? projects[0]?.id : selectedId;

  function updateField<K extends keyof PromptRequirements>(key: K, value: PromptRequirements[K]) {
    setRequirements((current) => ({ ...current, [key]: value }));
  }

  async function onAnalyze() {
    if (!projectId) {
      setError("Create a project before analyzing a prompt");
      return;
    }
    setAnalyzing(true);
    setError(null);
    try {
      const result = await analyzePrompt({ project_id: projectId, prompt });
      setPromptId(result.prompt_id);
      setRequirements(result.requirements);
      setAnalyzed(true);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Prompt analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }

  async function onConfirm() {
    if (!promptId) {
      setError("Analyze the prompt before confirming requirements");
      return;
    }
    setConfirming(true);
    setError(null);
    try {
      const result = await confirmRequirements(promptId, requirements);
      router.push(`/content-studio/${result.content_id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to confirm requirements");
      setConfirming(false);
    }
  }

  return (
    <PageScaffold>
      <div className="row g-3">
        <div className="col-xl-7">
          <div className="surface-card p-4">
            <div className="mb-3">
              <label className="form-label" htmlFor="prompt">
                Prompt
              </label>
              <textarea
                id="prompt"
                className="form-control"
                rows={12}
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                required
              />
              <div className="form-text">
                Original prompt is stored exactly. Analysis is saved separately and never overwrites it.
              </div>
            </div>
            {error ? <div className="alert alert-danger py-2">{error}</div> : null}
            <div className="d-flex flex-wrap gap-2">
              <button
                className="btn btn-accent"
                type="button"
                onClick={() => void onAnalyze()}
                disabled={analyzing || !prompt.trim()}
              >
                {analyzing ? "Analyzing…" : analyzed ? "Re-analyze" : "Analyze Prompt"}
              </button>
              <button
                className="btn btn-ghost"
                type="button"
                onClick={() => void onConfirm()}
                disabled={!analyzed || confirming}
              >
                {confirming ? "Confirming…" : "Confirm Requirements"}
              </button>
            </div>
          </div>
        </div>

        <div className="col-xl-5">
          <div className="surface-card p-4 h-100">
            <h2 className="section-title mb-3">Content requirements</h2>
            {!analyzed ? (
              <p className="text-muted mb-0">
                Paste a prompt and click Analyze Prompt to extract editable requirements.
              </p>
            ) : analyzing ? (
              <p className="text-muted mb-0">Analyzing prompt…</p>
            ) : (
              <div className="vstack gap-3">
                {requirements.uncertain_fields.length > 0 ? (
                  <div className="alert alert-warning py-2 small mb-0">
                    Needs confirmation: {requirements.uncertain_fields.join(", ")}
                  </div>
                ) : null}
                <Field label="Topic" value={requirements.topic ?? ""} onChange={(v) => updateField("topic", v || null)} />
                <Field
                  label="Primary keyword"
                  value={requirements.main_keyword ?? ""}
                  onChange={(v) => updateField("main_keyword", v || null)}
                />
                <Field
                  label="Secondary keywords"
                  value={requirements.secondary_keywords.join("\n")}
                  onChange={(v) =>
                    updateField(
                      "secondary_keywords",
                      v
                        .split("\n")
                        .map((item) => item.trim())
                        .filter(Boolean),
                    )
                  }
                  rows={4}
                />
                <Field
                  label="Content type"
                  value={requirements.content_type ?? ""}
                  onChange={(v) => updateField("content_type", v || null)}
                />
                <Field
                  label="Word count"
                  value={requirements.word_count?.toString() ?? ""}
                  onChange={(v) => updateField("word_count", v ? Number(v) : null)}
                />
                <Field label="Tone" value={requirements.tone ?? ""} onChange={(v) => updateField("tone", v || null)} />
                <Field
                  label="Target audience"
                  value={requirements.audience ?? ""}
                  onChange={(v) => updateField("audience", v || null)}
                />
                <Field
                  label="Country"
                  value={requirements.country ?? ""}
                  onChange={(v) => updateField("country", v || null)}
                />
                <Field
                  label="Language"
                  value={requirements.language ?? ""}
                  onChange={(v) => updateField("language", v || null)}
                />
                <Field
                  label="CTA"
                  value={
                    requirements.cta_requirement == null
                      ? ""
                      : requirements.cta_requirement
                        ? "required"
                        : "not required"
                  }
                  onChange={(v) =>
                    updateField(
                      "cta_requirement",
                      v.trim() === "" ? null : v.toLowerCase().includes("not") ? false : true,
                    )
                  }
                />
                <Field
                  label="Required elements"
                  value={requirements.required_elements.join(", ")}
                  onChange={(v) =>
                    updateField(
                      "required_elements",
                      v
                        .split(",")
                        .map((item) => item.trim())
                        .filter(Boolean),
                    )
                  }
                />
                <Field
                  label="Offer information"
                  value={requirements.offer_information ?? ""}
                  onChange={(v) => updateField("offer_information", v || null)}
                  rows={3}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </PageScaffold>
  );
}

function Field({
  label,
  value,
  onChange,
  rows = 1,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
}) {
  const id = label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div>
      <label className="form-label" htmlFor={id}>
        {label}
      </label>
      {rows > 1 ? (
        <textarea id={id} className="form-control" rows={rows} value={value} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <input id={id} className="form-control" value={value} onChange={(e) => onChange(e.target.value)} />
      )}
    </div>
  );
}
