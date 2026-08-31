"use client";

import Link from "next/link";
import {
  Cpu,
  Sparkles,
  Network,
  Brain,
  Boxes,
  Terminal,
  ShieldCheck,
  Server,
  Cloud,
  Database,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import BubbleBg from "@/components/BubbleBg";

const features = [
  {
    icon: Sparkles,
    title: "REE Input Understanding",
    desc: "Analyzes natural language problem statements and executes an interactive stakeholder interview to clarify ambiguous requirements.",
    gradient: "from-indigo-500 to-blue-500",
  },
  {
    icon: Network,
    title: "SAE Architecture & HLD",
    desc: "Transforms requirements into ARSRS specifications and renders interactive, zoomable High-Level Design (HLD) flowcharts.",
    gradient: "from-purple-500 to-pink-500",
  },
  {
    icon: Boxes,
    title: "5 Parallel LLD Generators",
    desc: "Synthesizes detailed Low-Level Designs concurrently across Backend, Frontend, Database, Security, and Cloud domains.",
    gradient: "from-emerald-500 to-teal-500",
  },
  {
    icon: Terminal,
    title: "Real-Time SSE Event Stream",
    desc: "Inspect live multi-agent execution, stage transitions, agent completions, and historical logs in a built-in terminal console.",
    gradient: "from-amber-500 to-orange-500",
  },
];

const lldBadges = [
  { name: "Backend LLD", icon: Server, color: "text-sky-400 bg-sky-500/10 border-sky-500/30" },
  { name: "Frontend LLD", icon: Cpu, color: "text-pink-400 bg-pink-500/10 border-pink-500/30" },
  { name: "Database LLD", icon: Database, color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" },
  { name: "Security LLD", icon: ShieldCheck, color: "text-rose-400 bg-rose-500/10 border-rose-500/30" },
  { name: "Cloud LLD", icon: Cloud, color: "text-teal-400 bg-teal-500/10 border-teal-500/30" },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-white dark:bg-black">
      <BubbleBg />

      <div className="relative z-10">
        <Navbar />

        {/* Hero Section */}
        <section className="relative overflow-hidden pt-14">
          <div className="relative mx-auto flex max-w-6xl flex-col items-center px-4 pb-20 pt-24 text-center md:pt-32">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-400/50 bg-indigo-100/80 px-4 py-1.5 text-xs font-semibold text-indigo-700 dark:border-indigo-500/40 dark:bg-indigo-950/60 dark:text-indigo-300">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Multi-Agent REE + SAE Architecture Engine</span>
            </div>

            <h1 className="max-w-4xl text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
              <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                AI System Architecture
              </span>
              <br />
              <span className="text-gray-900 dark:text-white">Generator</span>
            </h1>

            <p className="mt-6 max-w-2xl text-base sm:text-lg text-gray-600 dark:text-gray-300">
              Transform high-level problem statements into formal ARSRS specifications,
              interactive High-Level Designs, and 5 concurrent Low-Level Designs.
            </p>

            {/* 5 LLD badgelist */}
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {lldBadges.map(({ name, icon: Icon, color }, idx) => (
                <div
                  key={idx}
                  className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${color}`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{name}</span>
                </div>
              ))}
            </div>

            <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row">
              <Link
                href="/chat"
                className="flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:opacity-95 hover:shadow-xl hover:shadow-indigo-500/30"
              >
                <span>Start Architecture Generation</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/signup"
                className="rounded-full border border-gray-300 bg-white/80 px-8 py-3.5 text-sm font-semibold text-gray-700 shadow-sm backdrop-blur-sm transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-900/80 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                Create Account
              </Link>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="mx-auto max-w-6xl px-4 py-16">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white sm:text-3xl">
              End-to-End Multi-Agent Pipeline
            </h2>
            <p className="mt-2 text-sm text-gray-500">
              From requirement clarification to production-ready low-level architecture
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f, i) => {
              const Icon = f.icon;
              return (
                <div
                  key={i}
                  className="rounded-2xl border border-gray-200 bg-white/70 p-6 shadow-sm backdrop-blur-sm transition-all hover:border-indigo-300 hover:shadow-md dark:border-gray-800 dark:bg-gray-900/70 dark:hover:border-indigo-800"
                >
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${f.gradient} shadow-md`}
                  >
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="mt-4 text-base font-bold text-gray-900 dark:text-white">
                    {f.title}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-gray-600 dark:text-gray-400">
                    {f.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Call to Action Banner */}
        <section className="mx-auto max-w-6xl px-4 pb-20">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 px-8 py-16 text-center text-white shadow-2xl shadow-indigo-500/25">
            <h2 className="text-3xl font-bold sm:text-4xl">
              Ready to architect your next system?
            </h2>
            <p className="mt-3 text-base text-white/80 max-w-xl mx-auto">
              Test requirements, execute clarifying stakeholder interviews, and export complete
              ARSRS, HLD, and LLD specifications.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/chat"
                className="rounded-full bg-white px-8 py-3 text-sm font-semibold text-indigo-600 shadow-lg transition-all hover:bg-gray-100"
              >
                Open Architecture Studio
              </Link>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-gray-200 dark:border-gray-800">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-6 text-xs text-gray-500">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-indigo-500" />
              <span>ArchAI &copy; 2026</span>
            </div>
            <p>AI-Powered System Architecture Generator • REE & SAE</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
