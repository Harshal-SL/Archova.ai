"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAppStore } from "@/lib/store";
import {
  Cpu,
  Sparkles,
  Network,
  ShieldCheck,
  Server,
  Cloud,
  Database,
  ArrowRight,
  ArrowDownRight,
  ArrowDownLeft,
  ArrowDown,
  Zap,
  CheckCircle2,
  Layers,
  MessageSquare,
  ChevronRight,
  Check,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import BubbleBg from "@/components/BubbleBg";
import { AnimatedContainer } from "@/components/ui/footer-section";

const lldBadges = [
  { name: "Backend LLD", icon: Server },
  { name: "Frontend LLD", icon: Cpu },
  { name: "Database LLD", icon: Database },
  { name: "Security LLD", icon: ShieldCheck },
  { name: "Cloud LLD", icon: Cloud },
];

const metrics = [
  { value: "10x", label: "Faster RFC Velocity", detail: "From weeks of whiteboard debate to minutes of deterministic synthesis" },
  { value: "5", label: "Parallel LLD Engines", detail: "Concurrent generation across Backend, Frontend, DB, Security & Cloud" },
  { value: "100%", label: "Deterministic Graph", detail: "Visual React Flow topology with protocol-level edge verification" },
  { value: "ISO/IEEE", label: "Formal Spec Format", detail: "Standardized ARSRS documents ready for security and enterprise audits" },
];

const services = [
  {
    step: "01",
    icon: MessageSquare,
    title: "Stakeholder Clarification Interview (REE)",
    badge: "Requirements Engine",
    desc: "Autonomous multi-turn interview that proactively identifies edge cases, availability requirements, quantitative throughput metrics, and regulatory constraints.",
    features: [
      "Dynamic multi-turn stakeholder questioning",
      "Quantitative SLA, RTO, and RPO calculation",
      "Automated ambiguity resolution from natural language",
    ],
    pinColor: "#f97316",
    numberColor: "text-amber-500 dark:text-amber-400",
    badgeBg: "bg-amber-100/90 text-amber-900 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200/80 dark:border-amber-800/50",
    innerBg: "bg-[#fff8f0] dark:bg-[#1a140b]",
    innerBorder: "border-amber-200/80 dark:border-amber-900/40",
    rotation: "md:-rotate-2",
  },
  {
    step: "02",
    icon: Sparkles,
    title: "Formal ARSRS Specification Document",
    badge: "Specification Synthesis",
    desc: "Generates an Architecture-Ready Structured Requirements Specification document adhering to formal IEEE/ISO software engineering standards.",
    features: [
      "Comprehensive functional & non-functional requirements",
      "Executive summary & architectural constraints",
      "One-click JSON and Markdown specification export",
    ],
    pinColor: "#2563eb",
    numberColor: "text-blue-600 dark:text-blue-400",
    badgeBg: "bg-blue-100/90 text-blue-900 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200/80 dark:border-blue-800/50",
    innerBg: "bg-[#f0f6ff] dark:bg-[#0b1424]",
    innerBorder: "border-blue-200/80 dark:border-blue-900/40",
    rotation: "md:rotate-2",
  },
  {
    step: "03",
    icon: Network,
    title: "Interactive High-Level Design (HLD)",
    badge: "Visual Topology",
    desc: "Synthesizes an interactive, zoomable React Flow topology graph mapping clients, API gateways, microservices, databases, caches, and cloud infrastructure.",
    features: [
      "Real-time node drawer inspector with deep metadata",
      "Layer filtering: Client, Gateway, Services, Storage, Infra",
      "Animated protocol flows (REST, gRPC, WebSocket, Kafka)",
    ],
    pinColor: "#9333ea",
    numberColor: "text-purple-600 dark:text-purple-400",
    badgeBg: "bg-purple-100/90 text-purple-900 dark:bg-purple-950/60 dark:text-purple-300 border-purple-200/80 dark:border-purple-800/50",
    innerBg: "bg-[#faf5ff] dark:bg-[#180e26]",
    innerBorder: "border-purple-200/80 dark:border-purple-900/40",
    rotation: "md:-rotate-1.5",
  },
  {
    step: "04",
    icon: Server,
    title: "Backend & Microservices LLD",
    badge: "Execution Architecture",
    desc: "Synthesizes low-level backend service architecture including API schemas, internal gRPC contracts, message queues, and async worker choreography.",
    features: [
      "REST & gRPC endpoint contracts",
      "Event-driven Kafka & RabbitMQ choreography",
      "Service isolation, circuit breakers & idempotency rules",
    ],
    pinColor: "#ea580c",
    numberColor: "text-orange-500 dark:text-orange-400",
    badgeBg: "bg-orange-100/90 text-orange-900 dark:bg-orange-950/60 dark:text-orange-300 border-orange-200/80 dark:border-orange-800/50",
    innerBg: "bg-[#fff7ed] dark:bg-[#1a1109]",
    innerBorder: "border-orange-200/80 dark:border-orange-900/40",
    rotation: "md:rotate-2",
  },
  {
    step: "05",
    icon: Database,
    title: "Database, Schemas & Sharding LLD",
    badge: "Data Layer",
    desc: "Architects the complete persistence tier with relational schemas, NoSQL document collections, caching strategies, and partition models.",
    features: [
      "Entity-relationship schemas with indexing strategies",
      "Read/Write replica topology & Redis cache invalidation",
      "ACID vs BASE consistency models & sharding keys",
    ],
    pinColor: "#0284c7",
    numberColor: "text-sky-600 dark:text-sky-400",
    badgeBg: "bg-sky-100/90 text-sky-900 dark:bg-sky-950/60 dark:text-sky-300 border-sky-200/80 dark:border-sky-800/50",
    innerBg: "bg-[#f0f9ff] dark:bg-[#0a1622]",
    innerBorder: "border-sky-200/80 dark:border-sky-900/40",
    rotation: "md:-rotate-2",
  },
  {
    step: "06",
    icon: ShieldCheck,
    title: "Security, Cloud & Multi-Region LLD",
    badge: "Zero Trust & Infra",
    desc: "Enforces enterprise Zero Trust authentication, fine-grained RBAC matrices, Kubernetes cluster topologies, and multi-region disaster recovery.",
    features: [
      "OAuth2, OIDC, JWT & mTLS cryptographic flows",
      "Kubernetes pod topology & Terraform IaC blueprints",
      "Multi-region failover, DNS routing & automated backups",
    ],
    pinColor: "#4f46e5",
    numberColor: "text-indigo-600 dark:text-indigo-400",
    badgeBg: "bg-indigo-100/90 text-indigo-900 dark:bg-indigo-950/60 dark:text-indigo-300 border-indigo-200/80 dark:border-indigo-800/50",
    innerBg: "bg-[#eef2ff] dark:bg-[#11112b]",
    innerBorder: "border-indigo-200/80 dark:border-indigo-900/40",
    rotation: "md:rotate-1.5",
  },
];

const stepTransitions = [
  {
    from: "01",
    to: "02",
    top: "15.5%",
    direction: "down-right" as const,
    color: "#2563eb",
  },
  {
    from: "02",
    to: "03",
    top: "32.5%",
    direction: "down-left" as const,
    color: "#9333ea",
  },
  {
    from: "03",
    to: "04",
    top: "49.5%",
    direction: "down-right" as const,
    color: "#ea580c",
  },
  {
    from: "04",
    to: "05",
    top: "66.5%",
    direction: "down-left" as const,
    color: "#0284c7",
  },
  {
    from: "05",
    to: "06",
    top: "83.5%",
    direction: "down-right" as const,
    color: "#4f46e5",
  },
];

function PushPin({ color = "#f97316" }: { color?: string }) {
  return (
    <div className="relative flex items-center justify-center pointer-events-none select-none">
      {/* Puncture hole dot */}
      <div className="absolute top-[20px] left-1/2 -translate-x-1/2 w-1.5 h-1 rounded-full bg-black/40 blur-[0.5px]" />

      {/* Soft shadow cast by the pin on the paper */}
      <div className="absolute top-[18px] left-[calc(50%+3px)] w-4 h-2 rounded-full bg-black/25 blur-[1.5px] -rotate-12" />

      {/* 3D Push Pin SVG */}
      <svg
        width="26"
        height="30"
        viewBox="0 0 26 30"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="relative z-10 transition-transform duration-200 group-hover:scale-110 group-hover:-translate-y-0.5 filter drop-shadow-[0_2px_3px_rgba(0,0,0,0.18)]"
      >
        {/* Steel needle with highlight */}
        <line
          x1="13"
          y1="17"
          x2="13"
          y2="25"
          stroke="#94a3b8"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        <line
          x1="13.5"
          y1="18"
          x2="13.5"
          y2="24"
          stroke="#cbd5e1"
          strokeWidth="0.8"
        />

        {/* Lower rim base */}
        <ellipse cx="13" cy="17" rx="5.5" ry="2.2" fill={color} />
        <ellipse cx="13" cy="16.5" rx="4.8" ry="1.8" fill="#ffffff" fillOpacity="0.25" />

        {/* Tapered Pin Body / Waist */}
        <path
          d="M9.5 8 C9.5 12, 8.5 15, 7.5 17 L18.5 17 C17.5 15, 16.5 12, 16.5 8 Z"
          fill={color}
        />
        {/* Shading on right side of body */}
        <path
          d="M13 8 C14 12, 16 14, 18.5 17 C17.5 15, 16.5 12, 16.5 8 Z"
          fill="#000000"
          fillOpacity="0.18"
        />
        {/* Highlight on left side of body */}
        <path
          d="M9.5 8 C9.5 12, 8.5 15, 7.5 17 C8.5 16, 11 13, 11 8 Z"
          fill="#ffffff"
          fillOpacity="0.25"
        />

        {/* Upper Rim */}
        <ellipse cx="13" cy="8" rx="6.5" ry="2.4" fill={color} />
        <ellipse cx="13" cy="7.5" rx="5.8" ry="1.8" fill="#ffffff" fillOpacity="0.25" />

        {/* Top Dome Cap */}
        <ellipse cx="13" cy="4.8" rx="5.2" ry="3.2" fill={color} />
        {/* 3D Specular Highlight */}
        <ellipse cx="11.5" cy="3.8" rx="2.4" ry="1.3" fill="#ffffff" fillOpacity="0.65" />
      </svg>
    </div>
  );
}

export default function LandingPage() {
  const router = useRouter();
  const [activePreviewTab, setActivePreviewTab] = useState<"topology" | "terminal" | "arsrs">("topology");

  const handleLoadTemplate = () => {
    useAppStore.getState().loadDemoData();
    router.push("/chat");
  };


  return (
    <div className="relative min-h-screen overflow-x-hidden bg-white text-black dark:bg-black dark:text-white selection:bg-black selection:text-white dark:selection:bg-white dark:selection:text-black transition-colors">
      <BubbleBg />
      <Navbar />

      <div className="relative z-10">
        {/* ════════════════════════════════════════════════════════════════════════════════════════════
            SECTION 1: HOME (HERO)
        ════════════════════════════════════════════════════════════════════════════════════════════ */}
        <section id="home" className="relative pt-24 pb-20 md:pt-36 md:pb-28 overflow-hidden">
          <div className="mx-auto max-w-6xl px-4 text-center">
            {/* Announcement Pill */}
            <div className="inline-flex items-center gap-2 rounded-full border border-neutral-300 bg-neutral-100 px-4 py-1.5 text-xs font-semibold text-neutral-800 backdrop-blur-md transition-all hover:border-black dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:border-white shadow-xs mb-8">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-black dark:bg-white opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-black dark:bg-white" />
              </span>
              <span>ArchAI 2.5 • Autonomous Multi-Agent Systems Engineering</span>
              <ChevronRight className="h-3.5 w-3.5 text-neutral-500" />
            </div>

            {/* Bold Monochrome Headline */}
            <h1 className="font-heading max-w-5xl mx-auto text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-6xl md:text-7xl">
              Architect Enterprise Systems in{" "}
              <span className="bg-gradient-to-r from-black via-neutral-700 to-neutral-500 dark:from-white dark:via-neutral-200 dark:to-neutral-400 bg-clip-text text-transparent">
                Seconds, Not Sprints
              </span>
            </h1>

            {/* Subtitle */}
            <p className="mt-7 max-w-3xl mx-auto text-base sm:text-xl leading-relaxed text-neutral-600 dark:text-neutral-400">
              Transform high-level problem statements into formal IEEE/ISO-compliant ARSRS specifications,
              interactive zoomable High-Level Design (HLD) topologies, and 5 parallel Low-Level Designs.
            </p>

            {/* 5 LLD Domain Badges in Monochrome Aesthetic */}
            <div className="mt-8 flex flex-wrap justify-center gap-2.5">
              {lldBadges.map(({ name, icon: Icon }, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-neutral-800 shadow-xs backdrop-blur-sm transition-all duration-200 hover:border-black hover:text-black dark:border-neutral-800 dark:bg-neutral-950 dark:text-neutral-200 dark:hover:border-white dark:hover:text-white hover:-translate-y-0.5"
                >
                  <Icon className="h-3.5 w-3.5 text-neutral-700 dark:text-neutral-300" />
                  <span>{name}</span>
                </div>
              ))}
            </div>

            {/* Hero CTAs */}
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/chat"
                className="group flex items-center gap-2.5 rounded-full bg-black text-white dark:bg-white dark:text-black px-8 py-4 text-sm font-bold shadow-lg transition-all duration-200 hover:bg-neutral-800 dark:hover:bg-neutral-200 hover:-translate-y-0.5 active:translate-y-0"
              >
                <span>Launch Architecture Studio</span>
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
              </Link>
              <button
                type="button"
                onClick={handleLoadTemplate}
                className="group flex items-center gap-2.5 rounded-full border border-blue-500/40 bg-blue-50/90 px-7 py-4 text-sm font-bold text-blue-700 shadow-sm backdrop-blur-sm transition-all duration-200 hover:bg-blue-100 hover:border-blue-600 dark:border-blue-400/30 dark:bg-blue-950/50 dark:text-blue-300 dark:hover:bg-blue-900/60 dark:hover:border-blue-400 hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
              >
                <Layers className="h-4 w-4 text-blue-600 dark:text-blue-400 transition-transform duration-200 group-hover:scale-110" />
                <span>Load Basic HLD & LLD Template</span>
              </button>
              <a
                href="#services"
                className="flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-7 py-4 text-sm font-bold text-neutral-800 backdrop-blur-sm transition-all duration-200 hover:border-black hover:text-black dark:border-neutral-700 dark:bg-black dark:text-neutral-200 dark:hover:border-white dark:hover:text-white"
              >
                <span>Explore Capabilities</span>
              </a>
            </div>

            {/* Monochrome Code / Architecture Simulator Preview Window */}
            <div className="mt-16 mx-auto max-w-5xl rounded-2xl border border-neutral-300 bg-white/90 p-2 shadow-xl dark:border-neutral-800 dark:bg-[#0a0a0a]/90 backdrop-blur-xl">
              {/* Window Header */}
              <div className="flex items-center justify-between border-b border-neutral-200 dark:border-neutral-800 px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <div className="h-2.5 w-2.5 rounded-full bg-neutral-300 dark:bg-neutral-700" />
                  <div className="h-2.5 w-2.5 rounded-full bg-neutral-300 dark:bg-neutral-700" />
                  <div className="h-2.5 w-2.5 rounded-full bg-neutral-300 dark:bg-neutral-700" />
                  <span className="ml-2 font-mono text-xs text-neutral-500">
                    archai-engine://runtime-v2.5
                  </span>
                </div>

                {/* Tab Switcher */}
                <div className="flex items-center gap-1 rounded-lg bg-neutral-100 dark:bg-neutral-900 p-1 text-xs font-semibold">
                  <button
                    onClick={() => setActivePreviewTab("topology")}
                    className={`rounded-md px-3 py-1 transition-all ${activePreviewTab === "topology"
                        ? "bg-black text-white dark:bg-white dark:text-black shadow-xs"
                        : "text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
                      }`}
                  >
                    HLD Topology Map
                  </button>
                  <button
                    onClick={() => setActivePreviewTab("terminal")}
                    className={`rounded-md px-3 py-1 transition-all ${activePreviewTab === "terminal"
                        ? "bg-black text-white dark:bg-white dark:text-black shadow-xs"
                        : "text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
                      }`}
                  >
                    SSE Execution Log
                  </button>
                  <button
                    onClick={() => setActivePreviewTab("arsrs")}
                    className={`rounded-md px-3 py-1 transition-all ${activePreviewTab === "arsrs"
                        ? "bg-black text-white dark:bg-white dark:text-black shadow-xs"
                        : "text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
                      }`}
                  >
                    ARSRS Spec
                  </button>
                </div>
              </div>

              {/* Window Content */}
              <div className="p-6 text-left font-mono text-xs overflow-x-auto min-h-[260px] flex items-center justify-center">
                {activePreviewTab === "topology" && (
                  <div className="w-full space-y-4">
                    <div className="flex items-center justify-between text-neutral-900 dark:text-white border-b border-neutral-200 dark:border-neutral-800 pb-2">
                      <span className="font-bold flex items-center gap-2">
                        <Network className="h-4 w-4" /> Live Multi-Tier Graph Topology
                      </span>
                      <span className="text-[11px] bg-neutral-100 dark:bg-neutral-900 px-2 py-0.5 rounded text-neutral-700 dark:text-neutral-300 border border-neutral-300 dark:border-neutral-700">
                        14 Verified Nodes • 19 Edges
                      </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-center">
                      <div className="rounded-xl border border-neutral-300 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900/60 p-3">
                        <p className="text-[10px] uppercase tracking-wider text-neutral-500 font-bold">Client Tier</p>
                        <p className="mt-1 font-bold text-neutral-900 dark:text-white">Next.js Web + Mobile</p>
                        <span className="inline-block mt-2 text-[10px] text-neutral-500">HTTPS / WebSocket</span>
                      </div>
                      <div className="rounded-xl border border-black dark:border-white bg-neutral-100 dark:bg-neutral-800/80 p-3">
                        <p className="text-[10px] uppercase tracking-wider text-neutral-700 dark:text-neutral-300 font-bold">API Gateway</p>
                        <p className="mt-1 font-bold text-neutral-900 dark:text-white">Kong Gateway + OIDC</p>
                        <span className="inline-block mt-2 text-[10px] text-neutral-500">Rate Limit / JWT Auth</span>
                      </div>
                      <div className="rounded-xl border border-neutral-300 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900/60 p-3">
                        <p className="text-[10px] uppercase tracking-wider text-neutral-500 font-bold">Microservices</p>
                        <p className="mt-1 font-bold text-neutral-900 dark:text-white">Auth, Event & Queue</p>
                        <span className="inline-block mt-2 text-[10px] text-neutral-500">gRPC & Kafka Broker</span>
                      </div>
                      <div className="rounded-xl border border-neutral-300 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900/60 p-3">
                        <p className="text-[10px] uppercase tracking-wider text-neutral-500 font-bold">Persistence</p>
                        <p className="mt-1 font-bold text-neutral-900 dark:text-white">PostgreSQL + Redis</p>
                        <span className="inline-block mt-2 text-[10px] text-neutral-500">Read Replicas / Cache</span>
                      </div>
                    </div>
                  </div>
                )}

                {activePreviewTab === "terminal" && (
                  <div className="w-full space-y-1.5 text-neutral-700 dark:text-neutral-300">
                    <p className="font-bold text-black dark:text-white">[00:00:01] ⚡ [CLIENT] Problem statement ingested: "High-throughput real-time event analytics"</p>
                    <p>[00:00:02] 🧠 [REE Engine] Launching stakeholder clarification interview (5 questions initialized)</p>
                    <p className="text-neutral-500 dark:text-neutral-400">[00:00:04] ✓ [REE Engine] Clarifications resolved: SLA 99.99%, RTO 15m, 25k QPS peak</p>
                    <p className="font-bold text-black dark:text-white">[00:00:05] 🚀 [SAE Engine] Synthesizing ARSRS specification and generating HLD topology...</p>
                    <p>[00:00:07] ✓ [SAE Engine] ARSRS spec completed & HLD graph compiled (14 nodes, 19 edges)</p>
                    <p className="text-neutral-500 dark:text-neutral-400">[00:00:08] ⚡ [LLD Dispatcher] Spawning 5 parallel design generators (Backend, Frontend, DB, Security, Cloud)</p>
                  </div>
                )}

                {activePreviewTab === "arsrs" && (
                  <div className="w-full space-y-2 text-neutral-800 dark:text-neutral-200">
                    <p className="font-bold text-black dark:text-white"># ARCHITECTURE-READY STRUCTURED REQUIREMENTS SPECIFICATION</p>
                    <p className="text-neutral-500">// Standard: ISO/IEC/IEEE 29148:2018 | Verification: SAE v2.5</p>
                    <p><span className="font-bold text-black dark:text-white">SYSTEM_TARGET:</span> Distributed Event-Driven Architecture</p>
                    <p><span className="font-bold text-black dark:text-white">AVAILABILITY:</span> Multi-AZ active-passive with automatic health failover</p>
                    <p><span className="font-bold text-black dark:text-white">THROUGHPUT:</span> 25,000 sustained queries/sec with sub-50ms p99 latency</p>
                    <p><span className="font-bold text-black dark:text-white">SECURITY:</span> Zero Trust perimeter, mutual TLS (mTLS) service-to-service, OAuth2/OIDC</p>
                  </div>
                )}
              </div>
            </div>

            {/* Metrics Bar */}
            <div className="mt-16 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {metrics.map((m, idx) => (
                <div
                  key={idx}
                  className="monochrome-card rounded-2xl p-6 text-left backdrop-blur-md"
                >
                  <div className="text-3xl font-extrabold text-black dark:text-white font-heading">
                    {m.value}
                  </div>
                  <div className="mt-1 text-sm font-bold text-neutral-900 dark:text-white font-heading">
                    {m.label}
                  </div>
                  <div className="mt-2 text-xs leading-relaxed text-neutral-500 dark:text-neutral-400">
                    {m.detail}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════════════════════════════════════════
            SECTION 2: ABOUT
        ════════════════════════════════════════════════════════════════════════════════════════════ */}
        <section id="about" className="relative py-20 md:py-28 border-t border-neutral-200 dark:border-neutral-800">
          <div className="mx-auto max-w-6xl px-4">
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-neutral-300 bg-neutral-100 px-3.5 py-1 text-xs font-bold uppercase tracking-widest text-neutral-800 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-200 mb-3">
                <Layers className="h-3.5 w-3.5" />
                <span>About ArchAI</span>
              </div>
              <h2 className="font-heading text-3xl font-extrabold sm:text-5xl tracking-tight">
                The End of Architecture Paralysis
              </h2>
              <p className="mt-4 text-base sm:text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto leading-relaxed">
                Engineering teams spend weeks trapped in whiteboard meetings, debating ambiguous RFCs, and maintaining stale diagrams. ArchAI replaces subjective guesswork with formal multi-agent synthesis.
              </p>
            </div>

            {/* The Dual-Engine Core Bento */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* REE Card */}
              <div className="monochrome-card rounded-3xl p-8 lg:p-10 relative overflow-hidden">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-black text-white dark:bg-white dark:text-black shadow-md">
                    <Sparkles className="h-6 w-6" />
                  </div>
                  <span className="rounded-full border border-neutral-300 bg-neutral-100 px-3 py-1 text-xs font-bold text-neutral-800 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200">
                    Core Engine 01
                  </span>
                </div>

                <h3 className="font-heading text-2xl font-bold">
                  REE: Requirements Engineering Engine
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-neutral-600 dark:text-neutral-400">
                  Natural language problem statements are inherently ambiguous. REE acts as your principal systems engineer, executing an adaptive stakeholder interview to systematically uncover every critical requirement before a single line of architecture is generated.
                </p>

                <div className="mt-6 space-y-3">
                  <div className="flex items-start gap-3 text-xs text-neutral-700 dark:text-neutral-300">
                    <CheckCircle2 className="h-4 w-4 text-black dark:text-white shrink-0 mt-0.5" />
                    <span><strong>Proactive Ambiguity Probing:</strong> Automatically questions concurrency, peak traffic, storage retention, and compliance requirements.</span>
                  </div>
                  <div className="flex items-start gap-3 text-xs text-neutral-700 dark:text-neutral-300">
                    <CheckCircle2 className="h-4 w-4 text-black dark:text-white shrink-0 mt-0.5" />
                    <span><strong>Quantitative SLA & NFR Mapping:</strong> Determines strict availability targets (99.9% vs 99.99%), recovery time objectives, and data residency.</span>
                  </div>
                  <div className="flex items-start gap-3 text-xs text-neutral-700 dark:text-neutral-300">
                    <CheckCircle2 className="h-4 w-4 text-black dark:text-white shrink-0 mt-0.5" />
                    <span><strong>Adaptive Multiple-Choice & Custom Inputs:</strong> Provides recommended defaults with full keyboard shortcut velocity.</span>
                  </div>
                </div>
              </div>

              {/* SAE Card */}
              <div className="monochrome-card rounded-3xl p-8 lg:p-10 relative overflow-hidden">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-black text-white dark:bg-white dark:text-black shadow-md">
                    <Network className="h-6 w-6" />
                  </div>
                  <span className="rounded-full border border-neutral-300 bg-neutral-100 px-3 py-1 text-xs font-bold text-neutral-800 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200">
                    Core Engine 02
                  </span>
                </div>

                <h3 className="font-heading text-2xl font-bold">
                  SAE: System Architecture Engine
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-neutral-600 dark:text-neutral-400">
                  Once requirements are locked, SAE performs domain-driven system decomposition, mapping microservices, data pipelines, caching tiers, and cloud primitives into verifiable High-Level and Low-Level architecture specifications.
                </p>

                <div className="mt-6 space-y-3">
                  <div className="flex items-start gap-3 text-xs text-neutral-700 dark:text-neutral-300">
                    <CheckCircle2 className="h-4 w-4 text-black dark:text-white shrink-0 mt-0.5" />
                    <span><strong>ISO/IEEE Specification Synthesis:</strong> Generates formal ARSRS documents with clear functional constraints and executive summaries.</span>
                  </div>
                  <div className="flex items-start gap-3 text-xs text-neutral-700 dark:text-neutral-300">
                    <CheckCircle2 className="h-4 w-4 text-black dark:text-white shrink-0 mt-0.5" />
                    <span><strong>Interactive Graph Topology:</strong> Renders visual React Flow flowcharts with layer filtering and node-level inspection.</span>
                  </div>
                  <div className="flex items-start gap-3 text-xs text-neutral-700 dark:text-neutral-300">
                    <CheckCircle2 className="h-4 w-4 text-black dark:text-white shrink-0 mt-0.5" />
                    <span><strong>5 Concurrent LLD Blueprints:</strong> Parallel generation across Backend, Frontend, Database, Security, and Cloud domains.</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Architecture Principles */}
            <div className="mt-12 rounded-3xl border border-neutral-300 dark:border-neutral-800 bg-neutral-100/70 dark:bg-neutral-900/50 p-8 lg:p-10 backdrop-blur-md">
              <h4 className="font-heading text-xl font-bold text-neutral-900 dark:text-white mb-6">
                Our Foundational Architectural Principles
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h5 className="font-heading font-bold text-black dark:text-white text-sm">
                    Deterministic & Reproducible
                  </h5>
                  <p className="mt-2 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
                    Architectural decisions are backed by formal requirements models rather than random stochastic hallucinations. Same inputs yield verified blueprints.
                  </p>
                </div>
                <div>
                  <h5 className="font-heading font-bold text-black dark:text-white text-sm">
                    Zero-Trust & Security-First
                  </h5>
                  <p className="mt-2 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
                    Every synthesized architecture defaults to strict mTLS communication, least-privilege RBAC matrices, and cryptographic identity boundaries.
                  </p>
                </div>
                <div>
                  <h5 className="font-heading font-bold text-black dark:text-white text-sm">
                    Cloud-Agnostic Velocity
                  </h5>
                  <p className="mt-2 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
                    Export blueprints ready for Kubernetes, AWS, Google Cloud, Azure, or bare metal without proprietary vendor lock-in.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════════════════════════════════════════
            SECTION 3: SERVICES (ROADMAP PIPELINE)
        ════════════════════════════════════════════════════════════════════════════════════════════ */}
        <section id="services" className="relative py-20 md:py-32 border-t border-neutral-200 dark:border-neutral-800 overflow-hidden">
          <div className="mx-auto max-w-6xl px-4">
            <div className="text-center mb-16 md:mb-20">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-neutral-300 bg-neutral-100 px-3.5 py-1 text-xs font-bold uppercase tracking-widest text-neutral-800 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-200 mb-3 shadow-2xs">
                <Zap className="h-3.5 w-3.5" />
                <span>Our Capabilities • 6 Continuous Stages</span>
              </div>
              <h2 className="font-heading text-3xl font-extrabold sm:text-5xl tracking-tight">
                Full-Lifecycle Architecture Pipeline
              </h2>
              <p className="mt-4 text-base sm:text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto leading-relaxed">
                From interactive requirement clarification to production-ready low-level architecture modules across every engineering layer.
              </p>
            </div>

            {/* Zigzag Pinned Cards Pipeline Container */}
            <div className="relative max-w-5xl mx-auto px-2 sm:px-4">
              {/* Dashed Zigzag Connector Line for Desktop */}
              <svg
                className="absolute inset-0 w-full h-full pointer-events-none hidden md:block z-0"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
              >
                <path
                  d="M 27 6 L 73 23 L 27 41 L 73 59 L 27 77 L 73 94"
                  fill="none"
                  stroke="currentColor"
                  className="text-neutral-400 dark:text-neutral-700"
                  strokeWidth="2"
                  strokeDasharray="2.5 2.5"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>

              {/* Step Transition Arrow Indicators (Desktop) */}
              {stepTransitions.map((trans, tIdx) => (
                <div
                  key={tIdx}
                  className="hidden md:flex absolute left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 items-center justify-center pointer-events-none"
                  style={{ top: trans.top }}
                >
                  <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-neutral-300 dark:border-neutral-800 bg-white/95 dark:bg-[#0c0c0c]/95 shadow-md backdrop-blur-md">
                    <span className="font-mono text-[10px] font-bold text-neutral-500 dark:text-neutral-400">
                      Step {trans.from}
                    </span>
                    <div
                      className="flex items-center justify-center w-5 h-5 rounded-full bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-2xs"
                      style={{ color: trans.color }}
                    >
                      {trans.direction === "down-right" ? (
                        <ArrowDownRight className="h-3.5 w-3.5" />
                      ) : (
                        <ArrowDownLeft className="h-3.5 w-3.5" />
                      )}
                    </div>
                    <span className="font-mono text-[10px] font-bold" style={{ color: trans.color }}>
                      Step {trans.to}
                    </span>
                  </div>
                </div>
              ))}

              {/* Vertical Dashed Line for Mobile Background */}
              <div className="absolute left-1/2 -translate-x-1/2 top-10 bottom-10 w-0.5 border-l-2 border-dashed border-neutral-300 dark:border-neutral-700 md:hidden z-0" />

              {/* Cards Flow */}
              <div className="relative z-10 flex flex-col gap-6 md:gap-0">
                {services.map((s, idx) => {
                  const Icon = s.icon;
                  const isEven = idx % 2 === 0;

                  return (
                    <div key={idx} className="w-full flex flex-col">
                      <div
                        className={`relative z-10 w-full md:w-[420px] lg:w-[450px] transition-all duration-300 group ${
                          isEven
                            ? "md:self-start md:ml-4 lg:ml-10"
                            : "md:self-end md:mr-4 lg:mr-10"
                        } ${idx > 0 ? "md:-mt-20 lg:-mt-24" : ""}`}
                      >
                        <div
                          className={`transform transition-all duration-300 ease-out ${s.rotation} group-hover:rotate-0 group-hover:scale-[1.02] group-hover:z-20`}
                        >
                          {/* Card outer paper */}
                          <div className="relative rounded-[28px] bg-white dark:bg-[#141414] p-3 sm:p-4 border border-neutral-200/85 dark:border-neutral-800 shadow-[0_15px_35px_-5px_rgba(0,0,0,0.08),0_5px_15px_rgba(0,0,0,0.04)] dark:shadow-[0_15px_35px_-5px_rgba(0,0,0,0.6),0_0_1px_1px_rgba(255,255,255,0.08)]">
                            {/* Push Pin pinned at top center */}
                            <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-30">
                              <PushPin color={s.pinColor} />
                            </div>

                            {/* Inner tinted paper surface */}
                            <div
                              className={`rounded-2xl p-6 sm:p-7 border ${s.innerBg} ${s.innerBorder} transition-colors`}
                            >
                              {/* Top row: Step number and Domain Badge */}
                              <div className="flex items-center justify-between mb-4">
                                <span
                                  className={`font-heading text-3xl sm:text-4xl font-extrabold tracking-tight ${s.numberColor}`}
                                >
                                  {s.step}
                                </span>
                                <div
                                  className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-bold border shadow-2xs ${s.badgeBg}`}
                                >
                                  <Icon className="h-3.5 w-3.5" />
                                  <span>{s.badge}</span>
                                </div>
                              </div>

                              {/* Title */}
                              <h3 className="font-heading text-lg sm:text-xl font-extrabold text-neutral-900 dark:text-neutral-100 tracking-tight leading-snug">
                                {s.title}
                              </h3>

                              {/* Description */}
                              <p className="mt-2.5 text-xs sm:text-sm text-neutral-600 dark:text-neutral-300 leading-relaxed">
                                {s.desc}
                              </p>

                              {/* Feature Bullets */}
                              <div className="mt-5 space-y-2 border-t border-neutral-200/70 dark:border-neutral-800/80 pt-4">
                                {s.features.map((feat, fidx) => (
                                  <div
                                    key={fidx}
                                    className="flex items-start gap-2.5 text-xs font-medium text-neutral-700 dark:text-neutral-300"
                                  >
                                    <Check
                                      className="h-3.5 w-3.5 shrink-0 mt-0.5"
                                      style={{ color: s.pinColor }}
                                    />
                                    <span>{feat}</span>
                                  </div>
                                ))}
                              </div>

                              {/* Bottom Action Footer */}
                              <div className="mt-5 pt-3.5 border-t border-neutral-200/70 dark:border-neutral-800/80 flex items-center justify-between">
                                <Link
                                  href="/chat"
                                  className="inline-flex items-center gap-1.5 text-xs font-bold text-neutral-900 dark:text-white hover:underline group/link"
                                >
                                  <span>Generate in Studio</span>
                                  <ArrowRight
                                    className="h-3.5 w-3.5 transition-transform duration-200 group-hover/link:translate-x-1"
                                    style={{ color: s.pinColor }}
                                  />
                                </Link>
                                <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-400 dark:text-neutral-500 font-semibold">
                                  Step {s.step} / 06
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Mobile Connector with Arrow Mark between steps */}
                      {idx < services.length - 1 && (
                        <div className="flex md:hidden flex-col items-center justify-center py-2 z-10">
                          <div className="w-0.5 h-4 border-l-2 border-dashed border-neutral-300 dark:border-neutral-700" />
                          <div className="flex items-center gap-1.5 px-3 py-1 my-1 rounded-full border border-neutral-300 dark:border-neutral-800 bg-white dark:bg-[#0c0c0c] shadow-xs text-xs font-bold">
                            <span className="font-mono text-[10px] text-neutral-400">Step {s.step}</span>
                            <ArrowDown className="h-3 w-3 text-neutral-700 dark:text-neutral-300 animate-bounce" />
                            <span className="font-mono text-[10px] text-neutral-400">Step {services[idx + 1].step}</span>
                          </div>
                          <div className="w-0.5 h-4 border-l-2 border-dashed border-neutral-300 dark:border-neutral-700" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>



        {/* ════════════════════════════════════════════════════════════════════════════════════════════
            FOOTER (WITH ANIMATED BLUR IN VIEW CONTAINER)
        ════════════════════════════════════════════════════════════════════════════════════════════ */}
        <footer className="relative w-full border-t border-neutral-200 dark:border-neutral-800 py-12 lg:py-16 overflow-hidden">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
              <AnimatedContainer delay={0.1} className="space-y-4">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-black text-white dark:bg-white dark:text-black shadow-sm">
                    <Cpu className="h-4 w-4" />
                  </div>
                  <span className="font-heading font-extrabold text-base tracking-tight">
                    Arch<span className="text-neutral-500 dark:text-neutral-400">AI</span>
                  </span>
                </div>
                <p className="text-xs text-neutral-500 leading-relaxed">
                  Autonomous multi-agent system architecture generation platform for modern engineering teams.
                </p>
                <div className="flex items-center gap-2 text-xs font-semibold text-neutral-800 dark:text-neutral-200">
                  <span className="h-2 w-2 rounded-full bg-black dark:bg-white animate-pulse" />
                  <span>All Systems Operational</span>
                </div>
              </AnimatedContainer>

              <AnimatedContainer delay={0.2} className="space-y-3">
                <h4 className="font-heading text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-white mb-3">
                  Architecture Engines
                </h4>
                <ul className="space-y-2 text-xs text-neutral-500 dark:text-neutral-400">
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">Requirements Engine (REE)</a></li>
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">Visual HLD Generator</a></li>
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">5 Domain LLD Blueprints</a></li>
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">ARSRS Specification Synthesis</a></li>
                </ul>
              </AnimatedContainer>

              <AnimatedContainer delay={0.3} className="space-y-3">
                <h4 className="font-heading text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-white mb-3">
                  Navigation
                </h4>
                <ul className="space-y-2 text-xs text-neutral-500 dark:text-neutral-400">
                  <li><a href="#home" className="hover:text-black dark:hover:text-white transition-colors">Home</a></li>
                  <li><a href="#about" className="hover:text-black dark:hover:text-white transition-colors">About</a></li>
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">Services</a></li>
                  <li><Link href="/chat" className="hover:text-black dark:hover:text-white transition-colors">Studio App</Link></li>
                </ul>
              </AnimatedContainer>

              <AnimatedContainer delay={0.4} className="space-y-3">
                <h4 className="font-heading text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-white mb-3">
                  Security & Standards
                </h4>
                <ul className="space-y-2 text-xs text-neutral-500 dark:text-neutral-400">
                  <li>ISO/IEC/IEEE 29148:2018</li>
                  <li>OWASP Top 10 Zero Trust</li>
                  <li>OpenAPI 3.1 & AsyncAPI</li>
                  <li>Strict Cloud IaC Standards</li>
                </ul>
              </AnimatedContainer>
            </div>

            <AnimatedContainer delay={0.5} className="border-t border-neutral-200 dark:border-neutral-800 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-neutral-500">
              <p>&copy; 2026 ArchAI Architecture Engine. All rights reserved.</p>
              <p className="mt-2 sm:mt-0 font-mono text-[11px]">Designed with UI-UX Pro Max • Pure Black & White Architecture</p>
            </AnimatedContainer>
          </div>
        </footer>
      </div>
    </div>
  );
}
