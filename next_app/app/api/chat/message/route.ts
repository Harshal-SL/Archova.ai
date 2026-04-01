import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';

type CreateMessageBody = {
  session_id?: string;
  content?: string;
};

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateMessageBody;
    const sessionId = body.session_id?.trim();
    const content = body.content?.trim();

    if (!sessionId || !content) {
      return NextResponse.json(
        { error: 'session_id and content are required.' },
        { status: 400 }
      );
    }

    const { data, error } = await supabase
      .from('messages')
      .insert([{
        session_id: sessionId,
        content,
        role: 'user',
      }])
      .select()
      .single();

    if (error) {
      const status = error.code === '23503' ? 400 : 500;
      return NextResponse.json({ error: error.message }, { status });
    }

    return NextResponse.json({ message: data }, { status: 201 });
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body or unexpected server error.' },
      { status: 500 }
    );
  }
}
