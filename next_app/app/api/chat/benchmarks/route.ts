import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';

// GET /api/chat/benchmarks?session_id=... OR ?user_id=...
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
      .from('architecture_benchmarks')
      .select('id, session_id, user_id, generation_id, model_id, model_name, is_archova, status, latency_ms, package_json, validation_json, comparison_json, created_at, updated_at');

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

    return NextResponse.json({ benchmarks: data ?? [] }, { status: 200 });
  } catch {
    return NextResponse.json(
      { error: 'Unexpected server error while fetching benchmark data.' },
      { status: 500 }
    );
  }
}

