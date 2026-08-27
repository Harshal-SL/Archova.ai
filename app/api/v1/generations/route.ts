import { NextResponse } from "next/server";
import { createGenerationSession } from "@/lib/engine/session-store";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const prompt = typeof body?.prompt === "string" ? body.prompt.trim() : "";

    if (!prompt) {
      return NextResponse.json(
        { detail: "Prompt is required to start architecture generation." },
        { status: 400 }
      );
    }

    const session = createGenerationSession(prompt);
    const firstQ = session.questions[0] || null;

    return NextResponse.json({
      generation_id: session.generation_id,
      status: session.status,
      current_question: firstQ,
    });
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : "Failed to initialize generation session." },
      { status: 500 }
    );
  }
}
