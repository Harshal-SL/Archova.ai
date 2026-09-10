"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Cpu, Mail, Lock, User, Loader2, AlertCircle, CheckCircle2, ArrowLeft } from "lucide-react";
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
        try {
          await supabase.from("users").upsert({
            id: data.user.id,
            email: email.trim(),
            name: name.trim() || email.split("@")[0],
          });
        } catch {
          // Table trigger handles automatically
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
              Create an Account
            </h1>
            <p className="mt-1.5 text-xs sm:text-sm text-neutral-600 dark:text-neutral-400">
              Get started with ArchAI Multi-Agent Studio
            </p>
          </div>

          {/* Error Message */}
          {errorMessage && (
            <div className="mb-5 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50/90 p-3.5 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
              <AlertCircle className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
              <span>{errorMessage}</span>
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
            {/* Name */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                Full Name
              </label>
              <div className="flex items-center rounded-xl border border-neutral-300 bg-white px-3.5 transition-all focus-within:border-black focus-within:ring-2 focus-within:ring-black/10 dark:border-neutral-800 dark:bg-neutral-950 dark:focus-within:border-white dark:focus-within:ring-white/10">
                <User className="h-4 w-4 text-neutral-400" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Alex Morgan"
                  required
                  disabled={loading}
                  className="w-full bg-transparent px-3 py-2.5 text-xs text-black placeholder:text-neutral-400 outline-none dark:text-white dark:placeholder:text-neutral-500"
                />
              </div>
            </div>

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

            {/* Confirm Password */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                Confirm Password
              </label>
              <div className="flex items-center rounded-xl border border-neutral-300 bg-white px-3.5 transition-all focus-within:border-black focus-within:ring-2 focus-within:ring-black/10 dark:border-neutral-800 dark:bg-neutral-950 dark:focus-within:border-white dark:focus-within:ring-white/10">
                <Lock className="h-4 w-4 text-neutral-400" />
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
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
                  <span>Creating Account...</span>
                </>
              ) : (
                "Create Studio Account"
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-neutral-500 dark:text-neutral-400">
            Already have an account?{" "}
            <Link
              href="/signin"
              className="font-bold text-black hover:underline dark:text-white"
            >
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
