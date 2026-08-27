import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';

type CreateSessionBody = {
  user_id?: string;
};

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateSessionBody;
    const userId = body.user_id?.trim();

    if (!userId) {
      return NextResponse.json(
        { error: 'user_id is required.' },
        { status: 400 }
      );
    }

    const { data, error } = await supabase
      .from('chat_sessions')
      .insert([{ user_id: userId }])
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
