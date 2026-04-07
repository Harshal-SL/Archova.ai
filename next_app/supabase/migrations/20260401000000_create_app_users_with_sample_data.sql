-- Create a new app_users table
CREATE TABLE IF NOT EXISTS app_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Helpful index for email lookups
CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users (email);

-- Enable Row Level Security
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;

-- Basic read policy for authenticated users
DROP POLICY IF EXISTS "Authenticated users can read app_users" ON app_users;
CREATE POLICY "Authenticated users can read app_users" ON app_users
  FOR SELECT
  TO authenticated
  USING (TRUE);

-- Seed sample data
INSERT INTO app_users (email, full_name, role, is_active)
VALUES
  ('admin@example.com', 'Admin User', 'admin', TRUE),
  ('alice@example.com', 'Alice Johnson', 'user', TRUE),
  ('bob@example.com', 'Bob Smith', 'user', FALSE)
ON CONFLICT (email) DO NOTHING;
