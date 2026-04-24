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
      className={`inline-flex items-center gap-2 rounded-full border font-medium tracking-wide ${s.bg} ${s.fg} ${s.border} ${dims}`}
    >
      <span className="font-mono">{label}</span>
      <span className="opacity-80">{score}</span>
    </span>
  );
}
