-- =================================================================
-- Migration: 20261028000000_secure_rls_policies.sql
-- Description: Enforce strict Row Level Security (RLS) across all tables.
-- Eliminates insecure public policies, prevents unauthorized access,
-- wraps auth.uid() in (select auth.uid()) for optimal query execution,
-- and creates necessary indexes on RLS filter columns.
-- =================================================================

-- ── 1. Secure public.architecture_designs ─────────────────────────
ALTER TABLE IF EXISTS public.architecture_designs ENABLE ROW LEVEL SECURITY;

-- Create index on user_id for RLS performance
CREATE INDEX IF NOT EXISTS idx_architecture_designs_user_id 
  ON public.architecture_designs (user_id);

DROP POLICY IF EXISTS "Public access to architecture_designs" ON public.architecture_designs;
DROP POLICY IF EXISTS "Users can view own architecture designs" ON public.architecture_designs;
CREATE POLICY "Users can view own architecture designs" ON public.architecture_designs
  FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own architecture designs" ON public.architecture_designs;
CREATE POLICY "Users can insert own architecture designs" ON public.architecture_designs
  FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own architecture designs" ON public.architecture_designs;
CREATE POLICY "Users can update own architecture designs" ON public.architecture_designs
  FOR UPDATE
  TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own architecture designs" ON public.architecture_designs;
CREATE POLICY "Users can delete own architecture designs" ON public.architecture_designs
  FOR DELETE
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);


-- ── 2. Secure public.chat_sessions ────────────────────────────────
-- Note: chat_sessions.user_id is TEXT in production schema
ALTER TABLE IF EXISTS public.chat_sessions ENABLE ROW LEVEL SECURITY;

-- Create index on user_id for RLS performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id 
  ON public.chat_sessions (user_id);

-- Drop any previous insecure public policies
DROP POLICY IF EXISTS "Public access to chat_sessions" ON public.chat_sessions;
DROP POLICY IF EXISTS "Users can view own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can view own chat sessions" ON public.chat_sessions
  FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid())::text = user_id);

DROP POLICY IF EXISTS "Users can insert own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can insert own chat sessions" ON public.chat_sessions
  FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid())::text = user_id);

DROP POLICY IF EXISTS "Users can update own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can update own chat sessions" ON public.chat_sessions
  FOR UPDATE
  TO authenticated
  USING ((SELECT auth.uid())::text = user_id)
  WITH CHECK ((SELECT auth.uid())::text = user_id);

DROP POLICY IF EXISTS "Users can delete own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can delete own chat sessions" ON public.chat_sessions
  FOR DELETE
  TO authenticated
  USING ((SELECT auth.uid())::text = user_id);


-- ── 3. Secure public.messages ─────────────────────────────────────
-- Note: messages.session_id is TEXT, chat_sessions.id is TEXT, chat_sessions.user_id is TEXT
ALTER TABLE IF EXISTS public.messages ENABLE ROW LEVEL SECURITY;

-- Create index on session_id for nested RLS lookup performance
CREATE INDEX IF NOT EXISTS idx_messages_session_id 
  ON public.messages (session_id);

-- Drop any previous insecure public policies
DROP POLICY IF EXISTS "Public access to messages" ON public.messages;
DROP POLICY IF EXISTS "Users can view own session messages" ON public.messages;
CREATE POLICY "Users can view own session messages" ON public.messages
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.chat_sessions
      WHERE chat_sessions.id = messages.session_id
        AND chat_sessions.user_id = (SELECT auth.uid())::text
    )
  );

DROP POLICY IF EXISTS "Users can insert own session messages" ON public.messages;
CREATE POLICY "Users can insert own session messages" ON public.messages
  FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.chat_sessions
      WHERE chat_sessions.id = messages.session_id
        AND chat_sessions.user_id = (SELECT auth.uid())::text
    )
  );

DROP POLICY IF EXISTS "Users can update own session messages" ON public.messages;
CREATE POLICY "Users can update own session messages" ON public.messages
  FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.chat_sessions
      WHERE chat_sessions.id = messages.session_id
        AND chat_sessions.user_id = (SELECT auth.uid())::text
    )
  );

DROP POLICY IF EXISTS "Users can delete own session messages" ON public.messages;
CREATE POLICY "Users can delete own session messages" ON public.messages
  FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.chat_sessions
      WHERE chat_sessions.id = messages.session_id
        AND chat_sessions.user_id = (SELECT auth.uid())::text
    )
  );


-- ── 4. Secure public.users ────────────────────────────────────────
-- Note: users.id is UUID
ALTER TABLE IF EXISTS public.users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public can view users" ON public.users;
DROP POLICY IF EXISTS "Users can insert their own data" ON public.users;
DROP POLICY IF EXISTS "Users can update their own data" ON public.users;
DROP POLICY IF EXISTS "Users can view own user record" ON public.users;
DROP POLICY IF EXISTS "Users can insert own user record" ON public.users;
DROP POLICY IF EXISTS "Users can update own user record" ON public.users;

CREATE POLICY "Users can view own user record" ON public.users
  FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = id);

CREATE POLICY "Users can insert own user record" ON public.users
  FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid()) = id);

CREATE POLICY "Users can update own user record" ON public.users
  FOR UPDATE
  TO authenticated
  USING ((SELECT auth.uid()) = id)
  WITH CHECK ((SELECT auth.uid()) = id);
