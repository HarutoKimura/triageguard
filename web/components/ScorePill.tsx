import type { SignalLabel } from "@/lib/types";

const VERDICT_COLOR: Record<SignalLabel, string> = {
  SIGNAL: "var(--color-signal)",
  SLOP: "var(--color-slop)",
  UNCERTAIN: "var(--color-uncertain)",
  ERRORED: "var(--color-ink-dim)",
};

const VERDICT_GLYPH: Record<SignalLabel, string> = {
  SIGNAL: "✓",
  SLOP: "✕",
  UNCERTAIN: "?",
  ERRORED: "!",
};

/**
 * ScorePill — the inline verdict mark used in lists and card corners.
 *
 * Deliberately NOT a pill. AI scaffolding defaults to rounded-full with a
 * tinted bg and same-color border (the Linear / shadcn / every-template
 * shape). We reject that. This is a "forensic mark": a vertical color rule,
 * a glyph, a small-caps label, and a bold score. No background. No border.
 * No rounding. The verdict is carried by typography and one accent stripe.
 */
export function ScorePill({
  label,
  score,
  size = "md",
}: {
  label: SignalLabel;
  score: number;
  size?: "sm" | "md" | "lg";
}) {
  const color = VERDICT_COLOR[label];
  const glyph = VERDICT_GLYPH[label];

  const dims =
    size === "lg"
      ? {
          rule: "border-l-[3px]",
          pad: "pl-3 py-1",
          glyph: "text-lg",
          label: "text-xs tracking-[0.22em]",
          score: "text-3xl",
        }
      : size === "sm"
        ? {
            rule: "border-l-2",
            pad: "pl-2 py-0.5",
            glyph: "text-[11px]",
            label: "text-[9px] tracking-[0.2em]",
            score: "text-sm",
          }
        : {
            rule: "border-l-2",
            pad: "pl-2.5 py-1",
            glyph: "text-sm",
            label: "text-[10px] tracking-[0.22em]",
            score: "text-xl",
          };

  return (
    <span
      className={`inline-flex items-baseline gap-2 font-mono uppercase ${dims.rule} ${dims.pad}`}
      style={{ borderLeftColor: color, color }}
    >
      <span aria-hidden className={`${dims.glyph} leading-none`}>
        {glyph}
      </span>
      <span className={`${dims.label} font-medium leading-none`}>{label}</span>
      <span className={`${dims.score} font-bold leading-none tracking-tight`}>
        {score}
      </span>
    </span>
  );
}

/**
 * VerdictStamp — hero element on the run page. Renders as a rubber stamp
 * pressed onto a document, with the score as the primary glyph. See
 * SignalCard for usage at hero size.
 */
const STAMP_GLYPH: Record<SignalLabel, string> = {
  SIGNAL: "✓",
  SLOP: "✕",
  UNCERTAIN: "?",
  ERRORED: "!",
};

const STAMP_STYLE: Record<
  SignalLabel,
  { bg: string; fg: string; border: string }
> = {
  SIGNAL: {
    bg: "bg-[color:color-mix(in_oklab,var(--color-signal)_15%,transparent)]",
    fg: "text-[var(--color-signal)]",
    border:
      "border-[color:color-mix(in_oklab,var(--color-signal)_50%,transparent)]",
  },
  SLOP: {
    bg: "bg-[color:color-mix(in_oklab,var(--color-slop)_15%,transparent)]",
    fg: "text-[var(--color-slop)]",
    border:
      "border-[color:color-mix(in_oklab,var(--color-slop)_50%,transparent)]",
  },
  UNCERTAIN: {
    bg: "bg-[color:color-mix(in_oklab,var(--color-uncertain)_15%,transparent)]",
    fg: "text-[var(--color-uncertain)]",
    border:
      "border-[color:color-mix(in_oklab,var(--color-uncertain)_50%,transparent)]",
  },
  ERRORED: {
    bg: "bg-[var(--color-panel-2)]",
    fg: "text-[var(--color-ink-dim)]",
    border: "border-[var(--color-border)]",
  },
};

export function VerdictStamp({
  label,
  score,
  rule,
}: {
  label: SignalLabel;
  score: number;
  rule?: number | string;
}) {
  const s = STAMP_STYLE[label];
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
