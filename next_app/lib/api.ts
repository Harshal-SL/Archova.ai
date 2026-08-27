/**
 * api.ts – Typed API client for all backend interactions
 */

import type { ArchitectureData } from './store';

// ─── Auth ─────────────────────────────────────────────────────────────

export interface AuthResponse {
  user?: { id: string; email: string };
  session?: { access_token: string };
  error?: string;
}

export async function apiLogin(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return res.json() as Promise<AuthResponse>;
}

export async function apiSignup(
  email: string,
  password: string,
  name?: string
): Promise<AuthResponse> {
  const res = await fetch('/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  });
  return res.json() as Promise<AuthResponse>;
}

// ─── Sessions ─────────────────────────────────────────────────────────

export interface DBSession {
  id: string;
  title: string;
  created_at: string;
  user_id: string;
}

export async function apiGetSessions(userId: string): Promise<DBSession[]> {
  const res = await fetch(`/api/chat/session?user_id=${encodeURIComponent(userId)}`);
  const data = (await res.json()) as { sessions?: DBSession[]; error?: string };
  if (!res.ok || !data.sessions) return [];
  return data.sessions;
}

export async function apiCreateSession(
  userId: string,
  title = 'New Design'
): Promise<DBSession | null> {
  const res = await fetch('/api/chat/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, title }),
  });
  const data = (await res.json()) as { session?: DBSession; error?: string };
  return data.session ?? null;
}

export async function apiUpdateSessionTitle(
  sessionId: string,
  title: string
): Promise<void> {
  await fetch('/api/chat/session', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, title }),
  });
}

// ─── Messages ─────────────────────────────────────────────────────────

export interface DBMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  json_response?: unknown;
  created_at: string;
}

export async function apiGetHistory(sessionId: string): Promise<DBMessage[]> {
  const res = await fetch(
    `/api/chat/history?session_id=${encodeURIComponent(sessionId)}`
  );
  const data = (await res.json()) as { messages?: DBMessage[]; error?: string };
  if (!res.ok || !data.messages) return [];
  return data.messages;
}

// ─── AI Generate ──────────────────────────────────────────────────────

export interface GenerateResponse {
  response?: string;
  architectureData?: ArchitectureData;
  error?: string;
}

export async function apiGenerate(
  sessionId: string,
  message: string,
  userId?: string
): Promise<GenerateResponse> {
  const res = await fetch('/api/ai/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      user_id: userId,
    }),
  });
  return res.json() as Promise<GenerateResponse>;
}
