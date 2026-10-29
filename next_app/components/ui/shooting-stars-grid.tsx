"use client";

import * as React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

type ShootingStarsGridSpeed = "slow" | "normal" | "fast" | number;

export type ShootingStarsGridProps = {
  children?: React.ReactNode;
  starCount?: number;
  shootingStarCount?: number;
  gridSize?: number;
  speed?: ShootingStarsGridSpeed;
  glow?: boolean;
  className?: string;
  contentClassName?: string;
  showGrid?: boolean;
  showStaticStars?: boolean;
  reducedMotionFallback?: boolean;
  interactive?: boolean;
};

type StaticStar = {
  x: number;
  y: number;
  size: number;
  opacity: number;
  delay: number;
  duration: number;
};

type ShootingStar = {
  axis: "horizontal" | "vertical";
  line: number;
  start: string;
  end: string;
  length: number;
  delay: number;
  duration: number;
  repeatDelay: number;
  direction: 1 | -1;
};

const SPEED_SCALE: Record<Exclude<ShootingStarsGridSpeed, number>, number> = {
  slow: 1.25,
  normal: 1,
  fast: 0.72,
};

function seeded(index: number, salt: number) {
  const value = Math.sin(index * 91.73 + salt * 37.11) * 10000;
  return value - Math.floor(value);
}

function createStaticStars(count: number): StaticStar[] {
  return Array.from({ length: count }, (_, index) => {
    const rawX = seeded(index, 1) * 100;
    const rawY = seeded(index, 2) * 100;
    const rawSize = 1 + seeded(index, 3) * 2.4;
    const rawOpacity = 0.32 + seeded(index, 4) * 0.48;
    const rawDelay = seeded(index, 5) * 4;
    const rawDuration = 2.4 + seeded(index, 6) * 3.2;

    return {
      x: Math.round(rawX * 100) / 100,
      y: Math.round(rawY * 100) / 100,
      size: Math.round(rawSize * 10) / 10,
      opacity: Math.round(rawOpacity * 100) / 100,
      delay: Math.round(rawDelay * 10) / 10,
      duration: Math.round(rawDuration * 10) / 10,
    };
  });
}

function createShootingStars(count: number): ShootingStar[] {
  const horizontalLines = [3, 5, 7, 9, 11, 13, 16, 19];
  const verticalLines = [2, 4, 6, 8, 11, 14, 17, 20, 23];

  return Array.from({ length: count }, (_, index) => {
    const axis = index % 3 === 1 ? "vertical" : "horizontal";
    const direction = index % 2 === 0 ? 1 : -1;
    const lanes = axis === "horizontal" ? horizontalLines : verticalLines;

    return {
      axis,
      line: lanes[index % lanes.length],
      start: direction === 1 ? "-18%" : "112%",
      end: direction === 1 ? "112%" : "-18%",
      length: 86 + seeded(index, 15) * 132,
      delay: seeded(index, 16) * 7 + index * 0.65,
      duration: 1.65 + seeded(index, 17) * 1.6,
      repeatDelay: 4.8 + seeded(index, 18) * 6.2,
      direction,
    };
  });
}

function getSpeedScale(speed: ShootingStarsGridSpeed) {
  return typeof speed === "number" ? Math.max(0.35, speed) : SPEED_SCALE[speed];
}

function GridRunner({
  runner,
  index,
  shouldAnimate,
  speedScale,
}: {
  runner: ShootingStar;
  index: number;
  shouldAnimate: boolean;
  speedScale: number;
}) {
  const isHorizontal = runner.axis === "horizontal";
  const linePosition = `calc(var(--shooting-stars-grid-size) * ${runner.line})`;
  const gradientDirection = isHorizontal
    ? runner.direction === 1
      ? "90deg"
      : "270deg"
    : runner.direction === 1
      ? "180deg"
      : "0deg";

  return (
    <motion.span
      className={cn("absolute rounded-full", index > 4 && "max-sm:hidden")}
      style={{
        left: isHorizontal ? runner.start : linePosition,
        top: isHorizontal ? linePosition : runner.start,
        width: isHorizontal ? runner.length : 1.75,
        height: isHorizontal ? 1.75 : runner.length,
        background: `linear-gradient(${gradientDirection}, transparent 0%, var(--shooting-star-head, rgba(0,0,0,0.55)) 15%, var(--shooting-star-body, rgba(0,0,0,0.95)) 48%, var(--shooting-star-core, #000000) 65%, transparent 100%)`,
        boxShadow: "var(--shooting-star-shadow, 0 0 6px rgba(0,0,0,0.7), 0 0 14px rgba(0,0,0,0.35))",
        willChange: "transform, opacity",
        transform: "translateZ(0)",
      }}
      initial={{ opacity: 0, scaleX: isHorizontal ? 0.35 : 1, scaleY: isHorizontal ? 1 : 0.35 }}
      animate={
        shouldAnimate
          ? {
              left: isHorizontal ? [runner.start, runner.end] : linePosition,
              top: isHorizontal ? linePosition : [runner.start, runner.end],
              opacity: [0, 1, 1, 0],
              scaleX: isHorizontal ? [0.35, 1, 1.08, 0.8] : 1,
              scaleY: isHorizontal ? 1 : [0.35, 1, 1.08, 0.8],
            }
          : { opacity: 0 }
      }
      transition={{
        duration: runner.duration * speedScale,
        delay: runner.delay,
        repeat: Infinity,
        repeatDelay: runner.repeatDelay * speedScale,
        ease: "easeOut",
      }}
    />
  );
}

export function ShootingStarsGrid({
  children,
  starCount = 48,
  shootingStarCount = 6,
  gridSize = 44,
  speed = "normal",
  glow = true,
  className,
  contentClassName,
  showGrid = true,
  showStaticStars = true,
  reducedMotionFallback = true,
  interactive = false,
}: ShootingStarsGridProps) {
  const [mounted, setMounted] = React.useState(false);
  const [isVisible, setIsVisible] = React.useState(true);
  const reduceMotion = useReducedMotion() === true;
  const rootRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    setMounted(true);
    const onVisibility = () => {
      setIsVisible(!document.hidden);
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  const staticStars = React.useMemo(
    () => createStaticStars(Math.max(0, Math.min(starCount, 40))),
    [starCount],
  );
  const shootingStars = React.useMemo(
    () => createShootingStars(Math.max(0, Math.min(shootingStarCount, 6))),
    [shootingStarCount],
  );
  const speedScale = getSpeedScale(speed);

  const onPointerMove = React.useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (!interactive || reduceMotion) return;
      const node = rootRef.current;
      if (!node) return;
      const rect = node.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 100;
      const y = ((event.clientY - rect.top) / rect.height) * 100;
      node.style.setProperty("--shooting-stars-glow-x", `${x.toFixed(2)}%`);
      node.style.setProperty("--shooting-stars-glow-y", `${y.toFixed(2)}%`);
    },
    [interactive, reduceMotion],
  );

  const shouldAnimate = mounted && isVisible && (!reduceMotion || !reducedMotionFallback);

  return (
    <section
      ref={rootRef}
      onPointerMove={onPointerMove}
      suppressHydrationWarning
      className={cn(
        "group/shooting-stars relative isolate min-h-[520px] w-full overflow-hidden rounded-[2rem] border border-neutral-200 bg-white text-black shadow-2xl dark:border-white/10 dark:bg-black dark:text-white",
        className,
      )}
      style={
        {
          "--shooting-stars-grid-size": `${gridSize}px`,
          "--shooting-stars-glow-x": "50%",
          "--shooting-stars-glow-y": "30%",
        } as React.CSSProperties
      }
    >
      {showGrid && (
        <div
          aria-hidden="true"
          className={cn(
            "pointer-events-none absolute inset-0 -z-30 opacity-70 dark:opacity-60",
            "[background-image:linear-gradient(to_right,rgba(0,0,0,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(0,0,0,0.04)_1px,transparent_1px)]",
            "[background-size:var(--shooting-stars-grid-size)_var(--shooting-stars-grid-size)]",
            "dark:[background-image:linear-gradient(to_right,rgba(255,255,255,0.075)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.075)_1px,transparent_1px)]",
          )}
        />
      )}

      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-20 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(255,255,255,0.2)_54%,rgba(255,255,255,0.85)_100%)] dark:bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.35)_52%,rgba(0,0,0,0.98)_100%)]"
      />

      {glow && mounted && (
        <motion.div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_var(--shooting-stars-glow-x)_var(--shooting-stars-glow-y),rgba(0,0,0,0.1),transparent_36%),radial-gradient(circle_at_72%_72%,rgba(0,0,0,0.06),transparent_32%)] dark:bg-[radial-gradient(circle_at_var(--shooting-stars-glow-x)_var(--shooting-stars-glow-y),rgba(255,255,255,0.12),transparent_36%),radial-gradient(circle_at_72%_72%,rgba(255,255,255,0.06),transparent_32%)]"
          animate={shouldAnimate ? { opacity: [0.72, 1, 0.78], scale: [1, 1.03, 1] } : undefined}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        />
      )}

      {showStaticStars && mounted && (
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10" suppressHydrationWarning>
          {staticStars.map((star, index) => (
            <span
              key={index}
              className={cn(
                "absolute rounded-full bg-neutral-900 shadow-[0_0_6px_rgba(0,0,0,0.3)] dark:bg-white dark:shadow-[0_0_8px_rgba(255,255,255,0.5)]",
                index > 24 && "max-sm:hidden",
              )}
              style={{
                left: `${star.x}%`,
                top: `${star.y}%`,
                width: star.size,
                height: star.size,
                opacity: star.opacity,
                animation: shouldAnimate
                  ? `star-twinkle ${star.duration}s ease-in-out ${star.delay}s infinite alternate`
                  : "none",
                willChange: "opacity, transform",
                transform: "translateZ(0)",
              }}
            />
          ))}
        </div>
      )}

      {mounted && (
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10" suppressHydrationWarning>
          {shootingStars.map((star, index) => (
            <GridRunner
              key={index}
              runner={star}
              index={index}
              shouldAnimate={shouldAnimate}
              speedScale={speedScale}
            />
          ))}
        </div>
      )}

      {children !== undefined ? (
        children ? (
          <motion.div
            className={cn("relative z-10 flex min-h-[inherit] w-full items-center justify-center px-6 py-16 sm:px-10", contentClassName)}
            initial={reduceMotion ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: "easeOut" }}
          >
            {children}
          </motion.div>
        ) : null
      ) : (
        <motion.div
          className={cn("relative z-10 flex min-h-[inherit] w-full items-center justify-center px-6 py-16 sm:px-10", contentClassName)}
          initial={reduceMotion ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: "easeOut" }}
        >
          <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-neutral-300 bg-neutral-100 px-3 py-1 text-xs font-semibold text-neutral-800 backdrop-blur dark:border-white/20 dark:bg-white/10 dark:text-white">
              <Sparkles className="size-3.5" />
              Archova.ai Architecture Engine
            </div>
            <h2 className="text-balance text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl text-neutral-900 dark:text-white">
              Build systems that feel alive
            </h2>
            <p className="mt-5 max-w-2xl text-balance text-sm leading-6 text-neutral-600 sm:text-base dark:text-neutral-400">
              Deterministic multi-agent architecture synthesis for high-throughput enterprise systems.
            </p>
            <div className="mt-8 flex w-full flex-col justify-center gap-3 sm:w-auto sm:flex-row">
              <Link
                href="/chat"
                className="inline-flex items-center justify-center rounded-full bg-black px-5 py-2.5 text-sm font-semibold text-white shadow-lg dark:bg-white dark:text-black transition-all hover:opacity-90"
              >
                Launch Studio
                <ArrowRight className="ml-2 size-4" />
              </Link>
              <Link
                href="#services"
                className="inline-flex items-center justify-center rounded-full border border-neutral-300 bg-white/70 px-5 py-2.5 text-sm font-semibold text-neutral-900 backdrop-blur dark:border-white/15 dark:bg-white/10 dark:text-white transition-all hover:bg-neutral-100 dark:hover:bg-white/15"
              >
                View Pipeline
              </Link>
            </div>
          </div>
        </motion.div>
      )}
    </section>
  );
}

export default ShootingStarsGrid;
