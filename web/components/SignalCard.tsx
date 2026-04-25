import type { SignalScoreArtifact } from "@/lib/types";
import { VerdictStamp } from "./ScorePill";

type AgentState = "idle" | "running" | "done";

interface Props {
  state: AgentState;
  signal?: SignalScoreArtifact;
  allAgentsDone: boolean;
}

export function SignalCard({ state, signal, allAgentsDone }: Props) {
  if (state === "idle" && !allAgentsDone) {
    return (
      <div className="rounded-xl border border-dashed border-[var(--color-border)] p-8 text-center text-sm text-[var(--color-ink-faint)]">
        waiting for all four agents to land…
      </div>
    );
  }
  if (state !== "done" || !signal) {
    return (
      <div className="rounded-xl border border-[var(--color-accent)] bg-[color:color-mix(in_oklab,var(--color-accent)_10%,transparent)] p-8 text-center text-sm text-[var(--color-ink)] tg-pulse">
        synthesizing…
      </div>
    );
  }

  const verdicts = signal.sub_agent_verdicts as Record<string, unknown>;

  return (
    <div className="tg-fade-in rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-6">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="flex items-center gap-5">
          <VerdictStamp
            label={signal.label}
            score={signal.score}
            rule={signal.triggering_rule}
          />
          <div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-ink-faint)]">
              recommendation
            </div>
            <div className="font-mono text-base text-[var(--color-ink)]">
              {signal.recommendation}
            </div>
          </div>
        </div>
        {signal.ensemble_confidence != null && (
          <ConfidenceMeter value={signal.ensemble_confidence} />
        )}
      </div>

      <p className="mt-5 text-[var(--color-ink)]">{signal.reason}</p>

      {signal.narrative && <Narrative text={signal.narrative} />}

      <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-2 border-t border-[var(--color-border)] pt-4 text-xs text-[var(--color-ink-dim)] sm:grid-cols-4">
        {Object.entries(verdicts).map(([k, v]) => (
          <div key={k}>
            <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--color-ink-faint)]">
              {k}
            </dt>
            <dd className="font-mono text-[var(--color-ink)]">{String(v)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/**
 * ASCII-bar confidence meter. Replaces the SVG bar that every "agent
 * dashboard" submission uses. Reads as monospace progress, like a build log.
 */
function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  const cells = 20;
  const filled = Math.round((pct / 100) * cells);
  const bar = "█".repeat(filled) + "░".repeat(cells - filled);
  const color =
    pct >= 85
      ? "var(--color-signal)"
      : pct >= 60
        ? "var(--color-uncertain)"
        : "var(--color-slop)";
  return (
    <div className="text-right">
      <div className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-ink-faint)]">
        confidence
      </div>
      <div
        className="mt-1 font-mono text-[15px] leading-none"
        style={{ color }}
        aria-label={`confidence ${pct} percent`}
      >
        {bar}
      </div>
      <div className="mt-1 font-mono text-xs text-[var(--color-ink-dim)]">
        {pct}% · geo-mean ×4
      </div>
    </div>
  );
}

/**
 * Narrative panel — rendered as a cream "paper" sheet resting on the
 * warm-black canvas, with serif body text. The hero artifact: the maintainer
 * reads a short written report, not a chat output.
 */
function Narrative({ text }: { text: string }) {
  const paragraphs = text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
  return (
    <section className="mt-6 tg-paper rounded-md p-6">
      <header className="mb-3 flex items-baseline justify-between border-b border-[var(--color-paper-edge)] pb-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.28em] text-[var(--color-ink-deep)]">
          Reproducibility dossier
        </div>
        <div className="font-mono text-[10px] tracking-[0.15em] text-[var(--color-paper-rule)]">
          Opus 4.7 · xhigh · adaptive thinking
        </div>
      </header>
      <div className="space-y-3 text-[15px] leading-relaxed text-[var(--color-ink-deep)]">
        {paragraphs.map((p, i) => (
          <p
            key={i}
            className={i === 0 ? "first-letter:font-serif first-letter:text-3xl first-letter:font-bold first-letter:mr-1 first-letter:float-left first-letter:leading-[0.9]" : ""}
          >
            {p}
          </p>
        ))}
      </div>
    </section>
  );
}
