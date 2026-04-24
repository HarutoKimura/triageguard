import Link from "next/link";
import { listRuns } from "@/lib/findings";
import { ScorePill } from "@/components/ScorePill";

export const dynamic = "force-dynamic";

export default async function Home() {
  const runs = await listRuns();

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-10">
        <div className="flex items-baseline gap-3">
          <h1 className="text-3xl font-semibold tracking-tight">TriageGuard</h1>
          <span className="text-[var(--color-ink-dim)] text-sm">
            Signal vs. Slop, with receipts
          </span>
        </div>
        <p className="mt-2 text-[var(--color-ink-dim)] max-w-2xl">
          An autonomous validator for vulnerability reports. Four parallel sub-agents
          check reproducibility, root cause, duplicates, and hallucinated citations,
          then a deterministic synthesizer emits a signal score.
        </p>
      </header>

      <section>
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-xs uppercase tracking-widest text-[var(--color-ink-dim)]">
            Verified runs
          </h2>
          <span className="text-xs text-[var(--color-ink-faint)]">
            {runs.length} sample{runs.length === 1 ? "" : "s"}
          </span>
        </div>
        <ul className="grid gap-3 md:grid-cols-2">
          {runs.map((r) => (
            <li key={r.report_id}>
              <Link
                href={{ pathname: `/run/${r.report_id}` }}
                className="block rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-5 hover:border-[var(--color-accent)] transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-xs uppercase tracking-widest text-[var(--color-ink-faint)]">
                      {r.sample_id}
                    </div>
                    <div className="mt-1 text-lg font-medium">
                      {r.vendor}/{r.product}
                    </div>
                    <div className="text-sm text-[var(--color-ink-dim)]">
                      {r.bug_class ?? "—"}
                    </div>
                  </div>
                  <ScorePill label={r.label} score={r.score} />
                </div>
                <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-xs text-[var(--color-ink-faint)]">
                  <span>rule {r.triggering_rule}</span>
                  <span>{r.recommendation.toLowerCase()}</span>
                  {r.total_runtime_sec != null && (
                    <span>{r.total_runtime_sec.toFixed(1)}s wall</span>
                  )}
                  {r.total_cost_usd != null && (
                    <span>${r.total_cost_usd.toFixed(2)}</span>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
        {runs.length === 0 && (
          <p className="text-[var(--color-ink-dim)]">
            No findings/ runs yet. Run{" "}
            <code className="text-[var(--color-ink)]">
              .venv/bin/python -m orchestrator demo-inputs/s1-cve-2026-3849/
            </code>{" "}
            first.
          </p>
        )}
      </section>
    </main>
  );
}
