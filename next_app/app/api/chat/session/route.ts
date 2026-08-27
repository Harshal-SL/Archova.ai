import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';

// GET /api/chat/session?user_id=xxx  → list sessions
// POST /api/chat/session             → create session
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get('user_id')?.trim();

  if (!userId) {
    return NextResponse.json({ error: 'user_id is required.' }, { status: 400 });
  }

  const { data, error } = await supabase
    .from('chat_sessions')
    .select('id, title, created_at, user_id')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(50);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ sessions: data ?? [] }, { status: 200 });
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { user_id?: string; title?: string };
    const userId = body.user_id?.trim();
    const title = body.title?.trim() ?? 'New Design';

    if (!userId) {
      return NextResponse.json({ error: 'user_id is required.' }, { status: 400 });
    }

    const { data, error } = await supabase
      .from('chat_sessions')
      .insert([{ user_id: userId, title }])
      .select()
      .single();

    if (error) {
      const status = error.code === '23503' ? 400 : 500;
      return NextResponse.json({ error: error.message }, { status });
    }

    return NextResponse.json({ session: data }, { status: 201 });
  } catch {
    return NextResponse.json({ error: 'Unexpected server error.' }, { status: 500 });
  }
}

// PATCH /api/chat/session  → update title
export async function PATCH(request: Request) {
  try {
    const body = (await request.json()) as { session_id?: string; title?: string };
    const sessionId = body.session_id?.trim();
    const title = body.title?.trim();

    if (!sessionId || !title) {
      return NextResponse.json({ error: 'session_id and title are required.' }, { status: 400 });
    }

    const { error } = await supabase
      .from('chat_sessions')
      .update({ title })
      .eq('id', sessionId);

    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json({ ok: true }, { status: 200 });
  } catch {
    return NextResponse.json({ error: 'Unexpected server error.' }, { status: 500 });
  }
}
