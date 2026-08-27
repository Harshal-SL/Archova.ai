import { NextResponse } from "next/server";
import { sessionsDb } from "@/lib/engine/session-store";

export async function GET() {
  return NextResponse.json({
    status: "healthy",
    service: "ArchAI Architecture Engine (Next.js Native)",
    version: "2.0.0",
    active_sessions: sessionsDb.size,
  });
}
