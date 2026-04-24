import { promises as fs } from "node:fs";
import path from "node:path";
import type {
  DuplicateArtifact,
  HallucinationArtifact,
  InputMeta,
  ReproArtifact,
  RootCauseArtifact,
  RunBundle,
  RunSummary,
  SignalScoreArtifact,
} from "./types";

const REPO_ROOT = path.resolve(process.cwd(), "..");
const FINDINGS_DIR = path.join(REPO_ROOT, "findings");

async function readJson<T>(file: string): Promise<T> {
  const raw = await fs.readFile(file, "utf8");
  return JSON.parse(raw) as T;
}

async function tryReadText(file: string): Promise<string> {
  try {
    return await fs.readFile(file, "utf8");
  } catch {
    return "";
  }
}

async function listRunDirs(): Promise<string[]> {
  const entries = await fs.readdir(FINDINGS_DIR, { withFileTypes: true });
  return entries
    .filter((e) => e.isDirectory())
    .map((e) => e.name)
    .sort();
}

export async function loadRun(reportId: string): Promise<RunBundle | null> {
  const dir = path.join(FINDINGS_DIR, reportId);
  try {
    await fs.access(dir);
  } catch {
    return null;
  }

  const [signal, repro, rootCause, duplicate, hallucination, meta, inputMd, synthesisMd] =
    await Promise.all([
      readJson<SignalScoreArtifact>(path.join(dir, "SIGNAL_SCORE.json")),
      readJson<ReproArtifact>(path.join(dir, "A_reproducibility.json")),
      readJson<RootCauseArtifact>(path.join(dir, "B_root_cause.json")),
      readJson<DuplicateArtifact>(path.join(dir, "C_duplicate.json")),
      readJson<HallucinationArtifact>(path.join(dir, "D_hallucination.json")),
      readJson<InputMeta>(path.join(dir, "INPUT_meta.json")),
      tryReadText(path.join(dir, "INPUT.md")),
      tryReadText(path.join(dir, "SYNTHESIS.md")),
    ]);

  return {
    report_id: reportId,
    sample_id: meta.sample_id,
    input_meta: meta,
    input_md: inputMd,
    repro,
    root_cause: rootCause,
    duplicate,
    hallucination,
    signal,
    synthesis_md: synthesisMd,
  };
}

function summarizeBundle(bundle: RunBundle): RunSummary {
  return {
    report_id: bundle.report_id,
    sample_id: bundle.sample_id,
    vendor: bundle.input_meta.target.vendor,
    product: bundle.input_meta.target.product,
    bug_class: bundle.input_meta.bug_class ?? null,
    label: bundle.signal.label,
    score: bundle.signal.score,
    recommendation: bundle.signal.recommendation,
    triggering_rule: bundle.signal.triggering_rule,
    total_runtime_sec: bundle.signal.total_runtime_sec ?? null,
    total_cost_usd: bundle.signal.total_cost_usd ?? null,
    submitted_at: bundle.input_meta.submitted_at,
  };
}

// Return one representative run per sample_id (the most recent).
export async function listRuns(): Promise<RunSummary[]> {
  const dirs = await listRunDirs();
  const bundles = await Promise.all(
    dirs.map(async (d) => {
      try {
        return await loadRun(d);
      } catch {
        return null;
      }
    }),
  );
  const bySample = new Map<string, RunBundle>();
  for (const b of bundles) {
    if (!b) continue;
    const existing = bySample.get(b.sample_id);
    if (!existing || b.report_id > existing.report_id) {
      bySample.set(b.sample_id, b);
    }
  }
  return [...bySample.values()]
    .map(summarizeBundle)
    .sort((a, b) => a.sample_id.localeCompare(b.sample_id));
}

export async function latestReportIdForSample(
  sampleId: string,
): Promise<string | null> {
  const dirs = await listRunDirs();
  const matches = dirs.filter((d) => d.endsWith(`_${sampleId}`));
  if (matches.length === 0) return null;
  return matches.sort().at(-1) ?? null;
}
