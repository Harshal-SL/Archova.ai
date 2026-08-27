"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Cpu, Mail, Lock, Loader2, AlertCircle, CheckCircle2, Send } from "lucide-react";
import Navbar from "@/components/Navbar";
import BubbleBg from "@/components/BubbleBg";
import { supabase } from "@/lib/supabaseClient";
import { useAppStore } from "@/lib/store";

export default function SignInPage() {
  const router = useRouter();
  const { setUser, setSession } = useAppStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoading(true);

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (error) {
        setErrorMessage(error.message);
        setLoading(false);
        return;
      }

      if (data.user) {
        setUser(data.user);
        setSession(data.session);
        router.push("/chat");
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "An unexpected error occurred during sign in."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleResendConfirmation = async () => {
    if (!email.trim()) {
      setErrorMessage("Please enter your email address to resend confirmation.");
      return;
    }
    setResending(true);
    setErrorMessage(null);
    try {
      const redirectTo = typeof window !== "undefined" ? `${window.location.origin}/auth/callback` : undefined;
      const { error } = await supabase.auth.resend({
        type: "signup",
        email: email.trim(),
        options: {
          emailRedirectTo: redirectTo,
        },
      });

      if (error) {
        setErrorMessage(error.message);
      } else {
        setSuccessMessage("Confirmation email resent! Please check your inbox & spam folder.");
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to resend confirmation email.");
    } finally {
      setResending(false);
    }
  };

  const isEmailUnconfirmed = errorMessage?.toLowerCase().includes("confirm") || errorMessage?.toLowerCase().includes("verified");

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
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Welcome back</h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Sign in to your ArchAI account
              </p>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="mb-4 space-y-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
                  <span>{errorMessage}</span>
                </div>
                {isEmailUnconfirmed && (
                  <button
                    type="button"
                    onClick={handleResendConfirmation}
                    disabled={resending}
                    className="mt-1 flex items-center gap-1.5 rounded-lg bg-red-100 px-3 py-1.5 text-xs font-semibold text-red-800 transition-colors hover:bg-red-200 dark:bg-red-900/60 dark:text-red-200 dark:hover:bg-red-900"
                  >
                    {resending ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Send className="h-3.5 w-3.5" />
                    )}
                    <span>Resend Confirmation Email</span>
                  </button>
                )}
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

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:opacity-95 hover:shadow-xl hover:shadow-indigo-500/30 disabled:opacity-60"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  "Sign In"
                )}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
              Don&apos;t have an account?{" "}
              <Link
                href="/signup"
                className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
              >
                Sign Up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
