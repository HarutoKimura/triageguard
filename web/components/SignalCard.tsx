import type { SignalScoreArtifact } from "@/lib/types";
import { ScorePill } from "./ScorePill";

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
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <ScorePill label={signal.label} score={signal.score} size="lg" />
          <div>
            <div className="text-xs uppercase tracking-widest text-[var(--color-ink-faint)]">
              recommendation
            </div>
            <div className="font-mono text-lg">{signal.recommendation}</div>
          </div>
        </div>
        <div className="flex items-start gap-6">
          {signal.ensemble_confidence != null && (
            <ConfidenceMeter value={signal.ensemble_confidence} />
          )}
          <div className="text-right">
            <div className="text-xs uppercase tracking-widest text-[var(--color-ink-faint)]">
              triggering rule
            </div>
            <div className="font-mono text-lg">{signal.triggering_rule}</div>
          </div>
        </div>
      </div>

      <p className="mt-4 text-[var(--color-ink)]">{signal.reason}</p>

      {signal.narrative && <Narrative text={signal.narrative} />}

      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 border-t border-[var(--color-border)] pt-4 text-xs text-[var(--color-ink-dim)] sm:grid-cols-4">
        {Object.entries(verdicts).map(([k, v]) => (
          <div key={k}>
            <dt className="font-mono text-[var(--color-ink-faint)]">{k}</dt>
            <dd className="font-mono text-[var(--color-ink)]">{String(v)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  const barColor =
    pct >= 85
      ? "var(--color-signal)"
      : pct >= 60
        ? "var(--color-uncertain)"
        : "var(--color-slop)";
  return (
    <div className="min-w-28">
      <div className="text-xs uppercase tracking-widest text-[var(--color-ink-faint)] text-right">
        confidence
      </div>
      <div className="mt-0.5 flex items-baseline justify-end gap-1">
        <span className="font-mono text-lg">{pct}%</span>
      </div>
      <div
        className="mt-1 h-1.5 w-28 rounded-full bg-[var(--color-panel-2)] overflow-hidden"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
      >
        <div
          className="h-full transition-[width] duration-500"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
      <div className="mt-1 text-right text-[10px] text-[var(--color-ink-faint)] font-mono">
        geo-mean ×4
      </div>
    </div>
  );
}

function Narrative({ text }: { text: string }) {
  const paragraphs = text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
  return (
    <section className="mt-5 rounded-lg border border-[var(--color-border)] bg-[var(--color-panel-2)] p-4">
      <div className="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-widest text-[var(--color-ink-faint)]">
        <span>Opus 4.7 reasoning</span>
        <span className="font-mono text-[var(--color-ink-dim)] normal-case tracking-normal">
          xhigh · adaptive thinking
        </span>
      </div>
      <div className="space-y-3 text-[13px] leading-relaxed text-[var(--color-ink)]">
        {paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </div>
    </section>
  );
}
