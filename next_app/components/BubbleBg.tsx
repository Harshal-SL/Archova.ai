"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

// Lazy-load the heavy canvas/animation component only on the client
const ShootingStarsGrid = dynamic(
  () => import("@/components/ui/shooting-stars-grid"),
  {
    ssr: false,
    loading: () => null,
  }
);

interface BubbleBgProps {
  opacity?: string;
  speed?: "slow" | "normal" | "fast" | number;
  starCount?: number;
  shootingStarCount?: number;
}

export default function BubbleBg({
  opacity = "opacity-100",
  speed = "normal",
  starCount = 28,
  shootingStarCount = 4,
}: BubbleBgProps) {
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    // Lazy load background animation when the main browser thread is idle
    if (typeof window === "undefined") return;

    if ("requestIdleCallback" in window) {
      const handle = (
        window as unknown as {
          requestIdleCallback: (cb: () => void, opts?: { timeout: number }) => number;
        }
      ).requestIdleCallback(() => setShouldRender(true), { timeout: 400 });

      return () => {
        (
          window as unknown as { cancelIdleCallback: (id: number) => void }
        ).cancelIdleCallback(handle);
      };
    } else {
      const timer = setTimeout(() => setShouldRender(true), 150);
      return () => clearTimeout(timer);
    }
  }, []);

  if (!shouldRender) {
    // Ultra-lightweight static placeholder while lazy loading
    return (
      <div
        className={`pointer-events-none fixed inset-0 z-0 overflow-hidden ${opacity}`}
        style={{ contain: "strict" }}
        aria-hidden="true"
      />
    );
  }

  return (
    <div
      className={`pointer-events-none fixed inset-0 z-0 overflow-hidden transition-opacity duration-700 ${opacity}`}
      style={{
        contain: "strict",
        willChange: "transform",
        transform: "translateZ(0)",
      }}
      aria-hidden="true"
    >
      <ShootingStarsGrid
        starCount={starCount}
        shootingStarCount={shootingStarCount}
        gridSize={48}
        speed={speed}
        glow={true}
        interactive={false}
        className="h-full w-full rounded-none border-none shadow-none min-h-0 bg-transparent dark:bg-transparent"
      >
        {null}
      </ShootingStarsGrid>
    </div>
  );
}
