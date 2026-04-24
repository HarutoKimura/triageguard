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
        <div className="text-right">
          <div className="text-xs uppercase tracking-widest text-[var(--color-ink-faint)]">
            triggering rule
          </div>
          <div className="font-mono text-lg">{signal.triggering_rule}</div>
        </div>
      </div>

      <p className="mt-4 text-[var(--color-ink)]">{signal.reason}</p>

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
