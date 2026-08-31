import { NextResponse } from "next/server";
import { getGenerationSession, type LldType } from "@/lib/engine/session-store";
import { generateLldSpecification } from "@/lib/engine/lld";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string; type: string }> }
) {
  try {
    const { id, type } = await params;
    const session = getGenerationSession(id);

    if (!session) {
      return NextResponse.json(
        { detail: "Generation session not found" },
        { status: 404 }
      );
    }

    const t = type.toLowerCase() as LldType;
    const validTypes: LldType[] = ["backend", "frontend", "database", "security", "cloud"];

    if (!validTypes.includes(t)) {
      return NextResponse.json(
        {
          detail: `Invalid LLD type '${type}'. Valid options: ${validTypes.join(", ")}`,
        },
        { status: 400 }
      );
    }

    const status = session.lld_status[t] || "NOT_STARTED";
    let data = session.lld_data[t];

    if (status === "READY" && data) {
      return NextResponse.json({
        status: "READY",
        lld_type: t,
        data,
      });
    }

    // If architecture is completed and data is not generated yet, generate immediately
    if (session.arsrs && session.hld && !data) {
      data = generateLldSpecification(
        t,
        session.prompt,
        session.arsrs,
        session.hld ? { ...session.hld } : {}
      );
      session.lld_data[t] = data;
      session.lld_status[t] = "READY";

      return NextResponse.json({
        status: "READY",
        lld_type: t,
        data,
      });
    }

    return NextResponse.json({
      status,
      lld_type: t,
      data,
      message: `${t.toUpperCase()} LLD is ${status.toLowerCase()}.`,
    });
  } catch (err) {
    return NextResponse.json(
      { detail: err instanceof Error ? err.message : "Failed to retrieve LLD." },
      { status: 500 }
    );
  }
}
