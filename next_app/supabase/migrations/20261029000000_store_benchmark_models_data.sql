-- =================================================================
-- Migration: 20261029000000_store_benchmark_models_data.sql
-- Description: Create public.architecture_benchmarks table to store
-- all benchmark LLM models' generated architecture data (OpenAI GPT-4o,
-- Anthropic Claude 3.5 Sonnet, Google Gemini 1.5 Pro) alongside latency,
-- full architecture packages, quality validation scores, and RLS policies.
-- =================================================================

-- ── 1. Create public.architecture_benchmarks table ──────────────────
CREATE TABLE IF NOT EXISTS public.architecture_benchmarks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  generation_id TEXT,
  model_id TEXT NOT NULL,
  model_name TEXT NOT NULL,
  is_archova BOOLEAN NOT NULL DEFAULT FALSE,
  status TEXT NOT NULL DEFAULT 'COMPLETED',
  latency_ms NUMERIC,
  package_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  validation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  comparison_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 2. Performance & Foreign Key Indexes ───────────────────────────
CREATE INDEX IF NOT EXISTS idx_arch_benchmarks_session_id 
  ON public.architecture_benchmarks (session_id);

CREATE INDEX IF NOT EXISTS idx_arch_benchmarks_user_id 
  ON public.architecture_benchmarks (user_id);

CREATE INDEX IF NOT EXISTS idx_arch_benchmarks_model_id 
  ON public.architecture_benchmarks (model_id);

CREATE INDEX IF NOT EXISTS idx_arch_benchmarks_pkg 
  ON public.architecture_benchmarks USING gin (package_json);

-- ── 3. Enable Row Level Security (RLS) ─────────────────────────────
ALTER TABLE public.architecture_benchmarks ENABLE ROW LEVEL SECURITY;

-- ── 4. Grant table privileges to authenticated users ───────────────
GRANT SELECT, INSERT, UPDATE, DELETE ON public.architecture_benchmarks TO authenticated;

-- ── 5. Define Secure RLS Policies (using (select auth.uid()) = user_id) ──
DROP POLICY IF EXISTS "Users can view own benchmark runs" ON public.architecture_benchmarks;
CREATE POLICY "Users can view own benchmark runs" ON public.architecture_benchmarks
  FOR SELECT
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own benchmark runs" ON public.architecture_benchmarks;
CREATE POLICY "Users can insert own benchmark runs" ON public.architecture_benchmarks
  FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own benchmark runs" ON public.architecture_benchmarks;
CREATE POLICY "Users can update own benchmark runs" ON public.architecture_benchmarks
  FOR UPDATE
  TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own benchmark runs" ON public.architecture_benchmarks;
CREATE POLICY "Users can delete own benchmark runs" ON public.architecture_benchmarks
  FOR DELETE
  TO authenticated
  USING ((SELECT auth.uid()) = user_id);

