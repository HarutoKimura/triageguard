import Link from "next/link";
import { listRuns } from "@/lib/findings";
import { ScorePill } from "@/components/ScorePill";

export const dynamic = "force-dynamic";

export default async function Home() {
  const runs = await listRuns();

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-10 border-b border-[var(--color-border)] pb-6">
        <div className="flex items-baseline gap-3">
          <h1 className="font-mono text-3xl font-semibold tracking-tight text-[var(--color-ink)]">
            TriageGuard
          </h1>
          <span className="font-mono text-[10px] uppercase tracking-[0.3em] text-[var(--color-accent)]">
            Signal vs. Slop · with receipts
          </span>
        </div>
        <p className="mt-3 max-w-2xl text-[var(--color-ink-dim)]">
          Autonomous validator for vulnerability reports. Four parallel Claude
          Opus 4.7 sub-agents check reproducibility, root cause, duplicates,
          and hallucinated citations. A deterministic synthesizer emits a
          signal score with a cited reasoning dossier.
        </p>
      </header>

      <section>
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="font-mono text-[10px] uppercase tracking-[0.3em] text-[var(--color-ink-dim)]">
            Case files · verified runs
          </h2>
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--color-ink-faint)]">
            {runs.length} on file
          </span>
        </div>
        <ul className="grid gap-4 md:grid-cols-2">
          {runs.map((r) => (
            <li key={r.report_id}>
              <Link
                href={{ pathname: `/run/${r.report_id}` }}
                className="group block rounded-lg border border-[var(--color-border)] bg-[var(--color-panel)] p-5 transition-colors hover:border-[var(--color-accent)]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.28em] text-[var(--color-ink-faint)]">
                      file · {r.sample_id}
                    </div>
                    <div className="mt-1 font-mono text-lg text-[var(--color-ink)]">
                      {r.vendor}/{r.product}
                    </div>
                    <div className="mt-0.5 text-sm text-[var(--color-ink-dim)]">
                      {r.bug_class ?? "—"}
                    </div>
                  </div>
                  <ScorePill label={r.label} score={r.score} />
                </div>
                <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 border-t border-dashed border-[var(--color-border)] pt-3 font-mono text-[11px] text-[var(--color-ink-faint)]">
                  <span>rule {r.triggering_rule}</span>
                  <span>{r.recommendation.toLowerCase()}</span>
                  {r.total_runtime_sec != null && (
                    <span>{r.total_runtime_sec.toFixed(1)}s wall</span>
                  )}
                  {r.total_cost_usd != null && (
                    <span>${r.total_cost_usd.toFixed(2)}</span>
                  )}
                  <span className="ml-auto text-[var(--color-accent)] opacity-0 transition-opacity group-hover:opacity-100">
                    open case →
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
        {runs.length === 0 && (
          <div className="rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-panel)] p-6 text-sm text-[var(--color-ink-dim)]">
            <p className="mb-3 font-mono text-[10px] uppercase tracking-[0.28em] text-[var(--color-ink-faint)]">
              no case files yet · run a sample to populate this page
            </p>
            <ol className="list-decimal space-y-2 pl-5">
              <li>
                <code className="font-mono text-[var(--color-ink)]">
                  cp .env.example .env
                </code>
                {" — add "}
                <code className="font-mono text-[var(--color-ink)]">
                  ANTHROPIC_API_KEY
                </code>
                .
              </li>
              <li>
                <code className="font-mono text-[var(--color-ink)]">uv sync</code>
                {" (or "}
                <code className="font-mono text-[var(--color-ink)]">
                  pip install -e &quot;.[dev]&quot;
                </code>
                {")."}
              </li>
              <li>
                <code className="font-mono text-[var(--color-ink)]">
                  python -m orchestrator demo-inputs/s1-cve-2026-3849
                </code>
                {" — verdict lands in ~10 minutes."}
              </li>
            </ol>
            <p className="mt-4">
              Refresh this page when the run finishes; the case appears as a
              card. To triage your own report instead of the demo set, see the
              {" "}
              <span className="font-mono text-[var(--color-ink)]">
                Run your own report
              </span>{" "}
              section in the README.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
