"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Cpu, Mail, Lock, User, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import BubbleBg from "@/components/BubbleBg";
import { supabase } from "@/lib/supabaseClient";
import { useAppStore } from "@/lib/store";

export default function SignUpPage() {
  const router = useRouter();
  const { setUser, setSession } = useAppStore();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (password !== confirm) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setErrorMessage("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);

    try {
      // 1. Sign up with Supabase Auth
      const redirectTo = typeof window !== "undefined" ? `${window.location.origin}/auth/callback` : undefined;
      const { data, error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          emailRedirectTo: redirectTo,
          data: {
            name: name.trim(),
            full_name: name.trim(),
          },
        },
      });

      if (error) {
        setErrorMessage(error.message);
        setLoading(false);
        return;
      }

      if (data.user) {
        // 2. Insert/upsert into public.users table as well
        try {
          await supabase.from("users").upsert({
            id: data.user.id,
            email: email.trim(),
            name: name.trim() || email.split("@")[0],
          });
        } catch {
          // Table trigger might handle this automatically
        }

        setUser(data.user);
        setSession(data.session);

        if (data.session) {
          setSuccessMessage("Account created successfully! Redirecting...");
          setTimeout(() => {
            router.push("/chat");
          }, 1000);
        } else {
          setSuccessMessage(
            "Account created! Please check your email inbox to confirm your account or sign in."
          );
        }
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "An unexpected error occurred during signup."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-white dark:bg-black">
      <BubbleBg />
      <div className="relative z-10">
        <Navbar />

        <div className="flex min-h-screen items-center justify-center px-4 pt-14">
          <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white/90 p-8 shadow-xl backdrop-blur-md dark:border-gray-700 dark:bg-gray-900/90">
            {/* Header */}
            <div className="mb-8 flex flex-col items-center">
              <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25">
                <Cpu className="h-7 w-7 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Create account</h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Get started with ArchAI for free
              </p>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="mb-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
                <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Success Message */}
            {successMessage && (
              <div className="mb-4 flex items-start gap-2 rounded-xl border border-green-200 bg-green-50 p-3 text-sm text-green-700 dark:border-green-900/50 dark:bg-green-950/40 dark:text-green-300">
                <CheckCircle2 className="h-5 w-5 shrink-0 text-green-500" />
                <span>{successMessage}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">
                  Name
                </label>
                <div className="flex items-center rounded-xl border border-gray-300 bg-gray-50 px-3 transition-colors focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 dark:border-gray-700 dark:bg-gray-800">
                  <User className="h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="John Doe"
                    required
                    disabled={loading}
                    className="w-full bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-gray-400 dark:text-white"
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">
                  Email
                </label>
                <div className="flex items-center rounded-xl border border-gray-300 bg-gray-50 px-3 transition-colors focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 dark:border-gray-700 dark:bg-gray-800">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                    disabled={loading}
                    className="w-full bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-gray-400 dark:text-white"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">
                  Password
                </label>
                <div className="flex items-center rounded-xl border border-gray-300 bg-gray-50 px-3 transition-colors focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 dark:border-gray-700 dark:bg-gray-800">
                  <Lock className="h-4 w-4 text-gray-400" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    disabled={loading}
                    className="w-full bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-gray-400 dark:text-white"
                  />
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">
                  Confirm Password
                </label>
                <div className="flex items-center rounded-xl border border-gray-300 bg-gray-50 px-3 transition-colors focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 dark:border-gray-700 dark:bg-gray-800">
                  <Lock className="h-4 w-4 text-gray-400" />
                  <input
                    type="password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    placeholder="••••••••"
                    required
                    disabled={loading}
                    className="w-full bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-gray-400 dark:text-white"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:opacity-95 hover:shadow-xl hover:shadow-indigo-500/30 disabled:opacity-60"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  "Sign Up"
                )}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
              Already have an account?{" "}
              <Link
                href="/signin"
                className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
              >
                Sign In
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
