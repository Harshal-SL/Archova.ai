import { NextResponse } from "next/server";
import { getGenerationSession, submitInterviewAnswer } from "@/lib/engine/session-store";

export async function POST(
  request: Request,
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

    const body = await request.json();
    const questionId = typeof body?.question_id === "string" ? body.question_id.trim() : "";
    const answer = typeof body?.answer === "string" ? body.answer.trim() : "";

    if (!questionId || !answer) {
      return NextResponse.json(
        { detail: "question_id and answer are required." },
        { status: 400 }
      );
    }

    const result = submitInterviewAnswer(session, questionId, answer);
    return NextResponse.json(result);
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : "Failed to submit interview answer." },
      { status: 500 }
    );
  }
}
