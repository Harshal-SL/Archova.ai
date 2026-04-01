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

const OLLAMA_URL = 'http://localhost:11434/api/generate';

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

    let aiResponse: string;

    try {
      aiResponse = await generateWithOllama(userMessage);
    } catch (ollamaError) {
      const message =
        ollamaError instanceof Error
          ? ollamaError.message
          : 'Unexpected error while generating AI response.';

      const status = message.includes('unavailable') ? 503 : 502;
      return NextResponse.json({ error: message }, { status });
    }

    const { data, error } = await supabase
      .from('messages')
      .insert([{
        session_id: sessionId,
        content: aiResponse,
        role: 'assistant',
      }])
      .select()
      .single();

    if (error) {
      const status = error.code === '23503' ? 400 : 500;
      return NextResponse.json({ error: error.message }, { status });
    }

    return NextResponse.json(
      {
        response: aiResponse,
        message: data,
      },
      { status: 201 }
    );
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body or unexpected server error.' },
      { status: 500 }
    );
  }
}
