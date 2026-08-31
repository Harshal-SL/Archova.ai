-- Migration to create chat_sessions and messages tables for ArchAI

-- 1. Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  title TEXT NOT NULL DEFAULT 'New Architecture Session',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index on user_id for quick retrieval of user's chat history
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);

-- 2. Create messages table
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  json_response JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index on session_id for quick message lookups
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);

-- Enable Row Level Security (RLS)
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Allow read & write access for authenticated users / anon access for development
DROP POLICY IF EXISTS "Public access to chat_sessions" ON chat_sessions;
CREATE POLICY "Public access to chat_sessions" ON chat_sessions
  FOR ALL
  USING (TRUE)
  WITH CHECK (TRUE);

DROP POLICY IF EXISTS "Public access to messages" ON messages;
CREATE POLICY "Public access to messages" ON messages
  FOR ALL
  USING (TRUE)
  WITH CHECK (TRUE);
