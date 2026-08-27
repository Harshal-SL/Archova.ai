"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Cpu, AlertCircle, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { apiLogin } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function SignIn() {
  const router = useRouter();
  const setUser = useAppStore((s) => s.setUser);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiLogin(email, password);
      if (data.error) {
        setError(data.error);
        return;
      }
      if (data.user) {
        setUser({
          id: data.user.id,
          email: data.user.email,
          name: data.user.email.split("@")[0],
        });
      }
      router.push("/chat");
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-black font-sans">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="relative w-full max-w-md overflow-hidden rounded-2xl border border-[#333333] bg-[#0A0A0A] p-8"
      >
        <div className="absolute top-0 left-0 h-[1px] w-full bg-gradient-to-r from-transparent via-white to-transparent opacity-20" />

        <div className="mb-8 flex flex-col items-center text-center">
          <Link href="/" className="mb-6 flex items-center justify-center rounded-full border border-[#333] bg-black p-3">
            <Cpu className="h-6 w-6 text-white" />
          </Link>
          <h2 className="mb-2 text-2xl font-bold tracking-tight text-white">Welcome back</h2>
          <p className="text-sm text-[#AAAAAA]">Sign in to your ArchitectAI account</p>
        </div>

        {error && (
          <div className="mb-5 flex items-start gap-3 rounded-lg border border-[#555] bg-[#111] px-4 py-3">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-white" />
            <p className="text-sm text-[#CCCCCC]">{error}</p>
          </div>
        )}

        <form onSubmit={handleSignIn} className="flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-[#AAAAAA]">Email</label>
            <input
              id="signin-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="rounded-lg border border-[#333333] bg-white px-4 py-3 text-sm text-black placeholder-gray-400 transition-colors focus:border-white focus:outline-none focus:ring-1 focus:ring-white"
            />
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-[#AAAAAA]">Password</label>
            <input
              id="signin-password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="rounded-lg border border-[#333333] bg-white px-4 py-3 text-sm text-black placeholder-gray-400 transition-colors focus:border-white focus:outline-none focus:ring-1 focus:ring-white"
            />
          </div>

          <button
            id="signin-submit"
            type="submit"
            disabled={loading}
            className="group mt-2 flex items-center justify-center gap-2 rounded-lg border border-transparent bg-white px-4 py-3 font-semibold text-black transition-all hover:bg-black hover:text-white hover:border-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                Sign In
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </>
            )}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-[#555555]">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="text-white hover:underline">
            Sign Up
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
