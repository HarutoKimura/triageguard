import type { NextRequest } from "next/server";
import { loadRun } from "@/lib/findings";
import type { ReplayEvent } from "@/lib/types";

export const dynamic = "force-dynamic";

// Per-agent arrival offsets (ms) from t=0. Agents start simultaneously.
// Ordering reflects observed real-run timing: C finishes fastest, A last.
const ARRIVAL_MS: Record<"C" | "D" | "B" | "A", number> = {
  C: 2500,
  D: 4200,
  B: 6000,
  A: 8200,
};
const SYNTHESIS_DELAY_MS = 1200;

function encode(ev: ReplayEvent): Uint8Array {
  const payload = `event: ${ev.type}\ndata: ${JSON.stringify(ev)}\n\n`;
  return new TextEncoder().encode(payload);
}

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ reportId: string }> },
) {
  const { reportId } = await params;
  const bundle = await loadRun(reportId);
  if (!bundle) {
    return new Response(JSON.stringify({ error: "not_found" }), {
      status: 404,
      headers: { "content-type": "application/json" },
    });
  }

  const speed = Math.max(
    0.1,
    Math.min(10, Number(req.nextUrl.searchParams.get("speed") ?? "1")),
  );
  const scale = 1 / speed;

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      let cancelled = false;
      const timers: ReturnType<typeof setTimeout>[] = [];
      const schedule = (delayMs: number, fn: () => void) => {
        timers.push(setTimeout(fn, delayMs * scale));
      };

      controller.enqueue(
        encode({
          type: "bootstrap",
          report_id: bundle.report_id,
          sample_id: bundle.sample_id,
        }),
      );

      (["A", "B", "C", "D"] as const).forEach((agent) => {
        schedule(10, () => {
          if (!cancelled) controller.enqueue(encode({ type: "agent_start", agent }));
        });
      });

      schedule(ARRIVAL_MS.C, () => {
        if (cancelled) return;
        controller.enqueue(
          encode({ type: "agent_done", agent: "C", payload: bundle.duplicate }),
        );
      });
      schedule(ARRIVAL_MS.D, () => {
        if (cancelled) return;
        controller.enqueue(
          encode({
            type: "agent_done",
            agent: "D",
            payload: bundle.hallucination,
          }),
        );
      });
      schedule(ARRIVAL_MS.B, () => {
        if (cancelled) return;
        controller.enqueue(
          encode({ type: "agent_done", agent: "B", payload: bundle.root_cause }),
        );
      });
      schedule(ARRIVAL_MS.A, () => {
        if (cancelled) return;
        controller.enqueue(
          encode({ type: "agent_done", agent: "A", payload: bundle.repro }),
        );
      });

      const lastAgentAt = Math.max(...Object.values(ARRIVAL_MS));
      schedule(lastAgentAt + 200, () => {
        if (cancelled) return;
        controller.enqueue(encode({ type: "synthesis_start" }));
      });
      schedule(lastAgentAt + 200 + SYNTHESIS_DELAY_MS, () => {
        if (cancelled) return;
        controller.enqueue(
          encode({ type: "synthesis_done", payload: bundle.signal }),
        );
        controller.enqueue(encode({ type: "end" }));
        controller.close();
      });

      req.signal.addEventListener("abort", () => {
        cancelled = true;
        for (const t of timers) clearTimeout(t);
        try {
          controller.close();
        } catch {
          /* already closed */
        }
      });
    },
  });

  return new Response(stream, {
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
      connection: "keep-alive",
      "x-accel-buffering": "no",
    },
  });
}
