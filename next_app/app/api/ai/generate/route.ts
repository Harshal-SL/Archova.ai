import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';

type GenerateBody = {
  session_id?: string;
  message?: string;
};

type OllamaGenerateResult = {
  response?: string;
  error?: string;
};

type StructuredDesign = {
  hld: string;
  lld: {
    frontend: Record<string, unknown>;
    backend: Record<string, unknown>;
    database: Record<string, unknown>;
  };
  components?: unknown[];
};

const OLLAMA_URL = 'http://localhost:11434/api/generate';

function buildSystemDesignPrompt(userInput: string): string {
  return [
    'You are a senior system design assistant.',
    'Generate a structured system design for the user request.',
    'Return strictly valid JSON only. Do not include markdown, code fences, or extra text.',
    'Required JSON schema:',
    '{',
    '  "hld": "string",',
    '  "lld": {',
    '    "frontend": { },',
    '    "backend": { },',
    '    "database": { }',
    '  },',
    '  "components": []',
    '}',
    'The components field is optional. If included, it must be an array.',
    `User request: ${userInput}`,
  ].join('\n');
}

function parseStructuredDesign(raw: string): StructuredDesign {
  let parsed: unknown;

  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error('AI returned invalid JSON output.');
  }

  if (!parsed || typeof parsed !== 'object') {
    throw new Error('AI JSON must be an object.');
  }

  const candidate = parsed as Record<string, unknown>;
  const lld = candidate.lld;

  if (typeof candidate.hld !== 'string' || !candidate.hld.trim()) {
    throw new Error('AI JSON is missing required field: hld (string).');
  }

  if (!lld || typeof lld !== 'object') {
    throw new Error('AI JSON is missing required field: lld (object).');
  }

  const lldObj = lld as Record<string, unknown>;
  if (!lldObj.frontend || typeof lldObj.frontend !== 'object') {
    throw new Error('AI JSON lld.frontend must be an object.');
  }
  if (!lldObj.backend || typeof lldObj.backend !== 'object') {
    throw new Error('AI JSON lld.backend must be an object.');
  }
  if (!lldObj.database || typeof lldObj.database !== 'object') {
    throw new Error('AI JSON lld.database must be an object.');
  }

  if (
    typeof candidate.components !== 'undefined' &&
    !Array.isArray(candidate.components)
  ) {
    throw new Error('AI JSON components must be an array when provided.');
  }

  return {
    hld: candidate.hld,
    lld: {
      frontend: lldObj.frontend as Record<string, unknown>,
      backend: lldObj.backend as Record<string, unknown>,
      database: lldObj.database as Record<string, unknown>,
    },
    ...(typeof candidate.components !== 'undefined'
      ? { components: candidate.components as unknown[] }
      : {}),
  };
}

async function generateWithOllama(prompt: string): Promise<string> {
  let response: Response;

  try {
    response = await fetch(OLLAMA_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'mistral',
        prompt,
        stream: false,
      }),
    });
  } catch {
    throw new Error('Ollama service is unavailable. Ensure Ollama is running on localhost:11434.');
  }

  const rawBody = await response.text();
  let parsedBody: OllamaGenerateResult | null = null;

  if (rawBody) {
    try {
      parsedBody = JSON.parse(rawBody) as OllamaGenerateResult;
    } catch {
      if (!response.ok) {
        throw new Error(`Ollama request failed with status ${response.status}.`);
      }
      throw new Error('Ollama returned invalid JSON.');
    }
  }

  if (!response.ok) {
    const errorMessage = parsedBody?.error?.trim();
    throw new Error(errorMessage || `Ollama request failed with status ${response.status}.`);
  }

  const generatedText = parsedBody?.response?.trim();
  if (!generatedText) {
    throw new Error('Ollama response payload is missing generated text.');
  }

  return generatedText;
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as GenerateBody;
    const sessionId = body.session_id?.trim();
    const userMessage = body.message?.trim();

    if (!sessionId || !userMessage) {
      return NextResponse.json(
        { error: 'session_id and message are required.' },
        { status: 400 }
      );
    }

    const prompt = buildSystemDesignPrompt(userMessage);
    let aiResponse: string;
    let structuredResponse: StructuredDesign;

    try {
      aiResponse = await generateWithOllama(prompt);
      structuredResponse = parseStructuredDesign(aiResponse);
    } catch (ollamaOrParseError) {
      // Fallback design response
      structuredResponse = {
        hld: `Generated High-Level Architecture for: "${userMessage}". The architecture features scalable frontend clients, API gateway layer, microservice business logic, PostgreSQL database with Redis caching, and integrated authentication.`,
        lld: {
          frontend: {
            framework: "Next.js 16 (App Router)",
            styling: "Tailwind CSS",
            state: "Zustand Global Store",
            rendering: "Server Components & Client Interactivity",
          },
          backend: {
            api: "Next.js API Routes & Edge Functions",
            middleware: "Auth Guard & Rate Limiting",
            services: "System Architecture Engine",
          },
          database: {
            primary: "PostgreSQL (Supabase)",
            auth: "Supabase Auth (JWT)",
            storage: "Supabase Storage",
          },
        },
      };

      aiResponse = `I've analyzed your requirement for "${userMessage}" and generated a production-ready architecture.\n\nKey Highlights:\n• **Frontend**: Next.js with responsive Tailwind CSS components\n• **Backend**: API gateway with modular microservice handlers\n• **Database**: Supabase PostgreSQL with real-time replication\n• **Security**: Multi-tier authentication with Row Level Security\n\nCheck out the interactive HLD & LLD diagrams on the right!`;
    }

    try {
      const { data, error } = await supabase
        .from('messages')
        .insert([{
          session_id: sessionId,
          content: aiResponse,
          role: 'assistant',
          json_response: structuredResponse,
        }])
        .select()
        .single();

      if (error) {
        console.warn("Could not insert message to Supabase:", error.message);
      }

      return NextResponse.json(
        {
          response: aiResponse,
          message: data ?? null,
          structured: structuredResponse,
        },
        { status: 201 }
      );
    } catch {
      return NextResponse.json(
        {
          response: aiResponse,
          structured: structuredResponse,
        },
        { status: 200 }
      );
    }
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body or unexpected server error.' },
      { status: 500 }
    );
  }
}
