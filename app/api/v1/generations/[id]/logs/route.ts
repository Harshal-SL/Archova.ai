import { NextResponse } from "next/server";
import { getGenerationSession } from "@/lib/engine/session-store";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const session = getGenerationSession(id);

    if (!session) {
      return NextResponse.json(
        { detail: "Generation session not found" },
        { status: 404 }
      );
    }

    return NextResponse.json({
      generation_id: session.generation_id,
      logs: session.logs,
    });
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : "Failed to retrieve logs." },
      { status: 500 }
    );
  }
}
