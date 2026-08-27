import { NextResponse } from "next/server";
import { getGenerationSession, generateArchitecture } from "@/lib/engine/session-store";

export async function POST(
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

    const result = await generateArchitecture(session);
    return NextResponse.json(result);
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : "Failed to generate architecture." },
      { status: 500 }
    );
  }
}
