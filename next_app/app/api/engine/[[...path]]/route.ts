import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

/**
 * Server-Side AI Engine Reverse Proxy Route Handler
 * 
 * Security Advantages:
 * 1. Absolute API Isolation: Browser DevTools and network traces only see internal requests to `/api/engine/...`.
 * 2. Secrets Protection: The backend host and internal URLs are stored in `AI_ENGINE_URL` (server-only, no NEXT_PUBLIC_ prefix).
 * 3. CORS Elimination: Requests are same-origin from the browser's perspective.
 */
async function handleProxy(req: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  try {
    const { path } = await context.params;
    const subPath = path && path.length > 0 ? path.join("/") : "";
    
    // Server-only variable prioritized, with graceful fallback
    const rawTarget = process.env.AI_ENGINE_URL || process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";
    const targetBase = rawTarget.trim().replace(/\/+$/, "");
    const search = req.nextUrl.search || "";
    
    // Construct destination URL
    const destinationUrl = subPath ? `${targetBase}/${subPath}${search}` : `${targetBase}/${search}`;

    // Filter and prepare headers to forward
    const forwardHeaders = new Headers();
    req.headers.forEach((value, key) => {
      const lower = key.toLowerCase();
      // Exclude hop-by-hop and host headers
      if (!["host", "connection", "content-length", "transfer-encoding"].includes(lower)) {
        forwardHeaders.set(key, value);
      }
    });

    const method = req.method.toUpperCase();
    const hasBody = !["GET", "HEAD", "OPTIONS"].includes(method);
    const body = hasBody ? await req.arrayBuffer() : undefined;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000); // 60s timeout for LLM synthesis

    const backendRes = await fetch(destinationUrl, {
      method,
      headers: forwardHeaders,
      body,
      signal: controller.signal,
      cache: "no-store",
    });

    clearTimeout(timeout);

    // Prepare response headers
    const responseHeaders = new Headers();
    backendRes.headers.forEach((value, key) => {
      const lower = key.toLowerCase();
      if (!["transfer-encoding", "content-encoding"].includes(lower)) {
        responseHeaders.set(key, value);
      }
    });

    return new Response(backendRes.body, {
      status: backendRes.status,
      statusText: backendRes.statusText,
      headers: responseHeaders,
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Proxy error connecting to backend service.";
    return NextResponse.json(
      {
        error: "AI_ENGINE_UNAVAILABLE",
        detail: errorMsg.includes("abort") ? "AI Engine request timed out." : "Architecture Engine is currently unreachable.",
      },
      { status: 503 }
    );
  }
}

export async function GET(req: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  return handleProxy(req, context);
}

export async function POST(req: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  return handleProxy(req, context);
}

export async function PUT(req: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  return handleProxy(req, context);
}

export async function DELETE(req: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  return handleProxy(req, context);
}

export async function PATCH(req: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  return handleProxy(req, context);
}
