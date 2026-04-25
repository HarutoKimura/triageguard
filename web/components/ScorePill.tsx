import type { SignalLabel } from "@/lib/types";

const STYLE: Record<SignalLabel, { bg: string; fg: string; border: string }> = {
  SIGNAL: {
    bg: "bg-[color:color-mix(in_oklab,var(--color-signal)_15%,transparent)]",
    fg: "text-[var(--color-signal)]",
    border: "border-[color:color-mix(in_oklab,var(--color-signal)_50%,transparent)]",
  },
  SLOP: {
    bg: "bg-[color:color-mix(in_oklab,var(--color-slop)_15%,transparent)]",
    fg: "text-[var(--color-slop)]",
    border: "border-[color:color-mix(in_oklab,var(--color-slop)_50%,transparent)]",
  },
  UNCERTAIN: {
    bg: "bg-[color:color-mix(in_oklab,var(--color-uncertain)_15%,transparent)]",
    fg: "text-[var(--color-uncertain)]",
    border: "border-[color:color-mix(in_oklab,var(--color-uncertain)_50%,transparent)]",
  },
  ERRORED: {
    bg: "bg-[var(--color-panel-2)]",
    fg: "text-[var(--color-ink-dim)]",
    border: "border-[var(--color-border)]",
  },
};

const STAMP_GLYPH: Record<SignalLabel, string> = {
  SIGNAL: "✓",
  SLOP: "✕",
  UNCERTAIN: "?",
  ERRORED: "!",
};

export function ScorePill({
  label,
  score,
  size = "md",
}: {
  label: SignalLabel;
  score: number;
  size?: "sm" | "md" | "lg";
}) {
  const s = STYLE[label];
  const dims =
    size === "lg"
      ? "px-4 py-2 text-base"
      : size === "sm"
        ? "px-2 py-0.5 text-[11px]"
        : "px-3 py-1 text-xs";
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border font-mono tracking-wide ${s.bg} ${s.fg} ${s.border} ${dims}`}
    >
      <span>{label}</span>
      <span className="opacity-80">{score}</span>
    </span>
  );
}

/**
 * Verdict stamp — the hero element on the run page.
 * Renders like a rubber stamp pressed onto a document, with the score as the
 * primary glyph. Used in SignalCard at size="lg".
 */
export function VerdictStamp({
  label,
  score,
  rule,
}: {
  label: SignalLabel;
  score: number;
  rule?: number | string;
}) {
  const s = STYLE[label];
  const glyph = STAMP_GLYPH[label];
  return (
    <div
      className={`tg-stamp inline-flex flex-col items-center justify-center gap-0.5 rounded-md border-2 px-5 py-3 font-mono uppercase ${s.bg} ${s.fg} ${s.border}`}
      style={{
        letterSpacing: "0.18em",
        boxShadow:
          "inset 0 0 0 1px color-mix(in oklab, currentColor 30%, transparent)",
      }}
    >
      <div className="flex items-center gap-2 text-xs">
        <span aria-hidden>{glyph}</span>
        <span>{label}</span>
      </div>
      <div className="text-3xl font-bold leading-none tracking-tight">
        {score}
      </div>
      {rule != null && (
        <div className="text-[9px] tracking-[0.25em] opacity-70">
          rule {rule}
        </div>
      )}
    </div>
  );
}
