"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu } from "lucide-react";
import ThemeToggle from "./ThemeToggle";

export default function Navbar() {
  const pathname = usePathname();
  const isChat = pathname === "/chat";
  const isSignIn = pathname === "/signin";
  const isSignUp = pathname === "/signup";

  return (
    <nav className="fixed top-0 z-50 flex h-14 w-full items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur-md dark:border-gray-800 dark:bg-gray-950/80 md:px-6">
      <Link href="/" className="flex items-center gap-2 font-bold text-lg">
        <Cpu className="h-6 w-6 text-[#2563EB]" />
        <span className="text-[#0F172A] dark:text-white">
          ArchAI
        </span>
      </Link>

      <div className="flex items-center gap-3">
        <ThemeToggle />
        {isChat && (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#2563EB] text-xs font-bold text-white">
            U
          </div>
        )}
        {!isChat && (
          <div className="hidden items-center gap-2 sm:flex">
            <Link
              href="/signin"
              className={`rounded-lg border px-4 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ${
                isSignIn
                  ? "border-[#1E3A8A] bg-[#1E3A8A] text-white shadow-md shadow-[#1E3A8A]/35 hover:bg-[#1E40AF] focus-visible:ring-[#1E3A8A]"
                  : "border-slate-400 bg-white text-[#0F172A] shadow-sm hover:bg-slate-50 focus-visible:ring-slate-400 dark:border-gray-500 dark:bg-transparent dark:text-gray-100 dark:hover:bg-gray-800"
              }`}
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className={`rounded-lg border px-4 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ${
                isSignUp
                  ? "border-[#1E3A8A] bg-[#1E3A8A] text-white shadow-md shadow-[#1E3A8A]/35 hover:bg-[#1E40AF] focus-visible:ring-[#1E3A8A]"
                  : "border-slate-400 bg-white text-[#0F172A] shadow-sm hover:bg-slate-50 focus-visible:ring-slate-400 dark:border-gray-500 dark:bg-transparent dark:text-gray-100 dark:hover:bg-gray-800"
              }`}
            >
              Sign Up
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
