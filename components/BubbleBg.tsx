"use client";

import { useEffect, useState } from "react";

export default function BubbleBg() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden="true">
      {/* 1. Subtle Monochrome Tech Grid with radial edge falloff */}
      <div className="absolute inset-0 bg-grid-pattern mask-radial-faded opacity-60 dark:opacity-75" />

      {/* 2. Top-Center Ambient White/Black Spotlight */}
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-[450px] w-[750px] rounded-full bg-gradient-to-b from-neutral-200/40 to-transparent blur-3xl dark:from-white/10 dark:to-transparent" />

      {/* 3. Fine horizontal accent divider line */}
      <div className="absolute top-14 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-neutral-300 to-transparent dark:via-neutral-800" />
    </div>
  );
}
