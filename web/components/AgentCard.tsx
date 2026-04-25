import type {
  DuplicateArtifact,
  HallucinationArtifact,
  ReproArtifact,
  RootCauseArtifact,
} from "@/lib/types";

type Slot = "A" | "B" | "C" | "D";
type AgentState = "idle" | "running" | "done";

type Payload =
  | ReproArtifact
  | RootCauseArtifact
  | DuplicateArtifact
  | HallucinationArtifact;

interface Props {
  slot: Slot;
  title: string;
  subtitle: string;
  state: AgentState;
  payload: Payload | undefined;
}

const VERDICT_TONE: Record<string, "good" | "bad" | "warn" | "neutral"> = {
  reproduced: "good",
  match: "good",
  novel: "good",
  failed_to_reproduce: "bad",
  no_poc: "warn",
  build_error: "bad",
  timeout: "bad",
  partial_match: "warn",
  mismatch: "bad",
  file_not_found: "bad",
  duplicate: "warn",
  similar: "warn",
};

function toneClass(tone: "good" | "bad" | "warn" | "neutral") {
  switch (tone) {
    case "good":
      return "text-[var(--color-signal)]";
    case "bad":
      return "text-[var(--color-slop)]";
    case "warn":
      return "text-[var(--color-uncertain)]";
    default:
      return "text-[var(--color-ink)]";
  }
}

function StatusDot({ state }: { state: AgentState }) {
  if (state === "done") {
    return (
      <span
        aria-label="done"
        className="inline-block size-2 rounded-full bg-[var(--color-signal)]"
      />
    );
  }
  if (state === "running") {
    return (
      <span
        aria-label="running"
        className="tg-pulse inline-block size-2 rounded-full bg-[var(--color-accent)]"
      />
    );
  }
  return (
    <span
      aria-label="idle"
      className="inline-block size-2 rounded-full bg-[var(--color-ink-faint)]"
    />
  );
}

export function AgentCard({ slot, title, subtitle, state, payload }: Props) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-4 flex flex-col min-h-56">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex size-6 items-center justify-center rounded-md bg-[var(--color-panel-2)] text-xs font-mono text-[var(--color-ink-dim)]">
            {slot}
          </span>
          <div>
            <div className="text-sm font-medium">{title}</div>
            <div className="text-[11px] text-[var(--color-ink-faint)]">{subtitle}</div>
          </div>
        </div>
        <StatusDot state={state} />
      </div>

      <div className="mt-3 flex-1">
        {state === "idle" && (
          <div className="text-xs text-[var(--color-ink-faint)]">queued</div>
        )}
        {state === "running" && (
          <div className="text-xs text-[var(--color-ink-dim)] tg-pulse">
            …working
          </div>
        )}
        {state === "done" && payload && (
          <div className="tg-fade-in">
            <AgentBody slot={slot} payload={payload} />
          </div>
        )}
      </div>
    </div>
  );
}

function AgentBody({ slot, payload }: { slot: Slot; payload: Payload }) {
  if (slot === "A") return <ReproBody a={payload as ReproArtifact} />;
  if (slot === "B") return <RootCauseBody b={payload as RootCauseArtifact} />;
  if (slot === "C") return <DuplicateBody c={payload as DuplicateArtifact} />;
  return <HallucinationBody d={payload as HallucinationArtifact} />;
}

function VerdictLine({
  verdict,
  confidence,
}: {
  verdict: string;
  confidence: number;
}) {
  const tone = VERDICT_TONE[verdict] ?? "neutral";
  return (
    <div className="flex items-baseline justify-between">
      <span className={`font-mono text-sm ${toneClass(tone)}`}>{verdict}</span>
      <span className="text-[11px] text-[var(--color-ink-faint)]">
        conf {(confidence * 100).toFixed(0)}%
      </span>
    </div>
  );
}

function ReproBody({ a }: { a: ReproArtifact }) {
  const frames = (a.evidence.sanitizer_frames ?? []).slice(0, 3);
  const san = a.evidence.sanitizer_summary ?? null;
  return (
    <div className="space-y-2">
      <VerdictLine verdict={a.verdict} confidence={a.confidence} />
      {a.evidence.target_tag && (
        <div className="text-[11px] font-mono text-[var(--color-ink-dim)]">
          tag {a.evidence.target_tag}
        </div>
      )}
      {a.evidence.poc_signal && (
        <div className="text-[11px] text-[var(--color-ink-dim)]">
          PoC exit {a.evidence.poc_exit_code} ·{" "}
          <span className="text-[var(--color-slop)] font-mono">
            {a.evidence.poc_signal}
          </span>
        </div>
      )}
      {san && (
        <div className="text-[11px] leading-snug text-[var(--color-ink-dim)] line-clamp-3">
          {san}
        </div>
      )}
      {frames.length > 0 && (
        <div className="tg-crt rounded-md border border-[var(--color-border-strong)] p-2 font-mono text-[10px] leading-4">
          {frames.map((f, i) => {
            const isError = /error|overflow|invalid|crash/i.test(f);
            const isAddr = /0x[0-9a-f]+/i.test(f);
            const color = isError
              ? "var(--color-terminal-red)"
              : isAddr
                ? "var(--color-terminal-amber)"
                : "var(--color-terminal-green)";
            return (
              <div key={i} className="truncate" style={{ color }}>
                {f}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function RootCauseBody({ b }: { b: RootCauseArtifact }) {
  const verified = b.claims_checked.filter((c) => c.status === "verified").length;
  const total = b.claims_checked.length;
  const first = b.claims_checked[0];
  return (
    <div className="space-y-2">
      <VerdictLine verdict={b.match} confidence={b.confidence} />
      <div className="text-[11px] text-[var(--color-ink-dim)]">
        {verified}/{total} claims verified in source
      </div>
      {first && (
        <div className="rounded-md border border-[var(--color-border)] bg-[var(--color-panel-2)] p-2">
          <div className="text-[11px] leading-snug text-[var(--color-ink)] line-clamp-2">
            {first.claim}
          </div>
          {first.file && (
            <div className="mt-1 font-mono text-[10px] text-[var(--color-ink-faint)]">
              {first.file}
              {first.line_start ? `:${first.line_start}` : ""}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DuplicateBody({ c }: { c: DuplicateArtifact }) {
  return (
    <div className="space-y-2">
      <VerdictLine verdict={c.verdict} confidence={c.confidence} />
      <div className="text-[11px] text-[var(--color-ink-dim)]">
        queried {c.queried_databases.length > 0 ? c.queried_databases.join(", ") : "—"}
      </div>
      {c.matched_cve ? (
        <div className="font-mono text-[11px] text-[var(--color-uncertain)]">
          matches {c.matched_cve}
        </div>
      ) : (
        <div className="text-[11px] text-[var(--color-ink-faint)]">
          no prior disclosure found
        </div>
      )}
    </div>
  );
}

function HallucinationBody({ d }: { d: HallucinationArtifact }) {
  const invalidCount = d.stats.invalid;
  const headline =
    invalidCount === 0 ? "no fabrications" : `${invalidCount} invalid ref${invalidCount === 1 ? "" : "s"}`;
  const tone = invalidCount === 0 ? "good" : "bad";
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <span className={`font-mono text-sm ${toneClass(tone)}`}>{headline}</span>
        <span className="text-[11px] text-[var(--color-ink-faint)]">
          {d.stats.verified}/{d.stats.total} verified
        </span>
      </div>
      {d.invalid_refs.length > 0 ? (
        <ul className="space-y-1">
          {d.invalid_refs.slice(0, 3).map((r, i) => (
            <li
              key={i}
              className="rounded-md border border-[color:color-mix(in_oklab,var(--color-slop)_35%,transparent)] bg-[color:color-mix(in_oklab,var(--color-slop)_10%,transparent)] p-2"
            >
              <div className="font-mono text-[10px] text-[var(--color-slop)]">
                <span className="text-[var(--color-ink-faint)]">{r.kind}</span>
                <span className="mx-1">·</span>
                <span
                  className="tg-strike"
                  style={{ animationDelay: `${0.15 + i * 0.18}s` }}
                >
                  {r.value}
                </span>
              </div>
              {r.note && (
                <div className="mt-0.5 text-[10px] leading-snug text-[var(--color-ink-dim)] line-clamp-2">
                  {r.note}
                </div>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <div className="text-[11px] text-[var(--color-ink-faint)]">
          every cited function/file/line resolved in source
        </div>
      )}
    </div>
  );
}
