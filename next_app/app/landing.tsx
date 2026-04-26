"use client";

import Link from "next/link";
import {
  Cpu,
  Sparkles,
  Network,
  Brain,
  Lightbulb,
  ArrowRight,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import ClickSpark from "@/components/ClickSpark";

const features = [
  {
    icon: Sparkles,
    title: "AI Architecture Generation",
    desc: "Describe your system in plain English and get a complete architecture in seconds.",
    gradient: "from-indigo-500 to-blue-500",
  },
  {
    icon: Network,
    title: "Interactive HLD / LLD",
    desc: "Explore High-Level and Low-Level designs with interactive, zoomable diagrams.",
    gradient: "from-purple-500 to-pink-500",
  },
  {
    icon: Brain,
    title: "Explainable AI",
    desc: "Click any component to understand why it was chosen and how it fits the system.",
    gradient: "from-emerald-500 to-teal-500",
  },
  {
    icon: Lightbulb,
    title: "Architecture Inspirations",
    desc: "Browse curated architecture patterns for e-commerce, chat, streaming, and more.",
    gradient: "from-amber-500 to-orange-500",
  },
];

export default function LandingPage() {
  return (
    <ClickSpark
      sparkColor="#ffffff"
      sparkSize={10}
      sparkRadius={15}
      sparkCount={8}
      duration={400}
      easing="ease-out"
      extraScale={1}
      className="min-h-screen"
    >
      <div className="relative min-h-screen overflow-x-hidden bg-[#F8FAFC] text-[#0F172A] dark:bg-black dark:text-white">
      <div className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(circle_at_20%_15%,rgba(37,99,235,0.08),transparent_40%),radial-gradient(circle_at_80%_20%,rgba(15,23,42,0.06),transparent_35%),radial-gradient(circle_at_50%_90%,rgba(100,116,139,0.08),transparent_40%)] dark:bg-[radial-gradient(circle_at_20%_15%,rgba(255,255,255,0.08),transparent_40%),radial-gradient(circle_at_80%_20%,rgba(255,255,255,0.05),transparent_35%),radial-gradient(circle_at_50%_90%,rgba(255,255,255,0.06),transparent_40%)]" />

      {/* Page Content */}
      <div className="relative z-10">
        <Navbar />

        {/* Hero */}
      <section className="relative overflow-hidden pt-14">
        <div className="relative mx-auto flex max-w-6xl flex-col items-center px-4 pb-20 pt-24 text-center md:pt-32">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#2563EB]/30 bg-[#2563EB]/10 px-4 py-1.5 text-sm font-medium text-[#2563EB]">
            <Sparkles className="h-4 w-4" />
            Powered by AI
          </div>

          <h1 className="max-w-4xl text-4xl font-extrabold leading-tight tracking-tight text-[#0F172A] dark:text-white sm:text-5xl md:text-6xl lg:text-7xl">
            AI System Architecture
            <br />
            Generator
          </h1>

          <p className="mt-6 max-w-2xl text-lg text-[#64748B] dark:text-gray-300">
            Design production-ready system architectures in seconds. Describe what
            you want to build and let AI generate interactive High-Level and
            Low-Level design diagrams with full explanations.
          </p>

          <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row">
            <Link
              href="/chat"
              className="group flex items-center gap-2 rounded-full bg-[#2563EB] px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-[#2563EB]/30 transition-all hover:bg-[#1D4ED8] hover:shadow-xl hover:shadow-[#1D4ED8]/40"
            >
              Start Designing
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/signin"
              className="rounded-full border border-[#2563EB] bg-[#2563EB] px-8 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-[#1D4ED8]"
            >
              Sign In
            </Link>
          </div>

          {/* Preview mock */}
          <div className="mt-16 w-full max-w-4xl overflow-hidden rounded-2xl border border-slate-200 bg-[#FFFFFF] shadow-2xl dark:border-gray-700 dark:bg-transparent">
            <div className="flex items-center gap-2 border-b border-slate-200 bg-slate-100 px-4 py-2 dark:border-gray-700 dark:bg-gray-900">
              <div className="h-3 w-3 rounded-full bg-red-400" />
              <div className="h-3 w-3 rounded-full bg-yellow-400" />
              <div className="h-3 w-3 rounded-full bg-green-400" />
              <span className="ml-2 text-xs text-[#64748B] dark:text-gray-400">ArchAI - Chat</span>
            </div>
            <div className="flex h-64 items-center justify-center bg-gradient-to-br from-slate-100 to-white dark:from-gray-900 dark:to-black">
              <div className="flex flex-col items-center gap-3 opacity-70">
                <Cpu className="h-12 w-12 text-[#2563EB]" />
                <p className="text-sm text-[#64748B] dark:text-gray-400">
                  Your architecture preview will appear here
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="mb-12 text-center">
          <h2 className="text-3xl font-bold text-[#0F172A] dark:text-white sm:text-4xl">
            Everything you need to design systems
          </h2>
          <p className="mt-3 text-[#64748B] dark:text-gray-400">
            From idea to architecture diagram in seconds
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f) => (
            <div
              key={f.title}
              className="group rounded-2xl border border-slate-200 bg-[#FFFFFF] p-6 backdrop-blur-sm transition-all hover:-translate-y-1 hover:shadow-lg dark:border-gray-700 dark:bg-gray-900/80"
            >
              <div
                className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${f.gradient}`}
              >
                <f.icon className="h-6 w-6 text-white" />
              </div>
              <h3 className="mb-2 font-semibold text-[#0F172A] dark:text-white">{f.title}</h3>
              <p className="text-sm leading-relaxed text-[#64748B] dark:text-gray-400">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-4 pb-20">
        <div className="relative overflow-hidden rounded-3xl bg-[#2563EB] px-8 py-16 text-center text-white">
          <div className="pointer-events-none absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iLjA1Ij48cGF0aCBkPSJNMzYgMzRoLTJ2LTRoMnYtNGgydjRoNHYyaC00djRoLTJ2LTR6bS0yMi0yaDJ2LTRoLTJ2NGgtNHYyaDR2NGgydi00eiIvPjwvZz48L2c+PC9zdmc+')] opacity-50" />
          <h2 className="relative text-3xl font-bold sm:text-4xl">
            Ready to design your system?
          </h2>
          <p className="relative mt-3 text-lg text-white/80">
            Join thousands of developers using AI to create perfect architectures.
          </p>
          <div className="relative mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/signup"
              className="rounded-full bg-white px-8 py-3 font-semibold text-[#2563EB] shadow-lg transition-all hover:bg-slate-100 hover:shadow-xl"
            >
              Sign Up Free
            </Link>
            <Link
              href="/signin"
              className="rounded-full border border-white/40 px-8 py-3 font-semibold text-white transition-colors hover:bg-[#1D4ED8]"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-gray-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-6">
          <div className="flex items-center gap-2 text-sm text-[#64748B] dark:text-gray-500">
            <Cpu className="h-4 w-4 text-[#2563EB]" />
            <span>ArchAI &copy; 2026</span>
          </div>
          <p className="text-xs text-[#64748B] dark:text-gray-400">
            AI-Powered System Architecture Generator
          </p>
        </div>
      </footer>
      </div>
    </div>
    </ClickSpark>
  );
}
