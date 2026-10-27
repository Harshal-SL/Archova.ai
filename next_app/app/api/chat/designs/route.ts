import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';

// GET /api/chat/designs?session_id=... OR ?user_id=...
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get('session_id')?.trim();
    const userId = searchParams.get('user_id')?.trim();

    if (!sessionId && !userId) {
      return NextResponse.json(
        { error: 'Either session_id or user_id query parameter is required.' },
        { status: 400 }
      );
    }

    let query = supabase
      .from('architecture_designs')
      .select('id, session_id, user_id, prompt, design_json, version, version_tag, parent_id, diff, is_latest, created_at, updated_at');

    if (sessionId) {
      query = query.eq('session_id', sessionId);
    }
    if (userId) {
      query = query.eq('user_id', userId);
    }

    const { data, error } = await query.order('created_at', { ascending: false });

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ designs: data ?? [] }, { status: 200 });
  } catch {
    return NextResponse.json(
      { error: 'Unexpected server error while fetching designs.' },
      { status: 500 }
    );
  }
}
