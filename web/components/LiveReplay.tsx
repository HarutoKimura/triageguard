"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type {
  DuplicateArtifact,
  HallucinationArtifact,
  ReplayEvent,
  ReproArtifact,
  RootCauseArtifact,
  RunBundle,
  SignalScoreArtifact,
} from "@/lib/types";
import { AgentCard } from "./AgentCard";
import { SignalCard } from "./SignalCard";

type AgentState = "idle" | "running" | "done";

interface Slots {
  A?: ReproArtifact;
  B?: RootCauseArtifact;
  C?: DuplicateArtifact;
  D?: HallucinationArtifact;
  signal?: SignalScoreArtifact;
}

interface States {
  A: AgentState;
  B: AgentState;
  C: AgentState;
  D: AgentState;
  synth: AgentState;
}

const INITIAL_STATES: States = {
  A: "idle",
  B: "idle",
  C: "idle",
  D: "idle",
  synth: "idle",
};

export function LiveReplay({ bundle }: { bundle: RunBundle }) {
  const [slots, setSlots] = useState<Slots>({});
  const [states, setStates] = useState<States>(INITIAL_STATES);
  const [started, setStarted] = useState(false);
  const [finished, setFinished] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  const totals = useMemo(
    () => ({
      cost: bundle.signal.total_cost_usd ?? null,
      wall: bundle.signal.total_runtime_sec ?? null,
    }),
    [bundle],
  );

  useEffect(() => {
    return () => {
      esRef.current?.close();
    };
  }, []);

  function start(speed: number) {
    if (esRef.current) esRef.current.close();
    setSlots({});
    setStates(INITIAL_STATES);
    setFinished(false);
    setStarted(true);

    const url = `/api/replay/${bundle.report_id}?speed=${speed}`;
    const es = new EventSource(url);
    esRef.current = es;

    const handle = (raw: MessageEvent) => {
      const ev = JSON.parse(raw.data) as ReplayEvent;
      if (ev.type === "agent_start") {
        setStates((s) => ({ ...s, [ev.agent]: "running" }));
      } else if (ev.type === "agent_done") {
        setStates((s) => ({ ...s, [ev.agent]: "done" }));
        setSlots((prev) => ({ ...prev, [ev.agent]: ev.payload }));
      } else if (ev.type === "synthesis_start") {
        setStates((s) => ({ ...s, synth: "running" }));
      } else if (ev.type === "synthesis_done") {
        setStates((s) => ({ ...s, synth: "done" }));
        setSlots((prev) => ({ ...prev, signal: ev.payload }));
      } else if (ev.type === "end") {
        setFinished(true);
        es.close();
      }
    };

    for (const t of [
      "bootstrap",
      "agent_start",
      "agent_done",
      "synthesis_start",
      "synthesis_done",
      "end",
    ]) {
      es.addEventListener(t, handle as EventListener);
    }
    es.onerror = () => {
      es.close();
    };
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => start(1)}
            className="rounded-md border border-[var(--color-accent)] bg-[color:color-mix(in_oklab,var(--color-accent)_15%,transparent)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] hover:bg-[color:color-mix(in_oklab,var(--color-accent)_25%,transparent)] transition-colors"
          >
            {started && !finished ? "Restart" : started ? "Replay again" : "▶ Replay this triage"}
          </button>
          <button
            type="button"
            onClick={() => start(2)}
            className="rounded-md border border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-ink-dim)] hover:text-[var(--color-ink)] transition-colors"
          >
            2× speed
          </button>
          <button
            type="button"
            onClick={() => start(0.5)}
            className="rounded-md border border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-ink-dim)] hover:text-[var(--color-ink)] transition-colors"
          >
            0.5× speed
          </button>
        </div>
        <div className="text-xs text-[var(--color-ink-faint)]">
          {totals.wall != null && totals.cost != null ? (
            <span>
              original run: {totals.wall.toFixed(1)}s · ${totals.cost.toFixed(2)} ·
              Opus 4.7 ×4 @ xhigh
            </span>
          ) : (
            <span>Opus 4.7 ×4 @ xhigh</span>
          )}
        </div>
      </div>

      <section>
        <h2 className="mb-3 text-xs uppercase tracking-widest text-[var(--color-ink-dim)]">
          Sub-agents (parallel)
        </h2>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <AgentCard
            slot="A"
            title="Reproducibility"
            subtitle="Docker + ASan sandbox"
            state={states.A}
            payload={slots.A}
          />
          <AgentCard
            slot="B"
            title="Root cause"
            subtitle="Source verification"
            state={states.B}
            payload={slots.B}
          />
          <AgentCard
            slot="C"
            title="Duplicate"
            subtitle="NVD + vendor advisories"
            state={states.C}
            payload={slots.C}
          />
          <AgentCard
            slot="D"
            title="Hallucination"
            subtitle="Cite-or-reject every ref"
            state={states.D}
            payload={slots.D}
          />
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-xs uppercase tracking-widest text-[var(--color-ink-dim)]">
          Synthesizer
        </h2>
        <SignalCard
          state={states.synth}
          signal={slots.signal}
          allAgentsDone={
            states.A === "done" &&
            states.B === "done" &&
            states.C === "done" &&
            states.D === "done"
          }
        />
      </section>
    </div>
  );
}
