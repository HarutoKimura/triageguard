import Link from "next/link";
import { notFound } from "next/navigation";
import { loadRun } from "@/lib/findings";
import { LiveReplay } from "@/components/LiveReplay";

export const dynamic = "force-dynamic";

export default async function RunPage({
  params,
}: {
  params: Promise<{ reportId: string }>;
}) {
  const { reportId } = await params;
  const bundle = await loadRun(reportId);
  if (!bundle) notFound();

  const m = bundle.input_meta;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <nav className="mb-6 text-sm text-[var(--color-ink-dim)]">
        <Link href="/" className="hover:text-[var(--color-ink)]">
          ← all runs
        </Link>
      </nav>

      <header className="mb-8 rounded-lg border border-[var(--color-border)] bg-[var(--color-panel)] p-6">
        <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-[var(--color-accent)]">
            case file · {m.sample_id}
          </div>
          <div className="font-mono text-lg text-[var(--color-ink)]">
            {m.target.vendor}/{m.target.product}
          </div>
          {m.target.claimed_tag && (
            <div className="font-mono text-xs text-[var(--color-ink-dim)]">
              tag {m.target.claimed_tag}
            </div>
          )}
          {m.target.claimed_cve && (
            <div className="font-mono text-xs text-[var(--color-uncertain)]">
              {m.target.claimed_cve}
            </div>
          )}
        </div>
        <div className="mt-2 font-mono text-[11px] text-[var(--color-ink-dim)]">
          {m.bug_class ?? "—"} · submitted {new Date(m.submitted_at).toISOString().slice(0, 10)}{" "}
          · submitter {m.submitter}
        </div>
      </header>

      <LiveReplay bundle={bundle} />
    </main>
  );
}
