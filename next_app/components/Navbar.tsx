"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();
  const isChat = pathname === "/chat";

  // Hide Navbar completely on chat page since it has its own layout
  if (isChat) return null;

  return (
    <nav className="fixed top-0 z-50 flex h-16 w-full items-center justify-between border-b border-[#2A2A2A] bg-[#000000]/90 px-6 backdrop-blur-md">
      <Link href="/" className="font-mono text-xl font-bold tracking-tight text-white transition-opacity hover:opacity-80">
        ArchitectAI
      </Link>

      <div className="flex items-center gap-4">
        <Link
          href="/signin"
          className="text-sm font-medium text-[#AAAAAA] transition-colors hover:text-white"
        >
          Login
        </Link>
        <Link
          href="/chat"
          className="rounded-full bg-white px-5 py-2 text-sm font-semibold text-black transition-all hover:bg-[#E5E5E5] active:scale-95"
        >
          Get Started
        </Link>
      </div>
    </nav>
  );
}
