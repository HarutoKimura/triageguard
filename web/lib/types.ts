export type SignalLabel = "SIGNAL" | "SLOP" | "UNCERTAIN" | "ERRORED";
export type Recommendation = "ACCEPT" | "REVIEW" | "REJECT";

export type ReproVerdict =
  | "reproduced"
  | "failed_to_reproduce"
  | "no_poc"
  | "build_error"
  | "timeout";

export type RootCauseMatch =
  | "match"
  | "partial_match"
  | "mismatch"
  | "file_not_found";

export type DupVerdict = "novel" | "duplicate" | "similar";

export type RefKind =
  | "function"
  | "file"
  | "line"
  | "symbol"
  | "cve"
  | "cvss_vector"
  | "tag"
  | "option";
export type RefStatus = "verified" | "invalid" | "unchecked";

export interface InputMeta {
  sample_id: string;
  submitter: string;
  target: {
    vendor: string;
    product: string;
    repo: string;
    claimed_tag?: string | null;
    claimed_cve?: string | null;
  };
  bug_class?: string | null;
  poc: { present: boolean; path?: string | null; entry?: string | null };
  submitted_at: string;
  expected: {
    label: SignalLabel;
    score_min: number;
    score_max: number;
    triggering_rule_hint?: number | null;
  };
}

export interface ReproArtifact {
  agent: "reproducibility";
  report_id: string;
  verdict: ReproVerdict;
  confidence: number;
  evidence: {
    target_tag?: string | null;
    build_exit_code?: number | null;
    poc_exit_code?: number | null;
    poc_signal?: string | null;
    sanitizer_summary?: string | null;
    sanitizer_frames?: string[];
  };
  errors: string[];
}

export interface RootCauseArtifact {
  agent: "root_cause";
  report_id: string;
  match: RootCauseMatch;
  confidence: number;
  claims_checked: {
    claim: string;
    status: "verified" | "partially_verified" | "not_verified";
    file?: string | null;
    line_start?: number | null;
    line_end?: number | null;
    snippet?: string | null;
    note?: string | null;
  }[];
  errors: string[];
}

export interface DuplicateArtifact {
  agent: "duplicate_detector";
  report_id: string;
  verdict: DupVerdict;
  confidence: number;
  queried_databases: string[];
  top_candidates: {
    id: string;
    title: string;
    similarity: number;
    verdict: "different_class" | "related_but_distinct" | "likely_same";
  }[];
  matched_cve?: string | null;
  errors: string[];
}

export interface HallucinationArtifact {
  agent: "hallucination_detector";
  report_id: string;
  extracted_claims: {
    kind: RefKind;
    value: string;
    status: RefStatus;
    source?: string | null;
    note?: string | null;
  }[];
  invalid_refs: {
    kind: RefKind;
    value: string;
    note?: string | null;
  }[];
  stats: {
    total: number;
    verified: number;
    invalid: number;
    unchecked: number;
  };
  errors: string[];
}

export interface SignalScoreArtifact {
  report_id: string;
  score: number;
  label: SignalLabel;
  recommendation: Recommendation;
  reason: string;
  triggering_rule: number;
  sub_agent_verdicts: Record<string, unknown>;
  generated_at?: string | null;
  total_runtime_sec?: number | null;
  total_cost_usd?: number | null;
  narrative?: string | null;
}

export interface RunBundle {
  report_id: string;
  sample_id: string;
  input_meta: InputMeta;
  input_md: string;
  repro: ReproArtifact;
  root_cause: RootCauseArtifact;
  duplicate: DuplicateArtifact;
  hallucination: HallucinationArtifact;
  signal: SignalScoreArtifact;
  synthesis_md: string;
}

export interface RunSummary {
  report_id: string;
  sample_id: string;
  vendor: string;
  product: string;
  bug_class: string | null;
  label: SignalLabel;
  score: number;
  recommendation: Recommendation;
  triggering_rule: number;
  total_runtime_sec: number | null;
  total_cost_usd: number | null;
  submitted_at: string;
}

export type ReplayEvent =
  | { type: "bootstrap"; report_id: string; sample_id: string }
  | { type: "agent_start"; agent: "A" | "B" | "C" | "D" }
  | {
      type: "agent_done";
      agent: "A";
      payload: ReproArtifact;
    }
  | {
      type: "agent_done";
      agent: "B";
      payload: RootCauseArtifact;
    }
  | {
      type: "agent_done";
      agent: "C";
      payload: DuplicateArtifact;
    }
  | {
      type: "agent_done";
      agent: "D";
      payload: HallucinationArtifact;
    }
  | { type: "synthesis_start" }
  | { type: "synthesis_done"; payload: SignalScoreArtifact }
  | { type: "end" };
