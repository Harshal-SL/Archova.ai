import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';

type CreateSessionBody = {
  user_id?: string;
  title?: string;
};

type UpdateSessionBody = {
  session_id?: string;
  title?: string;
  is_pinned?: boolean;
};

// GET /api/chat/session?user_id=...
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('user_id')?.trim();

    if (!userId) {
      return NextResponse.json(
        { error: 'user_id query parameter is required.' },
        { status: 400 }
      );
    }

    const { data, error } = await supabase
      .from('chat_sessions')
      .select('id, user_id, title, created_at, updated_at')
      .eq('user_id', userId)
      .order('updated_at', { ascending: false });

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ sessions: data ?? [] }, { status: 200 });
  } catch {
    return NextResponse.json(
      { error: 'Unexpected server error while fetching sessions.' },
      { status: 500 }
    );
  }
}

// POST /api/chat/session
export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateSessionBody;
    const userId = body.user_id?.trim();
    const title = body.title?.trim() || 'New Architecture Session';

    if (!userId) {
      return NextResponse.json(
        { error: 'user_id is required.' },
        { status: 400 }
      );
    }

    const { data, error } = await supabase
      .from('chat_sessions')
      .insert([
        {
          user_id: userId,
          title,
          updated_at: new Date().toISOString(),
        },
      ])
      .select()
      .single();

    if (error) {
      const status = error.code === '23503' ? 400 : 500;
      return NextResponse.json({ error: error.message }, { status });
    }

    return NextResponse.json({ session: data }, { status: 201 });
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body or unexpected server error.' },
      { status: 500 }
    );
  }
}

// PATCH /api/chat/session (Update title or pin status)
export async function PATCH(request: Request) {
  try {
    const body = (await request.json()) as UpdateSessionBody;
    const sessionId = body.session_id?.trim();

    if (!sessionId) {
      return NextResponse.json(
        { error: 'session_id is required.' },
        { status: 400 }
      );
    }

    const updates: Record<string, unknown> = {
      updated_at: new Date().toISOString(),
    };
    if (typeof body.title === 'string') updates.title = body.title.trim();
    if (typeof body.is_pinned === 'boolean') updates.is_pinned = body.is_pinned;

    const { data, error } = await supabase
      .from('chat_sessions')
      .update(updates)
      .eq('id', sessionId)
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ session: data }, { status: 200 });
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body or unexpected server error.' },
      { status: 500 }
    );
  }
}

// DELETE /api/chat/session?session_id=...
export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get('session_id')?.trim();

    if (!sessionId) {
      return NextResponse.json(
        { error: 'session_id query parameter is required.' },
        { status: 400 }
      );
    }

    const { error } = await supabase
      .from('chat_sessions')
      .delete()
      .eq('id', sessionId);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json(
      { message: 'Session deleted successfully.' },
      { status: 200 }
    );
  } catch {
    return NextResponse.json(
      { error: 'Unexpected server error while deleting session.' },
      { status: 500 }
    );
  }
}

