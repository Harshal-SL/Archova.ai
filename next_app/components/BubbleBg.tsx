"use client";

import { useEffect, useState } from "react";
import ShootingStarsGrid from "@/components/ui/shooting-stars-grid";

interface BubbleBgProps {
  opacity?: string;
  speed?: "slow" | "normal" | "fast" | number;
  starCount?: number;
  shootingStarCount?: number;
}

export default function BubbleBg({
  opacity = "opacity-100",
  speed = "normal",
  starCount = 48,
  shootingStarCount = 6,
}: BubbleBgProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div
      className={`pointer-events-none fixed inset-0 z-0 overflow-hidden transition-opacity duration-300 ${opacity}`}
      aria-hidden="true"
    >
      <ShootingStarsGrid
        starCount={starCount}
        shootingStarCount={shootingStarCount}
        gridSize={44}
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
