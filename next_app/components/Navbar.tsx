"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Cpu,
  LogOut,
  ArrowRight,
  Menu,
  X,
  Sparkles,
} from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import EngineStatusButton from "./EngineStatusButton";
import { ShimmerButton } from "@/components/ui/shimmer-button";
import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export default function Navbar() {
  const router = useRouter();
  const { user, initAuth, signOut } = useAppStore();

  const [isScrolled, setIsScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState<string>("home");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  useEffect(() => {
    const sectionIds = ["home", "about", "services"];

    const handleScroll = () => {
      const scrollY = window.scrollY;
      setIsScrolled(scrollY > 20);

      // At top of page, home is active
      if (scrollY < 120) {
        setActiveSection("home");
        return;
      }

      // If scrolled to the bottom of the page, activate the last section
      if (window.innerHeight + scrollY >= document.documentElement.scrollHeight - 60) {
        setActiveSection("services");
        return;
      }

      // Check section bounding rects
      let current = "home";
      for (const id of sectionIds) {
        const elem = document.getElementById(id);
        if (elem) {
          const top = elem.getBoundingClientRect().top;
          // When top of section is within upper half of viewport
          if (top <= 200) {
            current = id;
          }
        }
      }
      setActiveSection(current);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleSignOut = async () => {
    await signOut();
  };

  const displayName =
    user?.user_metadata?.name ||
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "Architect";

  const userInitial = displayName.charAt(0).toUpperCase();

  const navLinks = [
    { label: "Home", href: "#home", id: "home" },
    { label: "About", href: "#about", id: "about" },
    { label: "Capabilities", href: "#services", id: "services" },
  ];

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (href.startsWith("#")) {
      e.preventDefault();
      const targetId = href.replace("#", "");
      setActiveSection(targetId);
      const elem = document.getElementById(targetId);
      if (elem) {
        elem.scrollIntoView({ behavior: "smooth" });
      }
      setMobileMenuOpen(false);
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex flex-col items-center pointer-events-none transition-all duration-300">
      {/* ── Floating Translucent Glass Pill Navbar ── */}
      <nav
        className={cn(
          "pointer-events-auto mx-auto mt-3 sm:mt-4 w-[calc(100%-1.75rem)] max-w-6xl",
          "flex items-center justify-between rounded-full px-4 sm:px-6 py-2 sm:py-2.5",
          "backdrop-blur-2xl backdrop-saturate-150 transition-all duration-300 select-none",
          isScrolled
            ? "border border-neutral-200/60 dark:border-white/15 bg-white/40 dark:bg-black/50 shadow-[0_8px_32px_rgba(0,0,0,0.08)] dark:shadow-[0_8px_32px_rgba(0,0,0,0.6)]"
            : "border border-neutral-200/40 dark:border-white/10 bg-white/20 dark:bg-black/25 shadow-[0_4px_24px_rgba(0,0,0,0.03)] dark:shadow-[0_4px_24px_rgba(0,0,0,0.3)]"
        )}
      >
        {/* Left: Brand logo */}
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-2.5 group"
            title="ArchAI - Autonomous Multi-Agent Systems Engineering"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-black text-white dark:bg-white dark:text-black shadow-xs transition-transform duration-200 group-hover:scale-105">
              <Cpu className="h-4 w-4" />
            </div>
            <span className="font-heading font-extrabold text-base sm:text-lg tracking-tight text-neutral-900 dark:text-white">
              Arch<span className="text-neutral-500 dark:text-neutral-400">AI</span>
            </span>
          </Link>
          <span className="hidden sm:inline-flex items-center gap-1 rounded-full border border-neutral-200/60 dark:border-white/10 bg-white/30 dark:bg-white/[0.04] px-2 py-0.5 text-[10px] font-mono text-neutral-600 dark:text-neutral-300 backdrop-blur-md">
            v2.5
          </span>
        </div>

        {/* Center: Nav links in glass sub-pill with Active Section Highlight */}
        <div className="hidden md:flex items-center gap-1 rounded-full border border-neutral-200/40 dark:border-white/[0.08] bg-white/20 dark:bg-white/[0.02] p-1 backdrop-blur-md">
          {navLinks.map((link) => {
            const isActive = activeSection === link.id;
            return (
              <a
                key={link.label}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className={cn(
                  "relative px-4 py-1.5 text-xs font-semibold rounded-full transition-all duration-200 select-none",
                  isActive
                    ? "bg-black text-white dark:bg-white dark:text-black shadow-xs font-bold"
                    : "text-neutral-600 dark:text-neutral-300 hover:text-black dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/10"
                )}
              >
                {link.label}
              </a>
            );
          })}
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-2 sm:gap-2.5">
          {/* Live Engine Status Button */}
          <EngineStatusButton />

          {/* Theme Switcher */}
          <ThemeToggle />

          {/* User Profile / Studio CTA */}
          {user ? (
            <div className="flex items-center gap-1.5 sm:gap-2">
              <Link
                href="/chat"
                className="flex items-center gap-2 rounded-full border border-neutral-200/60 dark:border-white/15 bg-white/40 dark:bg-white/[0.06] px-3 py-1 text-xs font-semibold text-neutral-900 dark:text-white shadow-2xs backdrop-blur-md hover:bg-white/80 dark:hover:bg-white/[0.12] transition-colors"
                title="Go to Architecture Studio"
              >
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-black text-white dark:bg-white dark:text-black text-[10px] font-bold shadow-xs">
                  {userInitial}
                </div>
                <span className="hidden sm:inline max-w-[100px] truncate">{displayName}</span>
              </Link>

              {/* Logout Button: Only the logo in red color */}
              <button
                type="button"
                onClick={handleSignOut}
                title="Logout"
                aria-label="Logout"
                className="flex h-7 w-7 items-center justify-center rounded-full border border-red-500/25 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:border-red-500/30 dark:bg-red-950/40 dark:hover:bg-red-900/50 dark:text-red-400 transition-all duration-150 cursor-pointer shadow-2xs group"
              >
                <LogOut className="h-3.5 w-3.5 text-red-600 dark:text-red-400 transition-transform duration-150 group-hover:scale-110" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/signin"
                className="hidden sm:inline-block px-3 py-1 text-xs font-semibold text-neutral-700 dark:text-neutral-300 hover:text-black dark:hover:text-white transition-colors"
              >
                Sign In
              </Link>
              <Link href="/chat">
                <ShimmerButton
                  shimmerColor="rgba(255, 255, 255, 0.9)"
                  shimmerDuration="2.5s"
                  borderRadius="9999px"
                  background="rgba(10, 10, 15, 0.9)"
                  className="px-4 py-1.5 text-xs font-bold shadow-sm hover:shadow-md border border-white/20"
                >
                  <div className="flex items-center gap-1.5 text-white">
                    <span>Studio</span>
                    <ArrowRight className="h-3 w-3" />
                  </div>
                </ShimmerButton>
              </Link>
            </div>
          )}

          {/* Mobile hamburger toggle */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden rounded-full p-1.5 text-neutral-700 dark:text-neutral-300 hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
            title="Toggle Menu"
          >
            {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </nav>

      {/* ── Mobile Glass Menu Dropdown ── */}
      {mobileMenuOpen && (
        <div className="pointer-events-auto mx-auto mt-2 w-[calc(100%-1.75rem)] max-w-6xl rounded-3xl border border-neutral-200/50 dark:border-white/15 bg-white/80 dark:bg-black/85 backdrop-blur-2xl p-4 shadow-2xl md:hidden animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex flex-col gap-2">
            {navLinks.map((link) => {
              const isActive = activeSection === link.id;
              return (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={(e) => handleNavClick(e, link.href)}
                  className={cn(
                    "flex items-center justify-between px-4 py-2.5 text-sm font-semibold rounded-2xl transition-colors",
                    isActive
                      ? "bg-black text-white dark:bg-white dark:text-black font-bold shadow-xs"
                      : "text-neutral-800 dark:text-neutral-200 hover:bg-black/5 dark:hover:bg-white/10"
                  )}
                >
                  <span>{link.label}</span>
                  {isActive && <span className="h-1.5 w-1.5 rounded-full bg-white dark:bg-black" />}
                </a>
              );
            })}

            {user ? (
              <div className="pt-2 border-t border-neutral-200/40 dark:border-white/10 flex flex-col gap-2">
                <div className="flex items-center gap-2 px-2 py-1 text-xs text-neutral-600 dark:text-neutral-400">
                  <div className="flex h-5 w-5 items-center justify-center rounded-full bg-black text-white dark:bg-white dark:text-black text-[10px] font-bold">
                    {userInitial}
                  </div>
                  <span className="truncate">{displayName}</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    handleSignOut();
                  }}
                  className="flex items-center justify-center gap-2 w-full px-4 py-2.5 text-xs font-bold text-neutral-800 dark:text-neutral-200 bg-white/70 hover:bg-white dark:bg-[#0D0D0F] dark:hover:bg-[#161619] dark:hover:border-white/20 border border-neutral-200/80 dark:border-[#262626] rounded-2xl transition-all cursor-pointer shadow-2xs backdrop-blur-md"
                >
                  <LogOut className="h-4 w-4 text-red-600 dark:text-red-400" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="pt-2 border-t border-neutral-200/40 dark:border-white/10 flex items-center justify-between">
                <Link
                  href="/signin"
                  className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 px-3 py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Sign In
                </Link>
                <Link href="/chat" onClick={() => setMobileMenuOpen(false)}>
                  <ShimmerButton
                    shimmerColor="rgba(255, 255, 255, 0.9)"
                    shimmerDuration="2.5s"
                    borderRadius="9999px"
                    background="rgba(10, 10, 15, 0.9)"
                    className="px-5 py-2 text-xs font-bold text-white shadow-sm"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Studio</span>
                      <ArrowRight className="h-3 w-3" />
                    </div>
                  </ShimmerButton>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
