"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Cpu, Mail, Lock, Loader2, AlertCircle, CheckCircle2, Send, ArrowLeft } from "lucide-react";
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
    <div className="relative min-h-screen overflow-x-hidden bg-white text-black dark:bg-black dark:text-white transition-colors">
      <BubbleBg />
      <Navbar />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 pt-14 pb-12">
        <div className="w-full max-w-md monochrome-card rounded-3xl p-8 sm:p-10 backdrop-blur-xl shadow-xl">
          {/* Back to Home Link */}
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-neutral-500 hover:text-black dark:text-neutral-400 dark:hover:text-white mb-6 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Home</span>
          </Link>

          {/* Header */}
          <div className="mb-8 flex flex-col items-center text-center">
            <div className="mb-3.5 flex h-14 w-14 items-center justify-center rounded-2xl bg-black text-white dark:bg-white dark:text-black shadow-md">
              <Cpu className="h-7 w-7" />
            </div>
            <h1 className="font-heading text-2xl sm:text-3xl font-extrabold tracking-tight">
              Welcome back
            </h1>
            <p className="mt-1.5 text-xs sm:text-sm text-neutral-600 dark:text-neutral-400">
              Sign in to your ArchAI Architecture Studio
            </p>
          </div>

          {/* Error Message */}
          {errorMessage && (
            <div className="mb-5 space-y-2 rounded-xl border border-red-200 bg-red-50/90 p-3.5 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
              {isEmailUnconfirmed && (
                <button
                  type="button"
                  onClick={handleResendConfirmation}
                  disabled={resending}
                  className="mt-1.5 flex items-center gap-1.5 rounded-lg bg-red-100 px-3 py-1.5 text-xs font-semibold text-red-800 transition-colors hover:bg-red-200 dark:bg-red-900/60 dark:text-red-200 dark:hover:bg-red-900"
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
            <div className="mb-5 flex items-start gap-2 rounded-xl border border-neutral-300 bg-neutral-100 p-3.5 text-xs text-black dark:border-neutral-700 dark:bg-neutral-900 dark:text-white">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-black dark:text-white mt-0.5" />
              <span>{successMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                Work Email
              </label>
              <div className="flex items-center rounded-xl border border-neutral-300 bg-white px-3.5 transition-all focus-within:border-black focus-within:ring-2 focus-within:ring-black/10 dark:border-neutral-800 dark:bg-neutral-950 dark:focus-within:border-white dark:focus-within:ring-white/10">
                <Mail className="h-4 w-4 text-neutral-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="engineer@company.com"
                  required
                  disabled={loading}
                  className="w-full bg-transparent px-3 py-2.5 text-xs text-black placeholder:text-neutral-400 outline-none dark:text-white dark:placeholder:text-neutral-500"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                Password
              </label>
              <div className="flex items-center rounded-xl border border-neutral-300 bg-white px-3.5 transition-all focus-within:border-black focus-within:ring-2 focus-within:ring-black/10 dark:border-neutral-800 dark:bg-neutral-950 dark:focus-within:border-white dark:focus-within:ring-white/10">
                <Lock className="h-4 w-4 text-neutral-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  disabled={loading}
                  className="w-full bg-transparent px-3 py-2.5 text-xs text-black placeholder:text-neutral-400 outline-none dark:text-white dark:placeholder:text-neutral-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-black text-white dark:bg-white dark:text-black py-3 text-xs font-bold shadow-md transition-all hover:bg-neutral-800 dark:hover:bg-neutral-200 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                "Sign In to Studio"
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-neutral-500 dark:text-neutral-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/signup"
              className="font-bold text-black hover:underline dark:text-white"
            >
              Create Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
