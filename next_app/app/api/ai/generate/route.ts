import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';
import type { Node, Edge } from '@xyflow/react';

// ─── Types ───────────────────────────────────────────────────────────
type GenerateBody = {
  session_id?: string;
  message?: string;
  user_id?: string;
};

type OllamaResult = { response?: string; error?: string };

interface HLDNodeSpec {
  id: string;
  label: string;
  description?: string;
  x?: number;
  y?: number;
}

interface HLDEdgeSpec {
  source: string;
  target: string;
  label?: string;
}

interface LLDNodeSpec {
  id: string;
  label: string;
  details?: string;
  x?: number;
  y?: number;
}

interface LLDEdgeSpec { source: string; target: string; }

interface DesignJSON {
  summary: string;
  hld: {
    nodes: HLDNodeSpec[];
    edges: HLDEdgeSpec[];
  };
  lld: Record<string, {
    nodes: LLDNodeSpec[];
    edges: LLDEdgeSpec[];
  }>;
}

// ─── Constants ──────────────────────────────────────────────────────
const OLLAMA_URL = 'http://localhost:11434/api/generate';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL ?? 'mistral';

// ─── Prompt Builder ──────────────────────────────────────────────────
function buildPrompt(userInput: string): string {
  return `You are an expert system design AI. Given a user request, return ONLY a valid JSON object (no markdown, no explanation) matching this exact schema:

{
  "summary": "2-3 sentence conversational summary of the design",
  "hld": {
    "nodes": [
      { "id": "string (slug, e.g. api-server)", "label": "Display Name", "description": "brief role", "x": number, "y": number }
    ],
    "edges": [
      { "source": "node-id", "target": "node-id", "label": "optional" }
    ]
  },
  "lld": {
    "<hld-node-id>": {
      "nodes": [
        { "id": "string", "label": "Display Name", "details": "technical detail", "x": number, "y": number }
      ],
      "edges": [
        { "source": "node-id", "target": "node-id" }
      ]
    }
  }
}

Rules:
- Include 5-8 HLD nodes arranged in a logical flow (use x,y positions: spread across 0-600 x, 0-400 y)
- For each HLD node provide 3-5 LLD nodes with x,y positions (0-400 x, 0-300 y)
- edges must reference valid node ids
- JSON only, no markdown fences

User request: ${userInput}`;
}

// ─── Auto-layout fallback positions ─────────────────────────────────
function applyAutoLayout<T extends { x?: number; y?: number }>(
  items: T[],
  cols = 3,
  xStep = 200,
  yStep = 140
): (T & { x: number; y: number })[] {
  return items.map((item, i) => ({
    ...item,
    x: item.x ?? (i % cols) * xStep,
    y: item.y ?? Math.floor(i / cols) * yStep,
  }));
}

// ─── Convert DesignJSON → ReactFlow nodes/edges ──────────────────────
function buildGraphData(design: DesignJSON) {
  const hldNodes: Node[] = applyAutoLayout(design.hld.nodes, 3, 200, 150).map(
    (n) => ({
      id: n.id,
      type: 'default',
      data: { label: n.label, description: n.description ?? '' },
      position: { x: n.x, y: n.y },
      style: {},
    })
  );

  const hldEdges: Edge[] = design.hld.edges.map((e, i) => ({
    id: `hld-e-${i}`,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: true,
    style: {},
  }));

  const lldMap: Record<string, { nodes: Node[]; edges: Edge[] }> = {};
  for (const [nodeId, lld] of Object.entries(design.lld)) {
    const lldNodes: Node[] = applyAutoLayout(lld.nodes, 2, 200, 150).map(
      (n) => ({
        id: n.id,
        type: 'default',
        data: { label: n.label, details: n.details ?? '' },
        position: { x: n.x, y: n.y },
        style: {},
      })
    );
    const lldEdges: Edge[] = lld.edges.map((e, i) => ({
      id: `lld-${nodeId}-e-${i}`,
      source: e.source,
      target: e.target,
      animated: true,
      style: {},
    }));
    lldMap[nodeId] = { nodes: lldNodes, edges: lldEdges };
  }

  return { hldNodes, hldEdges, lldMap };
}

// ─── Parse + validate AI response ───────────────────────────────────
function parseDesign(raw: string): DesignJSON {
  // Strip markdown fences if model ignored instructions
  const cleaned = raw
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim();

  let parsed: unknown;
  try {
    parsed = JSON.parse(cleaned);
  } catch {
    // Try extracting first JSON object from response
    const match = cleaned.match(/\{[\s\S]*\}/);
    if (!match) throw new Error('No JSON object found in AI response.');
    parsed = JSON.parse(match[0]);
  }

  const d = parsed as Record<string, unknown>;
  if (!d.summary || !d.hld || !d.lld) {
    throw new Error('AI JSON missing required fields: summary, hld, or lld.');
  }
  return d as unknown as DesignJSON;
}

// ─── Ollama call ────────────────────────────────────────────────────
async function callOllama(prompt: string): Promise<string> {
  let res: Response;
  try {
    res = await fetch(OLLAMA_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: OLLAMA_MODEL, prompt, stream: false }),
    });
  } catch {
    throw new Error(
      'Ollama is unreachable. Make sure Ollama is running: `ollama serve`'
    );
  }

  const body = await res.text();
  if (!res.ok) {
    let msg = `Ollama error ${res.status}`;
    try { msg = (JSON.parse(body) as OllamaResult).error ?? msg; } catch { /* ignore */ }
    throw new Error(msg);
  }

  let parsed: OllamaResult;
  try { parsed = JSON.parse(body) as OllamaResult; } catch {
    throw new Error('Ollama returned unparseable response.');
  }
  const text = parsed.response?.trim();
  if (!text) throw new Error('Ollama response was empty.');
  return text;
}

// ─── POST handler ────────────────────────────────────────────────────
export async function POST(request: Request) {
  try {
    const body = (await request.json()) as GenerateBody;
    const sessionId = body.session_id?.trim();
    const userMessage = body.message?.trim();
    const userId = body.user_id?.trim();

    if (!sessionId || !userMessage) {
      return NextResponse.json(
        { error: 'session_id and message are required.' },
        { status: 400 }
      );
    }

    // 1. Persist user message to Supabase (best-effort, don't block on failure)
    if (userId) {
      await supabase.from('messages').insert([{
        session_id: sessionId,
        content: userMessage,
        role: 'user',
      }]).select().single();
    }

    // 2. Call Ollama
    let rawAI: string;
    try {
      rawAI = await callOllama(buildPrompt(userMessage));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Ollama error';
      const status = msg.includes('unreachable') ? 503 : 502;
      return NextResponse.json({ error: msg }, { status });
    }

    // 3. Parse structured design
    let design: DesignJSON;
    try {
      design = parseDesign(rawAI);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Parse error';
      return NextResponse.json({ error: msg }, { status: 502 });
    }

    // 4. Build graph data
    const { hldNodes, hldEdges, lldMap } = buildGraphData(design);

    // 5. Persist AI response to Supabase (best-effort)
    if (userId) {
      await supabase.from('messages').insert([{
        session_id: sessionId,
        content: design.summary,
        role: 'assistant',
        json_response: design,
      }]).select().single();
    }

    // 6. Return everything the frontend needs
    return NextResponse.json(
      {
        response: design.summary,
        architectureData: {
          hldNodes,
          hldEdges,
          lldMap,
          summaryText: design.summary,
        },
      },
      { status: 200 }
    );
  } catch {
    return NextResponse.json(
      { error: 'Unexpected server error.' },
      { status: 500 }
    );
  }
}
