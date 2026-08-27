import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';

type LoginBody = {
  email?: string;
  password?: string;
};

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as LoginBody;
    const email = body.email?.trim();
    const password = body.password;

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required.' },
        { status: 400 }
      );
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Please provide a valid email address.' },
        { status: 400 }
      );
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      const status = error.status ?? 401;
      return NextResponse.json({ error: error.message }, { status });
    }

    return NextResponse.json(
      {
        message: 'Login successful.',
        user: data.user,
        session: data.session,
      },
      { status: 200 }
    );
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body or unexpected server error.' },
      { status: 500 }
    );
  }
}
