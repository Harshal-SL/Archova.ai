"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu } from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import { useAppStore } from "@/lib/store";

export default function Navbar() {
  const pathname = usePathname();
  const isChat = pathname === "/chat";

  return (
    <nav className="fixed top-0 z-50 flex h-14 w-full items-center justify-between border-b border-gray-200 bg-white/80 px-4 backdrop-blur-md dark:border-gray-800 dark:bg-gray-950/80 md:px-6">
      <Link href="/" className="flex items-center gap-2 font-bold text-lg">
        <Cpu className="h-6 w-6 text-indigo-500" />
        <span className="bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
          ArchAI
        </span>
      </Link>

      <div className="flex items-center gap-3">
        <ThemeToggle />
        {isChat && (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-xs font-bold text-white">
            U
          </div>
        )}
        {!isChat && (
          <div className="hidden items-center gap-2 sm:flex">
            <Link
              href="/signin"
              className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:opacity-90"
            >
              Sign Up
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
