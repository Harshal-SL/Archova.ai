"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Cpu, Mail, Lock, User } from "lucide-react";
import Navbar from "@/components/Navbar";
import BubbleBg from "@/components/BubbleBg";

export default function SignUpPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock sign up — just navigate
    router.push("/chat");
  };

  return (
    <div className="signin-space relative min-h-screen overflow-x-hidden bg-[#F8FAFC] text-[#0F172A] dark:bg-black dark:text-white">
      <div className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(circle_at_20%_15%,rgba(37,99,235,0.08),transparent_40%),radial-gradient(circle_at_80%_20%,rgba(15,23,42,0.06),transparent_35%),radial-gradient(circle_at_50%_90%,rgba(100,116,139,0.08),transparent_40%)] dark:bg-[radial-gradient(circle_at_20%_15%,rgba(255,255,255,0.08),transparent_40%),radial-gradient(circle_at_80%_20%,rgba(255,255,255,0.05),transparent_35%),radial-gradient(circle_at_50%_90%,rgba(255,255,255,0.06),transparent_40%)]" />
      <BubbleBg />
      <div className="relative z-10">
      <Navbar />

      <div className="flex min-h-screen items-center justify-center px-4 pt-14">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-[#FFFFFF]/90 p-8 shadow-xl backdrop-blur-md dark:border-gray-700 dark:bg-gray-900/80">
          {/* Header */}
          <div className="mb-8 flex flex-col items-center">
            <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600">
              <Cpu className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-[#0F172A] dark:text-white">Create account</h1>
            <p className="mt-1 text-sm text-[#64748B] dark:text-gray-400">
              Get started with ArchAI for free
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="mb-1 block text-sm font-medium text-[#0F172A] dark:text-gray-200">Name</label>
              <div className="flex items-center rounded-xl border border-slate-300 bg-white px-3 transition-colors focus-within:border-[#2563EB] focus-within:ring-2 focus-within:ring-[#2563EB]/20 dark:border-gray-700 dark:bg-gray-800 dark:focus-within:border-indigo-400 dark:focus-within:ring-indigo-400/20">
                <User className="h-4 w-4 text-[#64748B] dark:text-gray-400" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  required
                  className="w-full bg-transparent px-3 py-2.5 text-sm text-[#0F172A] outline-none placeholder:text-[#64748B] dark:text-white dark:placeholder:text-gray-500"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="mb-1 block text-sm font-medium text-[#0F172A] dark:text-gray-200">Email</label>
              <div className="flex items-center rounded-xl border border-slate-300 bg-white px-3 transition-colors focus-within:border-[#2563EB] focus-within:ring-2 focus-within:ring-[#2563EB]/20 dark:border-gray-700 dark:bg-gray-800 dark:focus-within:border-indigo-400 dark:focus-within:ring-indigo-400/20">
                <Mail className="h-4 w-4 text-[#64748B] dark:text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full bg-transparent px-3 py-2.5 text-sm text-[#0F172A] outline-none placeholder:text-[#64748B] dark:text-white dark:placeholder:text-gray-500"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="mb-1 block text-sm font-medium text-[#0F172A] dark:text-gray-200">Password</label>
              <div className="flex items-center rounded-xl border border-slate-300 bg-white px-3 transition-colors focus-within:border-[#2563EB] focus-within:ring-2 focus-within:ring-[#2563EB]/20 dark:border-gray-700 dark:bg-gray-800 dark:focus-within:border-indigo-400 dark:focus-within:ring-indigo-400/20">
                <Lock className="h-4 w-4 text-[#64748B] dark:text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-transparent px-3 py-2.5 text-sm text-[#0F172A] outline-none placeholder:text-[#64748B] dark:text-white dark:placeholder:text-gray-500"
                />
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="mb-1 block text-sm font-medium text-[#0F172A] dark:text-gray-200">
                Confirm Password
              </label>
              <div className="flex items-center rounded-xl border border-slate-300 bg-white px-3 transition-colors focus-within:border-[#2563EB] focus-within:ring-2 focus-within:ring-[#2563EB]/20 dark:border-gray-700 dark:bg-gray-800 dark:focus-within:border-indigo-400 dark:focus-within:ring-indigo-400/20">
                <Lock className="h-4 w-4 text-[#64748B] dark:text-gray-400" />
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-transparent px-3 py-2.5 text-sm text-[#0F172A] outline-none placeholder:text-[#64748B] dark:text-white dark:placeholder:text-gray-500"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full rounded-xl border border-[#1E40AF] bg-[#1E3A8A] py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#1E3A8A]/40 transition-all hover:bg-[#1E40AF] hover:shadow-xl hover:shadow-[#1E40AF]/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1E40AF] focus-visible:ring-offset-2 dark:border-[#3B82F6] dark:bg-[#1E3A8A] dark:shadow-[#1E3A8A]/35 dark:hover:bg-[#1E40AF]"
            >
              Sign Up
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-[#64748B] dark:text-gray-400">
            Already have an account?{" "}
            <Link
              href="/signin"
              className="font-medium text-[#2563EB] hover:text-[#1D4ED8] dark:text-indigo-400 dark:hover:text-indigo-300"
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
