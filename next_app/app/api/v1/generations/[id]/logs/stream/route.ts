import { NextResponse } from "next/server";
import { getGenerationSession, type LogEntry } from "@/lib/engine/session-store";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const session = getGenerationSession(id);

  if (!session) {
    return NextResponse.json(
      { detail: "Generation session not found" },
      { status: 404 }
    );
  }

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      // 1. Replay historical logs first
      for (const log of session.logs) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(log)}\n\n`));
      }

      // 2. Subscriber for real-time logs
      const subscriber = (newLog: LogEntry) => {
        try {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(newLog)}\n\n`));
        } catch {
          // Stream closed
        }
      };

      session.log_subscribers.add(subscriber);

      // 3. Keepalive interval
      const interval = setInterval(() => {
        try {
          controller.enqueue(encoder.encode(": keepalive\n\n"));
        } catch {
          clearInterval(interval);
          session.log_subscribers.delete(subscriber);
        }
      }, 15000);

      // Clean up if request signals abort
      request.signal.addEventListener("abort", () => {
        clearInterval(interval);
        session.log_subscribers.delete(subscriber);
      });
    },
    cancel() {
      // Stream cancelled by client
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
