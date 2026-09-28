"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Cpu,
  Sparkles,
  Network,
  Boxes,
  Terminal,
  ShieldCheck,
  Server,
  Cloud,
  Database,
  ArrowRight,
  Zap,
  CheckCircle2,
  Code2,
  Lock,
  Layers,
  Send,
  MessageSquare,
  ChevronRight,
  ExternalLink,
  Sliders,
  Check,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import BubbleBg from "@/components/BubbleBg";

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
    icon: MessageSquare,
    title: "Stakeholder Clarification Interview (REE)",
    badge: "Requirements Engine",
    desc: "Autonomous multi-turn interview that proactively identifies edge cases, availability requirements, quantitative throughput metrics, and regulatory constraints.",
    features: [
      "Dynamic multi-turn stakeholder questioning",
      "Quantitative SLA, RTO, and RPO calculation",
      "Automated ambiguity resolution from natural language",
    ],
  },
  {
    icon: Sparkles,
    title: "Formal ARSRS Specification Document",
    badge: "Specification Synthesis",
    desc: "Generates an Architecture-Ready Structured Requirements Specification document adhering to formal IEEE/ISO software engineering standards.",
    features: [
      "Comprehensive functional & non-functional requirements",
      "Executive summary & architectural constraints",
      "One-click JSON and Markdown specification export",
    ],
  },
  {
    icon: Network,
    title: "Interactive High-Level Design (HLD)",
    badge: "Visual Topology",
    desc: "Synthesizes an interactive, zoomable React Flow topology graph mapping clients, API gateways, microservices, databases, caches, and cloud infrastructure.",
    features: [
      "Real-time node drawer inspector with deep metadata",
      "Layer filtering: Client, Gateway, Services, Storage, Infra",
      "Animated protocol flows (REST, gRPC, WebSocket, Kafka)",
    ],
  },
  {
    icon: Server,
    title: "Backend & Microservices LLD",
    badge: "Execution Architecture",
    desc: "Synthesizes low-level backend service architecture including API schemas, internal gRPC contracts, message queues, and async worker choreography.",
    features: [
      "REST & gRPC endpoint contracts",
      "Event-driven Kafka & RabbitMQ choreography",
      "Service isolation, circuit breakers & idempotency rules",
    ],
  },
  {
    icon: Database,
    title: "Database, Schemas & Sharding LLD",
    badge: "Data Layer",
    desc: "Architects the complete persistence tier with relational schemas, NoSQL document collections, caching strategies, and partition models.",
    features: [
      "Entity-relationship schemas with indexing strategies",
      "Read/Write replica topology & Redis cache invalidation",
      "ACID vs BASE consistency models & sharding keys",
    ],
  },
  {
    icon: ShieldCheck,
    title: "Security, Cloud & Multi-Region LLD",
    badge: "Zero Trust & Infra",
    desc: "Enforces enterprise Zero Trust authentication, fine-grained RBAC matrices, Kubernetes cluster topologies, and multi-region disaster recovery.",
    features: [
      "OAuth2, OIDC, JWT & mTLS cryptographic flows",
      "Kubernetes pod topology & Terraform IaC blueprints",
      "Multi-region failover, DNS routing & automated backups",
    ],
  },
];

export default function LandingPage() {
  const [activePreviewTab, setActivePreviewTab] = useState<"topology" | "terminal" | "arsrs">("topology");
  
  // Contact Form State
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [contactForm, setContactForm] = useState({
    name: "",
    email: "",
    scope: "Enterprise Microservices",
    cloud: "AWS",
    message: "",
  });

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormSubmitted(true);
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
                    className={`rounded-md px-3 py-1 transition-all ${
                      activePreviewTab === "topology"
                        ? "bg-black text-white dark:bg-white dark:text-black shadow-xs"
                        : "text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
                    }`}
                  >
                    HLD Topology Map
                  </button>
                  <button
                    onClick={() => setActivePreviewTab("terminal")}
                    className={`rounded-md px-3 py-1 transition-all ${
                      activePreviewTab === "terminal"
                        ? "bg-black text-white dark:bg-white dark:text-black shadow-xs"
                        : "text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
                    }`}
                  >
                    SSE Execution Log
                  </button>
                  <button
                    onClick={() => setActivePreviewTab("arsrs")}
                    className={`rounded-md px-3 py-1 transition-all ${
                      activePreviewTab === "arsrs"
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
            SECTION 3: SERVICES
        ════════════════════════════════════════════════════════════════════════════════════════════ */}
        <section id="services" className="relative py-20 md:py-28 border-t border-neutral-200 dark:border-neutral-800">
          <div className="mx-auto max-w-6xl px-4">
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-neutral-300 bg-neutral-100 px-3.5 py-1 text-xs font-bold uppercase tracking-widest text-neutral-800 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-200 mb-3">
                <Zap className="h-3.5 w-3.5" />
                <span>Our Capabilities</span>
              </div>
              <h2 className="font-heading text-3xl font-extrabold sm:text-5xl tracking-tight">
                Full-Lifecycle Architecture Services
              </h2>
              <p className="mt-4 text-base sm:text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto leading-relaxed">
                From interactive requirement clarification to production-ready low-level architecture modules across every engineering layer.
              </p>
            </div>

            {/* 6 Services Bento Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {services.map((s, idx) => {
                const Icon = s.icon;
                return (
                  <div
                    key={idx}
                    className="monochrome-card rounded-2xl p-7 flex flex-col justify-between group backdrop-blur-md"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-5">
                        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-black text-white dark:bg-white dark:text-black shadow-sm transition-transform duration-200 group-hover:scale-105">
                          <Icon className="h-5 w-5" />
                        </div>
                        <span className="rounded-full border border-neutral-300 bg-neutral-100 px-2.5 py-0.5 text-[11px] font-bold text-neutral-700 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300">
                          {s.badge}
                        </span>
                      </div>

                      <h3 className="font-heading text-lg font-bold text-neutral-900 dark:text-white">
                        {s.title}
                      </h3>
                      <p className="mt-2 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
                        {s.desc}
                      </p>

                      <div className="mt-5 space-y-2 border-t border-neutral-200 dark:border-neutral-800 pt-4">
                        {s.features.map((feat, fidx) => (
                          <div key={fidx} className="flex items-start gap-2 text-xs text-neutral-700 dark:text-neutral-300">
                            <Check className="h-3.5 w-3.5 text-black dark:text-white shrink-0 mt-0.5" />
                            <span>{feat}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-neutral-200 dark:border-neutral-800">
                      <Link
                        href="/chat"
                        className="inline-flex items-center gap-1 text-xs font-bold text-black dark:text-white hover:underline"
                      >
                        <span>Generate in Studio</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════════════════════════════════════════
            SECTION 4: CONTACT & CONSULTATION
        ════════════════════════════════════════════════════════════════════════════════════════════ */}
        <section id="contact" className="relative py-20 md:py-28 border-t border-neutral-200 dark:border-neutral-800">
          <div className="mx-auto max-w-6xl px-4">
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-neutral-300 bg-neutral-100 px-3.5 py-1 text-xs font-bold uppercase tracking-widest text-neutral-800 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-200 mb-3">
                <Send className="h-3.5 w-3.5" />
                <span>Contact & Consultation</span>
              </div>
              <h2 className="font-heading text-3xl font-extrabold sm:text-5xl tracking-tight">
                Consult With Our Systems Architects
              </h2>
              <p className="mt-4 text-base sm:text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto leading-relaxed">
                Have custom compliance, high-throughput SLAs, or enterprise on-premises deployment needs? Our team is ready to assist.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
              {/* Contact Information Column */}
              <div className="lg:col-span-5 space-y-6">
                <div className="monochrome-card rounded-3xl p-8 backdrop-blur-md">
                  <h3 className="font-heading text-xl font-bold">
                    Direct Engineering Channels
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
                    Reach out for dedicated enterprise POCs, custom LLM fine-tuning on proprietary architecture patterns, or security evaluations.
                  </p>

                  <div className="mt-6 space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 dark:bg-neutral-900 text-black dark:text-white border border-neutral-300 dark:border-neutral-800">
                        <Terminal className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-xs font-bold text-neutral-900 dark:text-white">Architecture Advisory</p>
                        <p className="text-xs text-neutral-500">architects@archai.engine</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 dark:bg-neutral-900 text-black dark:text-white border border-neutral-300 dark:border-neutral-800">
                        <ShieldCheck className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-xs font-bold text-neutral-900 dark:text-white">Security & Compliance</p>
                        <p className="text-xs text-neutral-500">compliance@archai.engine</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 dark:bg-neutral-900 text-black dark:text-white border border-neutral-300 dark:border-neutral-800">
                        <ExternalLink className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-xs font-bold text-neutral-900 dark:text-white">GitHub Community</p>
                        <p className="text-xs text-neutral-500">github.com/archai-project</p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-8 rounded-2xl border border-neutral-300 dark:border-neutral-800 bg-neutral-100/70 dark:bg-neutral-900/50 p-4">
                    <p className="text-xs font-bold text-black dark:text-white">
                      ⚡ 24/7 Enterprise Availability
                    </p>
                    <p className="mt-1 text-[11px] text-neutral-600 dark:text-neutral-400">
                      Enterprise tier includes custom private VPC deployments, strict SOC 2 Type II compliance, and dedicated architecture reviews.
                    </p>
                  </div>
                </div>
              </div>

              {/* Interactive Inquiry Form */}
              <div className="lg:col-span-7">
                <div className="monochrome-card rounded-3xl p-8 lg:p-10 backdrop-blur-md">
                  {formSubmitted ? (
                    <div className="py-12 text-center space-y-4">
                      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-black text-white dark:bg-white dark:text-black shadow-lg">
                        <CheckCircle2 className="h-8 w-8" />
                      </div>
                      <h3 className="font-heading text-2xl font-bold">
                        Inquiry Received
                      </h3>
                      <p className="text-sm text-neutral-600 dark:text-neutral-400 max-w-md mx-auto">
                        Thank you, <strong>{contactForm.name}</strong>. A principal systems architect has been assigned to your brief and will respond within 24 hours.
                      </p>
                      <button
                        onClick={() => setFormSubmitted(false)}
                        className="mt-4 rounded-full border border-neutral-300 dark:border-neutral-700 px-6 py-2 text-xs font-semibold text-neutral-800 dark:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-900"
                      >
                        Submit Another Inquiry
                      </button>
                    </div>
                  ) : (
                    <form onSubmit={handleContactSubmit} className="space-y-4">
                      <h3 className="font-heading text-xl font-bold mb-4">
                        Schedule an Architecture Review
                      </h3>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-1">
                            Your Name *
                          </label>
                          <input
                            type="text"
                            required
                            value={contactForm.name}
                            onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                            placeholder="Alex Morgan"
                            className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs text-neutral-900 placeholder:text-neutral-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white dark:focus:border-white dark:focus:ring-white/10"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-1">
                            Work Email *
                          </label>
                          <input
                            type="email"
                            required
                            value={contactForm.email}
                            onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                            placeholder="alex@company.com"
                            className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs text-neutral-900 placeholder:text-neutral-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white dark:focus:border-white dark:focus:ring-white/10"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-1">
                            Architecture Scope
                          </label>
                          <select
                            value={contactForm.scope}
                            onChange={(e) => setContactForm({ ...contactForm, scope: e.target.value })}
                            className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs text-neutral-900 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white dark:focus:border-white"
                          >
                            <option>Enterprise Microservices</option>
                            <option>High-Throughput Fintech / Banking</option>
                            <option>Real-Time IoT & Streaming</option>
                            <option>AI / LLM Multi-Agent System</option>
                            <option>Legacy Monolith Cloud Migration</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-1">
                            Primary Cloud Target
                          </label>
                          <select
                            value={contactForm.cloud}
                            onChange={(e) => setContactForm({ ...contactForm, cloud: e.target.value })}
                            className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs text-neutral-900 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white dark:focus:border-white"
                          >
                            <option>Amazon Web Services (AWS)</option>
                            <option>Google Cloud Platform (GCP)</option>
                            <option>Microsoft Azure</option>
                            <option>Bare-Metal / Hybrid Kubernetes</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-1">
                          Project Brief & Concurrency Constraints *
                        </label>
                        <textarea
                          rows={4}
                          required
                          value={contactForm.message}
                          onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                          placeholder="Describe the system, target peak QPS, consistency needs (ACID vs Eventual), or regulatory requirements..."
                          className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs text-neutral-900 placeholder:text-neutral-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white dark:focus:border-white resize-none"
                        />
                      </div>

                      <button
                        type="submit"
                        className="w-full flex items-center justify-center gap-2 rounded-xl bg-black text-white dark:bg-white dark:text-black py-3 text-xs font-bold shadow-md transition-all hover:bg-neutral-800 dark:hover:bg-neutral-200"
                      >
                        <Send className="h-4 w-4" />
                        <span>Submit Architecture Consultation Request</span>
                      </button>
                    </form>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════════════════════════════════════════════
            FOOTER
        ════════════════════════════════════════════════════════════════════════════════════════════ */}
        <footer className="border-t border-neutral-200 dark:border-neutral-800 py-12 bg-neutral-50/50 dark:bg-neutral-950/50 backdrop-blur-md">
          <div className="mx-auto max-w-6xl px-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
              <div className="space-y-3">
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
              </div>

              <div>
                <h4 className="font-heading text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-white mb-3">
                  Architecture Engines
                </h4>
                <ul className="space-y-2 text-xs text-neutral-500 dark:text-neutral-400">
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">Requirements Engine (REE)</a></li>
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">Visual HLD Generator</a></li>
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">5 Domain LLD Blueprints</a></li>
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">ARSRS Specification Synthesis</a></li>
                </ul>
              </div>

              <div>
                <h4 className="font-heading text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-white mb-3">
                  Navigation
                </h4>
                <ul className="space-y-2 text-xs text-neutral-500 dark:text-neutral-400">
                  <li><a href="#home" className="hover:text-black dark:hover:text-white transition-colors">Home</a></li>
                  <li><a href="#about" className="hover:text-black dark:hover:text-white transition-colors">About</a></li>
                  <li><a href="#services" className="hover:text-black dark:hover:text-white transition-colors">Services</a></li>
                  <li><a href="#contact" className="hover:text-black dark:hover:text-white transition-colors">Contact</a></li>
                  <li><Link href="/chat" className="hover:text-black dark:hover:text-white transition-colors">Studio App</Link></li>
                </ul>
              </div>

              <div>
                <h4 className="font-heading text-xs font-bold uppercase tracking-wider text-neutral-900 dark:text-white mb-3">
                  Security & Standards
                </h4>
                <ul className="space-y-2 text-xs text-neutral-500 dark:text-neutral-400">
                  <li>ISO/IEC/IEEE 29148:2018</li>
                  <li>OWASP Top 10 Zero Trust</li>
                  <li>OpenAPI 3.1 & AsyncAPI</li>
                  <li>Strict Cloud IaC Standards</li>
                </ul>
              </div>
            </div>

            <div className="border-t border-neutral-200 dark:border-neutral-800 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-neutral-500">
              <p>&copy; 2026 ArchAI Architecture Engine. All rights reserved.</p>
              <p className="mt-2 sm:mt-0 font-mono text-[11px]">Designed with UI-UX Pro Max • Pure Black & White Architecture</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
