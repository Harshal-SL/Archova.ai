-- =================================================================
-- Archova.ai Production Database Schema
-- Migration: 20261015000000_archova_production_schema.sql
-- Features:
-- 1. Stores user details & preferences
-- 2. Store user prompts and corresponding architecture design JSON (with GIN index & versioning)
-- 3. Manage multiple chats per user with sorting, titles, and cascade deletions
-- =================================================================

-- 1. Ensure uuid-ossp extension is enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Generic updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Enhance public.users
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{"theme": "dark"}'::jsonb;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- 4. Enhance public.chat_sessions
ALTER TABLE public.chat_sessions ADD COLUMN IF NOT EXISTS title TEXT NOT NULL DEFAULT 'New Architecture Session';
ALTER TABLE public.chat_sessions ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.chat_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_updated ON public.chat_sessions(user_id, updated_at DESC);

-- 5. Enhance public.messages
CREATE INDEX IF NOT EXISTS idx_messages_session_created ON public.messages(session_id, created_at ASC);

-- 6. Create architecture_designs table
CREATE TABLE IF NOT EXISTS public.architecture_designs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  prompt TEXT NOT NULL,
  design_json JSONB NOT NULL,
  version INT NOT NULL DEFAULT 1,
  is_latest BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_designs_session_id ON public.architecture_designs(session_id);
CREATE INDEX IF NOT EXISTS idx_designs_user_id ON public.architecture_designs(user_id);
CREATE INDEX IF NOT EXISTS idx_designs_jsonb ON public.architecture_designs USING gin (design_json);
