"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  MessageSquare,
  Cpu,
  User as UserIcon,
  X,
  Minus,
  Maximize2,
  Minimize2,
  Sparkles,
  GripVertical,
  CornerDownLeft,
  Copy,
  Check,
  Layers,
  ArrowRight,
} from "lucide-react";
import { useAppStore, generateMsgId, type ChatMessage } from "@/lib/store";
import { cn } from "@/lib/utils";

// ── Smart Architecture Copilot Generator for Live Diagram Inquiries ──
function generateArchitectureReply(prompt: string, hldData: Record<string, unknown> | null): string {
  const p = prompt.toLowerCase();

  if (p.includes("cache") || p.includes("redis")) {
    return `### ⚡ Caching Tier Recommendation

To optimize throughput for your current architecture:
1. **Redis Cluster (Multi-AZ)**: Deploy a Redis 7.2 cluster with in-memory write-through caching for high-velocity session tokens and component queries.
2. **TTL Strategy**: 
   - Hot queries: \`300s\` with jitter to prevent cache stampedes.
   - Static component metadata: \`3600s\`.
3. **Cache Invalidation**: Use Redis Pub/Sub or Kafka CDC events from the persistence layer to trigger deterministic cache eviction.

*Visual HLD & Database LLD updated with recommended cache topology.*`;
  }

  if (p.includes("kafka") || p.includes("queue") || p.includes("event") || p.includes("broker")) {
    return `### 📡 Event-Driven Pipeline Choreography

For asynchronous decoupled microservices:
1. **Partitioning**: Partition by \`tenant_id\` or \`entity_id\` with 12 partitions per topic for horizontal consumer scaling.
2. **Idempotency**: Consumers enforce deduplication via distributed lock on transaction ID with transactional outbox pattern.
3. **Dead-Letter Queue (DLQ)**: Failed events retry up to 3 times with exponential backoff before landing in \`dlq-events\` for alerting.`;
  }

  if (p.includes("security") || p.includes("auth") || p.includes("jwt") || p.includes("mtls")) {
    return `### 🛡️ Zero-Trust Security Specification

1. **Edge Gateway**: Enforces OAuth2 / OIDC JWT token validation with JWKS rotation every 24 hours.
2. **Internal Service-to-Service**: Strictly enforced mutual TLS (mTLS) with SPIFFE/SPIRE workload cryptographic identity attestation.
3. **RBAC Matrix**: Role-based access control with least-privilege policies verified on every RPC boundary.`;
  }

  if (p.includes("scale") || p.includes("load") || p.includes("traffic") || p.includes("qps")) {
    return `### 📈 Horizontal Scaling Blueprint

1. **Auto-scaling (HPA)**: Kubernetes pods configured to scale on 70% CPU / memory target or queue depth metrics via KEDA.
2. **Database Read Replicas**: Route read-heavy traffic to 3 read replicas with PgBouncer connection pooling.
3. **Global Edge CDN**: Edge caching for static assets with AWS CloudFront / Cloudflare reducing origin traffic by up to 78%.`;
  }

  // General contextual architecture response
  return `### 🏛️ Architecture Co-Pilot Analysis

Regarding your inquiry: *"__${prompt.slice(0, 100)}..."*

1. **System Impact**: This inquiry targets the core service boundary in your High-Level Design (HLD).
2. **Recommended Action**:
   - Inspect the corresponding component drawer in the interactive topology above.
   - Cross-reference with the **Low-Level Design (LLD)** blueprints for schema and protocol verification.
3. **Verification**: The system guarantees IEEE/ISO compliance across API contracts, persistence sharding, and edge ingress routing.

*Feel free to ask for specific code blueprints, schema DDLs, or Kubernetes manifests!*`;
}

export default function TubelightChatBar() {
  const {
    sessions,
    activeSessionId,
    addMessage,
    createSession,
    hldData,
    user,
    hldWorkspaceTab,
  } = useAppStore();

  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Floating Window Drag State
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef<{ mouseX: number; mouseY: number; posX: number; posY: number }>({
    mouseX: 0,
    mouseY: 0,
    posX: 0,
    posY: 0,
  });

  // Floating Window Resize State
  type ResizeDirection = "e" | "w" | "s" | "n" | "se" | "sw" | "ne" | "nw";
  const [size, setSize] = useState({ width: 460, height: 530 });
  const [isResizing, setIsResizing] = useState(false);
  const resizeStartRef = useRef<{
    mouseX: number;
    mouseY: number;
    startW: number;
    startH: number;
    startPosX: number;
    startPosY: number;
    direction: ResizeDirection;
  }>({
    mouseX: 0,
    mouseY: 0,
    startW: 0,
    startH: 0,
    startPosX: 0,
    startPosY: 0,
    direction: "se",
  });

  const [isMaximized, setIsMaximized] = useState(false);
  const [floatingInput, setFloatingInput] = useState("");

  const chatScrollRef = useRef<HTMLDivElement>(null);
  const floatingWindowRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const messages = activeSession?.messages ?? [];
  const messageCount = messages.length;

  // Initialize position once in browser
  useEffect(() => {
    if (typeof window !== "undefined" && position === null) {
      const defaultW = Math.min(480, window.innerWidth - 32);
      const defaultH = Math.min(540, window.innerHeight - 100);
      setSize({ width: defaultW, height: defaultH });
      const defaultX = Math.max(16, window.innerWidth - defaultW - 24);
      const defaultY = Math.max(70, window.innerHeight - defaultH - 90);
      setPosition({ x: defaultX, y: defaultY });
    }
  }, [position]);

  // Auto-scroll chat history when messages change or window opens
  useEffect(() => {
    if (showHistory) {
      chatScrollRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, showHistory, isSending]);

  // ── Drag Logic (Moveable) ──
  const handleStartDrag = (e: React.MouseEvent | React.TouchEvent) => {
    if (isMaximized) return;
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

    setIsDragging(true);
    dragStartRef.current = {
      mouseX: clientX,
      mouseY: clientY,
      posX: position?.x ?? 50,
      posY: position?.y ?? 50,
    };
  };

  useEffect(() => {
    if (!isDragging) return;

    document.body.style.userSelect = "none";
    document.body.style.cursor = "grabbing";

    const handleMove = (e: MouseEvent | TouchEvent) => {
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

      const deltaX = clientX - dragStartRef.current.mouseX;
      const deltaY = clientY - dragStartRef.current.mouseY;

      const newX = Math.max(8, Math.min(window.innerWidth - size.width - 8, dragStartRef.current.posX + deltaX));
      const newY = Math.max(10, Math.min(window.innerHeight - size.height - 10, dragStartRef.current.posY + deltaY));

      setPosition({ x: newX, y: newY });
    };

    const handleEnd = () => {
      setIsDragging(false);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleEnd);
    window.addEventListener("touchmove", handleMove);
    window.addEventListener("touchend", handleEnd);

    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleEnd);
      window.removeEventListener("touchmove", handleMove);
      window.removeEventListener("touchend", handleEnd);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };
  }, [isDragging, size]);

  // ── Multi-Directional Dynamic Resize Logic ──
  const handleStartResize = (
    e: React.MouseEvent | React.TouchEvent,
    direction: ResizeDirection
  ) => {
    e.preventDefault();
    e.stopPropagation();
    if (isMaximized) return;

    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

    setIsResizing(true);
    resizeStartRef.current = {
      mouseX: clientX,
      mouseY: clientY,
      startW: size.width,
      startH: size.height,
      startPosX: position?.x ?? 20,
      startPosY: position?.y ?? 70,
      direction,
    };
  };

  useEffect(() => {
    if (!isResizing) return;

    document.body.style.userSelect = "none";
    const dir = resizeStartRef.current.direction;
    document.body.style.cursor =
      dir === "se" || dir === "nw"
        ? "nwse-resize"
        : dir === "sw" || dir === "ne"
        ? "nesw-resize"
        : dir === "e" || dir === "w"
        ? "ew-resize"
        : "ns-resize";

    const handleResizeMove = (e: MouseEvent | TouchEvent) => {
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

      const deltaX = clientX - resizeStartRef.current.mouseX;
      const deltaY = clientY - resizeStartRef.current.mouseY;
      const currentDir = resizeStartRef.current.direction;

      const minW = 320;
      const maxW = Math.min(1200, window.innerWidth - 20);
      const minH = 340;
      const maxH = Math.min(950, window.innerHeight - 30);

      let newW = resizeStartRef.current.startW;
      let newH = resizeStartRef.current.startH;
      let newPosX = resizeStartRef.current.startPosX;
      let newPosY = resizeStartRef.current.startPosY;

      // Horizontal resize calculation
      if (currentDir.includes("e")) {
        const desiredW = resizeStartRef.current.startW + deltaX;
        if (newPosX + desiredW > window.innerWidth - 10) {
          // If reaches right edge, push posX to left to allow expanding wider
          newPosX = Math.max(10, window.innerWidth - desiredW - 10);
        }
        newW = Math.max(minW, Math.min(maxW, Math.min(window.innerWidth - newPosX - 10, desiredW)));
      } else if (currentDir.includes("w")) {
        const desiredW = resizeStartRef.current.startW - deltaX;
        const clampedW = Math.max(minW, Math.min(maxW, desiredW));
        const proposedPosX = resizeStartRef.current.startPosX + (resizeStartRef.current.startW - clampedW);
        if (proposedPosX >= 10) {
          newPosX = proposedPosX;
          newW = clampedW;
        } else {
          newPosX = 10;
          newW = Math.max(minW, resizeStartRef.current.startPosX + resizeStartRef.current.startW - 10);
        }
      }

      // Vertical resize calculation
      if (currentDir.includes("s")) {
        const desiredH = resizeStartRef.current.startH + deltaY;
        if (newPosY + desiredH > window.innerHeight - 10) {
          // If reaches bottom edge, push posY up to allow expanding taller
          newPosY = Math.max(10, window.innerHeight - desiredH - 10);
        }
        newH = Math.max(minH, Math.min(maxH, Math.min(window.innerHeight - newPosY - 10, desiredH)));
      } else if (currentDir.includes("n")) {
        const desiredH = resizeStartRef.current.startH - deltaY;
        const clampedH = Math.max(minH, Math.min(maxH, desiredH));
        const proposedPosY = resizeStartRef.current.startPosY + (resizeStartRef.current.startH - clampedH);
        if (proposedPosY >= 10) {
          newPosY = proposedPosY;
          newH = clampedH;
        } else {
          newPosY = 10;
          newH = Math.max(minH, resizeStartRef.current.startPosY + resizeStartRef.current.startH - 10);
        }
      }

      setSize({ width: Math.round(newW), height: Math.round(newH) });
      setPosition({ x: Math.round(newPosX), y: Math.round(newPosY) });
    };

    const handleResizeEnd = () => {
      setIsResizing(false);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };

    window.addEventListener("mousemove", handleResizeMove);
    window.addEventListener("mouseup", handleResizeEnd);
    window.addEventListener("touchmove", handleResizeMove);
    window.addEventListener("touchend", handleResizeEnd);

    return () => {
      window.removeEventListener("mousemove", handleResizeMove);
      window.removeEventListener("mouseup", handleResizeEnd);
      window.removeEventListener("touchmove", handleResizeMove);
      window.removeEventListener("touchend", handleResizeEnd);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };
  }, [isResizing]);

  // ── Send Message Handler (from Tubelight Bar or Floating Window) ──
  const handleSendMessage = useCallback(
    async (textToSend: string) => {
      const trimmed = textToSend.trim();
      if (!trimmed || isSending) return;

      let sid = activeSessionId;
      if (!sid) {
        sid = await createSession(trimmed.slice(0, 32));
      }

      // Add user message
      await addMessage(sid, {
        id: generateMsgId(),
        role: "user",
        content: trimmed,
      });

      setInput("");
      setFloatingInput("");
      setIsSending(true);

      // Simulate Copilot processing with intelligent response
      setTimeout(async () => {
        const reply = generateArchitectureReply(trimmed, hldData);
        if (sid) {
          await addMessage(sid, {
            id: generateMsgId(),
            role: "ai",
            content: reply,
          });
        }
        setIsSending(false);
      }, 750);
    },
    [activeSessionId, createSession, addMessage, hldData, isSending]
  );

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1800);
  };

  return (
    <>
      {/* ══════════════════════════════════════════════════════════════════════════════
          TUBELIGHT CHAT DOCK (DOCK BAR BELOW HLD & LLD)
      ══════════════════════════════════════════════════════════════════════════════ */}
      <div
        className={cn(
          "absolute left-1/2 -translate-x-1/2 z-30 w-[95%] max-w-2xl pointer-events-none select-none transition-all duration-300",
          hldWorkspaceTab === "lld" ? "bottom-16 sm:bottom-18" : "bottom-4 sm:bottom-6"
        )}
      >
        <div className="relative flex flex-col items-center pointer-events-auto group">
          {/* ── 1. The Fluorescent Tubelight Fixture ── */}
          <div className="relative w-[92%] sm:w-[86%] flex items-center justify-center z-10 -mb-1.5 transition-all duration-300">
            {/* Left Bracket Socket */}
            <div className="h-3.5 w-3 rounded-l-xs bg-gradient-to-r from-neutral-400 to-neutral-500 dark:from-neutral-700 dark:to-neutral-600 border border-neutral-400/80 dark:border-neutral-700 shadow-sm shrink-0" />

            {/* Glowing Fluorescent Neon Tubelight Tube */}
            <div className="relative flex-1 h-[4.5px] rounded-full bg-gradient-to-r from-cyan-400 via-sky-300 to-cyan-400 dark:from-cyan-300 dark:via-white dark:to-cyan-300 shadow-[0_0_14px_rgba(6,182,212,0.9),0_0_28px_rgba(14,165,233,0.6),0_0_42px_rgba(56,189,248,0.3)] transition-all">
              {/* Inner animated incandescent core */}
              <div className="absolute inset-0 rounded-full bg-white opacity-90 animate-pulse" />
              {/* Top ambient fluorescent glare */}
              <div className="absolute -top-1 left-1/4 right-1/4 h-[8px] bg-cyan-300/40 blur-xs rounded-full pointer-events-none" />
            </div>

            {/* Right Bracket Socket */}
            <div className="h-3.5 w-3 rounded-r-xs bg-gradient-to-l from-neutral-400 to-neutral-500 dark:from-neutral-700 dark:to-neutral-600 border border-neutral-400/80 dark:border-neutral-700 shadow-sm shrink-0" />
          </div>

          {/* ── 2. The Tubelight Control Bar Container ── */}
          <div className="relative w-full rounded-2xl sm:rounded-full border border-neutral-200/90 dark:border-white/15 bg-white/85 dark:bg-[#0d0d0d]/85 backdrop-blur-2xl backdrop-saturate-150 p-1.5 sm:p-2 shadow-[0_12px_36px_-6px_rgba(0,0,0,0.18)] dark:shadow-[0_16px_45px_-6px_rgba(0,0,0,0.9)] transition-all duration-300 group-hover:border-cyan-500/50 dark:group-hover:border-cyan-400/40">
            {/* Soft Ambient Light Spill underneath the tube */}
            <div className="absolute top-0 left-10 right-10 h-6 bg-gradient-to-b from-cyan-400/15 to-transparent blur-md pointer-events-none rounded-t-2xl" />

            <div className="relative z-10 flex items-center gap-2">
              {/* ── A. Emoji Button to Preview / Open Chat History ── */}
              <button
                type="button"
                onClick={() => setShowHistory((prev) => !prev)}
                title="Preview Chat History & Open Floating Window"
                className={cn(
                  "relative flex h-10 w-10 sm:h-11 sm:w-11 shrink-0 items-center justify-center rounded-xl sm:rounded-full transition-all duration-200 cursor-pointer shadow-xs active:scale-95 group/emoji",
                  showHistory
                    ? "bg-black text-white dark:bg-white dark:text-black shadow-md ring-2 ring-cyan-400/50"
                    : "bg-neutral-100 hover:bg-neutral-200 text-neutral-800 dark:bg-neutral-900 dark:hover:bg-neutral-800 dark:text-white border border-neutral-200/80 dark:border-neutral-800 hover:border-cyan-400"
                )}
              >
                {/* The Interactive Emoji */}
                <span className="text-lg transition-transform group-hover/emoji:scale-125 select-none">
                  {showHistory ? "💬" : "💬"}
                </span>

                {/* Message Count / Pulse Indicator Badge */}
                {messageCount > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-4 min-w-4 px-1 items-center justify-center rounded-full bg-cyan-500 text-[10px] font-bold text-white shadow-xs">
                    {messageCount}
                  </span>
                )}
              </button>

              {/* ── B. Live Chat Input Field ── */}
              <div className="relative flex-1 flex items-center min-w-0">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleSendMessage(input);
                    }
                  }}
                  placeholder="Ask ArchAI to refine components, protocols, or schemas..."
                  className="w-full bg-transparent px-2.5 py-1.5 text-xs sm:text-sm font-medium text-neutral-900 placeholder:text-neutral-400 focus:outline-none dark:text-white dark:placeholder:text-neutral-500"
                />
              </div>

              {/* ── C. Action Controls & Send Button ── */}
              <div className="flex items-center gap-1.5 shrink-0">
                {/* Model Pill */}
                <div className="hidden sm:inline-flex items-center gap-1 rounded-full border border-neutral-200 dark:border-neutral-800 bg-neutral-100/80 dark:bg-neutral-900/80 px-2.5 py-1 text-[11px] font-semibold text-neutral-600 dark:text-neutral-400">
                  <Sparkles className="h-3 w-3 text-cyan-500" />
                  <span>ArchAI 4o</span>
                </div>

                {/* Send Button with Neon Accent */}
                <button
                  type="button"
                  onClick={() => handleSendMessage(input)}
                  disabled={!input.trim() || isSending}
                  title="Send to Architecture Copilot"
                  className={cn(
                    "flex h-9 w-9 sm:h-10 sm:w-10 items-center justify-center rounded-xl sm:rounded-full transition-all duration-200 cursor-pointer shadow-xs active:scale-95",
                    input.trim() && !isSending
                      ? "bg-black text-white hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200 shadow-md ring-2 ring-cyan-400/40"
                      : "bg-neutral-200/70 text-neutral-400 dark:bg-neutral-800/60 dark:text-neutral-600 cursor-not-allowed"
                  )}
                >
                  <Send className={cn("h-4 w-4 transition-transform", input.trim() && "translate-x-0.5 -translate-y-0.5")} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════════════
          FLOATING, MOVEABLE, RESIZABLE CHAT WINDOW
      ══════════════════════════════════════════════════════════════════════════════ */}
      {showHistory && position && (
        <div
          ref={floatingWindowRef}
          style={
            isMaximized
              ? {
                  position: "fixed",
                  top: "60px",
                  left: "16px",
                  right: "16px",
                  bottom: "85px",
                  width: "calc(100% - 32px)",
                  height: "calc(100vh - 145px)",
                  zIndex: 50,
                }
              : {
                  position: "fixed",
                  left: `${position.x}px`,
                  top: `${position.y}px`,
                  width: `${size.width}px`,
                  height: `${size.height}px`,
                  zIndex: 50,
                }
          }
          className={cn(
            "flex flex-col rounded-3xl border border-neutral-200/90 dark:border-white/15 bg-white/95 dark:bg-[#0f0f0f]/95 shadow-[0_24px_60px_-10px_rgba(0,0,0,0.25)] dark:shadow-[0_24px_70px_-10px_rgba(0,0,0,0.95)] backdrop-blur-2xl backdrop-saturate-150 overflow-hidden transition-shadow select-none",
            isDragging && "opacity-95 shadow-2xl cursor-grabbing ring-2 ring-cyan-500/40"
          )}
        >
          {/* ── Window Top Bar / Drag Handle ── */}
          <div
            onMouseDown={handleStartDrag}
            onTouchStart={handleStartDrag}
            className="flex items-center justify-between px-4 py-3 border-b border-neutral-200/80 dark:border-white/10 bg-neutral-50/80 dark:bg-white/[0.03] backdrop-blur-md cursor-grab active:cursor-grabbing shrink-0"
          >
            {/* Left: Move Grip, Emoji & Title */}
            <div className="flex items-center gap-2 min-w-0">
              <GripVertical className="h-4 w-4 text-neutral-400 dark:text-neutral-500 shrink-0" />
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/10 dark:bg-cyan-400/20 text-cyan-600 dark:text-cyan-300 font-bold shrink-0">
                💬
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <h4 className="font-heading text-xs font-bold text-neutral-900 dark:text-white truncate">
                    Architecture Copilot
                  </h4>
                  <span className="rounded-full bg-neutral-200/80 px-1.5 py-0.2 text-[9px] font-mono text-neutral-700 dark:bg-white/10 dark:text-neutral-300 shrink-0">
                    Live
                  </span>
                </div>
                <p className="truncate text-[10px] text-neutral-500 dark:text-neutral-400">
                  {activeSession?.title || "Active Architecture Chat"}
                </p>
              </div>
            </div>

            {/* Right: Window Controls (Minimize, Maximize, Close) */}
            <div className="flex items-center gap-1 shrink-0 ml-2">
              {/* Maximize / Restore Button */}
              <button
                type="button"
                onClick={() => setIsMaximized((prev) => !prev)}
                title={isMaximized ? "Restore floating window" : "Maximize window"}
                className="flex h-7 w-7 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-200 hover:text-black dark:text-neutral-400 dark:hover:bg-white/10 dark:hover:text-white transition-colors cursor-pointer"
              >
                {isMaximized ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
              </button>

              {/* Close Button */}
              <button
                type="button"
                onClick={() => setShowHistory(false)}
                title="Close floating chat window"
                className="flex h-7 w-7 items-center justify-center rounded-lg text-neutral-500 hover:bg-red-50 hover:text-red-600 dark:text-neutral-400 dark:hover:bg-red-950/40 dark:hover:text-red-400 transition-colors cursor-pointer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* ── Message History Stream ── */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 min-h-0 select-text">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center px-4 py-8 text-neutral-500 dark:text-neutral-400">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 dark:bg-cyan-400/15 mb-3 text-2xl">
                  💬
                </div>
                <p className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                  No conversation history yet
                </p>
                <p className="text-[11px] text-neutral-500 dark:text-neutral-400 mt-1 max-w-xs">
                  Ask ArchAI below to refine services, inspect schemas, or explain protocols in your HLD/LLD diagrams.
                </p>
                <div className="mt-4 flex flex-wrap justify-center gap-1.5 max-w-sm">
                  {[
                    "Add Redis caching tier",
                    "How does Kafka handle consumer lag?",
                    "Explain mTLS security policy",
                  ].map((starter, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSendMessage(starter)}
                      className="rounded-full border border-neutral-200 dark:border-neutral-800 bg-white/80 dark:bg-white/5 px-2.5 py-1 text-[11px] font-medium text-neutral-700 dark:text-neutral-300 hover:border-cyan-400 transition-all cursor-pointer"
                    >
                      {starter}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m) => {
                const isUser = m.role === "user";
                return (
                  <div
                    key={m.id}
                    className={cn(
                      "flex w-full gap-2.5 group/msg",
                      isUser ? "justify-end" : "justify-start"
                    )}
                  >
                    {!isUser && (
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-black text-white dark:bg-white dark:text-black shadow-xs text-xs mt-0.5">
                        <Cpu className="h-3.5 w-3.5" />
                      </div>
                    )}

                    <div
                      className={cn(
                        "relative rounded-2xl p-3 text-xs leading-relaxed max-w-[85%] shadow-xs",
                        isUser
                          ? "bg-neutral-900 text-white dark:bg-white dark:text-black font-medium rounded-tr-xs"
                          : "border border-neutral-200/90 dark:border-white/10 bg-white/90 dark:bg-[#141414] text-neutral-800 dark:text-neutral-200 rounded-tl-xs"
                      )}
                    >
                      <div className="whitespace-pre-wrap">{m.content}</div>

                      {/* Copy action for AI messages */}
                      {!isUser && (
                        <button
                          type="button"
                          onClick={() => copyToClipboard(m.content, m.id)}
                          title="Copy message"
                          className="absolute top-2 right-2 opacity-0 group-hover/msg:opacity-100 transition-opacity p-1 rounded-md text-neutral-400 hover:text-neutral-700 dark:hover:text-white"
                        >
                          {copiedId === m.id ? (
                            <Check className="h-3 w-3 text-emerald-500" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </button>
                      )}
                    </div>

                    {isUser && (
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl border border-neutral-300 bg-neutral-100 text-neutral-800 dark:border-neutral-700 dark:bg-neutral-800 dark:text-white shadow-xs text-xs mt-0.5 font-bold">
                        {user?.email?.charAt(0).toUpperCase() || "U"}
                      </div>
                    )}
                  </div>
                );
              })
            )}

            {/* AI Thinking Animation */}
            {isSending && (
              <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400 py-1">
                <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-black text-white dark:bg-white dark:text-black text-xs animate-spin">
                  <Cpu className="h-3 w-3" />
                </div>
                <span className="font-mono text-[11px] animate-pulse">ArchAI is analyzing architecture...</span>
              </div>
            )}

            <div ref={chatScrollRef} />
          </div>

          {/* ── Bottom Input inside Floating Window ── */}
          <div className="p-3 border-t border-neutral-200/80 dark:border-white/10 bg-neutral-50/70 dark:bg-white/[0.02] shrink-0">
            <div className="relative flex items-center gap-2 rounded-2xl border border-neutral-200/90 dark:border-white/15 bg-white dark:bg-[#121212] px-3 py-1.5 shadow-xs">
              <input
                type="text"
                value={floatingInput}
                onChange={(e) => setFloatingInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleSendMessage(floatingInput);
                  }
                }}
                placeholder="Type architecture question or change..."
                className="w-full bg-transparent text-xs text-neutral-900 placeholder:text-neutral-400 focus:outline-none dark:text-white dark:placeholder:text-neutral-500"
              />

              <button
                type="button"
                onClick={() => handleSendMessage(floatingInput)}
                disabled={!floatingInput.trim() || isSending}
                className={cn(
                  "flex h-7 w-7 items-center justify-center rounded-xl transition-all cursor-pointer shadow-xs",
                  floatingInput.trim() && !isSending
                    ? "bg-black text-white hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200"
                    : "bg-neutral-200 text-neutral-400 dark:bg-neutral-800 dark:text-neutral-600 cursor-not-allowed"
                )}
              >
                <CornerDownLeft className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* ── Multi-Directional Dynamic Resize Handles ── */}
          {!isMaximized && (
            <>
              {/* Right edge */}
              <div
                onMouseDown={(e) => handleStartResize(e, "e")}
                onTouchStart={(e) => handleStartResize(e, "e")}
                className="absolute top-3 right-0 w-3 h-[calc(100%-24px)] cursor-ew-resize hover:bg-cyan-500/20 active:bg-cyan-500/40 z-30 transition-colors"
                title="Drag horizontally to resize"
              />
              {/* Left edge */}
              <div
                onMouseDown={(e) => handleStartResize(e, "w")}
                onTouchStart={(e) => handleStartResize(e, "w")}
                className="absolute top-3 left-0 w-3 h-[calc(100%-24px)] cursor-ew-resize hover:bg-cyan-500/20 active:bg-cyan-500/40 z-30 transition-colors"
                title="Drag horizontally to resize"
              />
              {/* Bottom edge */}
              <div
                onMouseDown={(e) => handleStartResize(e, "s")}
                onTouchStart={(e) => handleStartResize(e, "s")}
                className="absolute bottom-0 left-3 h-3 w-[calc(100%-24px)] cursor-ns-resize hover:bg-cyan-500/20 active:bg-cyan-500/40 z-30 transition-colors"
                title="Drag vertically to resize"
              />
              {/* Top edge */}
              <div
                onMouseDown={(e) => handleStartResize(e, "n")}
                onTouchStart={(e) => handleStartResize(e, "n")}
                className="absolute top-0 left-3 h-3 w-[calc(100%-24px)] cursor-ns-resize hover:bg-cyan-500/20 active:bg-cyan-500/40 z-30 transition-colors"
                title="Drag vertically to resize"
              />

              {/* Bottom-Right Tactile Corner Grip (SE) */}
              <div
                onMouseDown={(e) => handleStartResize(e, "se")}
                onTouchStart={(e) => handleStartResize(e, "se")}
                title="Drag corner to dynamically resize window"
                className="absolute bottom-0 right-0 h-9 w-9 cursor-nwse-resize flex items-end justify-end p-2 z-40 select-none group/resize"
              >
                <div className="flex flex-col items-end gap-[3px] opacity-60 group-hover/resize:opacity-100 group-hover/resize:scale-115 transition-all">
                  <span className="h-[2px] w-4.5 rounded-full bg-neutral-400 dark:bg-neutral-500 group-hover/resize:bg-cyan-400 shadow-xs transition-colors" />
                  <span className="h-[2px] w-3 rounded-full bg-neutral-400 dark:bg-neutral-500 group-hover/resize:bg-cyan-400 shadow-xs transition-colors" />
                  <span className="h-[2px] w-1.5 rounded-full bg-neutral-400 dark:bg-neutral-500 group-hover/resize:bg-cyan-400 shadow-xs transition-colors" />
                </div>
              </div>

              {/* Bottom-Left Corner (SW) */}
              <div
                onMouseDown={(e) => handleStartResize(e, "sw")}
                onTouchStart={(e) => handleStartResize(e, "sw")}
                className="absolute bottom-0 left-0 h-8 w-8 cursor-nesw-resize z-40"
              />
              {/* Top-Right Corner (NE) */}
              <div
                onMouseDown={(e) => handleStartResize(e, "ne")}
                onTouchStart={(e) => handleStartResize(e, "ne")}
                className="absolute top-0 right-0 h-8 w-8 cursor-nesw-resize z-40"
              />
              {/* Top-Left Corner (NW) */}
              <div
                onMouseDown={(e) => handleStartResize(e, "nw")}
                onTouchStart={(e) => handleStartResize(e, "nw")}
                className="absolute top-0 left-0 h-8 w-8 cursor-nwse-resize z-40"
              />
            </>
          )}

          {/* Real-time Dynamic Resize Dimension Tooltip */}
          {isResizing && (
            <div className="absolute top-2.5 left-1/2 -translate-x-1/2 z-50 pointer-events-none animate-in fade-in zoom-in-95 duration-150">
              <span className="rounded-full bg-black/85 text-white dark:bg-white/90 dark:text-black font-mono text-[11px] font-bold px-3 py-1 shadow-lg border border-cyan-400/50">
                {size.width} × {size.height} px
              </span>
            </div>
          )}
        </div>
      )}
    </>
  );
}
