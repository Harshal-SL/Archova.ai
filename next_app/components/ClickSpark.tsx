"use client";

import {
  useEffect,
  useMemo,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react";

type ClickSparkProps = {
  sparkColor?: string;
  sparkSize?: number;
  sparkRadius?: number;
  sparkCount?: number;
  duration?: number;
  easing?: string;
  extraScale?: number;
  className?: string;
  children?: ReactNode;
};

type SparkParticle = {
  id: string;
  className: string;
  tx: number;
  ty: number;
  size: number;
};

type SparkBurst = {
  id: string;
  x: number;
  y: number;
  createdAt: number;
  particles: SparkParticle[];
};

const randomBetween = (min: number, max: number) => Math.random() * (max - min) + min;
const createId = () => `${Date.now()}${Math.random().toString(36).slice(2, 9)}`;

export default function ClickSpark({
  sparkColor = "#ffffff",
  sparkSize = 10,
  sparkRadius = 15,
  sparkCount = 8,
  duration = 400,
  easing = "ease-out",
  extraScale = 1,
  className,
  children,
}: ClickSparkProps) {
  const [bursts, setBursts] = useState<SparkBurst[]>([]);

  useEffect(() => {
    if (bursts.length === 0) return;

    const interval = window.setInterval(() => {
      const now = Date.now();
      setBursts((prev) => prev.filter((b) => now - b.createdAt < duration + 120));
    }, 100);

    return () => window.clearInterval(interval);
  }, [bursts.length, duration]);

  const handleClickCapture = (event: MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const burstId = createId();

    const particles: SparkParticle[] = Array.from({ length: sparkCount }).map((_, i) => {
      const baseAngle = (Math.PI * 2 * i) / sparkCount;
      const jitter = randomBetween(-0.22, 0.22);
      const angle = baseAngle + jitter;
      const distance = sparkRadius * randomBetween(0.8, 1.35);
      const tx = Math.cos(angle) * distance;
      const ty = Math.sin(angle) * distance;

      return {
        id: createId(),
        className: `click-spark-${burstId}-${i}`,
        tx,
        ty,
        size: sparkSize * randomBetween(0.65, 1.15),
      };
    });

    setBursts((prev) => [
      ...prev,
      {
        id: burstId,
        x,
        y,
        createdAt: Date.now(),
        particles,
      },
    ]);
  };

  const rootClassName = useMemo(() => {
    return ["relative", className].filter(Boolean).join(" ");
  }, [className]);

  const particleRules = useMemo(() => {
    return bursts
      .flatMap((burst) =>
        burst.particles.map((particle) => {
          return `.${particle.className}{left:${burst.x}px;top:${burst.y}px;width:${particle.size}px;height:${particle.size}px;background-color:${sparkColor};color:${sparkColor};--spark-tx:${particle.tx}px;--spark-ty:${particle.ty}px;--spark-duration:${duration}ms;--spark-easing:${easing};--spark-scale:${extraScale};}`;
        })
      )
      .join("\n");
  }, [bursts, duration, easing, extraScale, sparkColor]);

  return (
    <div className={rootClassName} onClickCapture={handleClickCapture}>
      {children}

      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden" aria-hidden="true">
        {bursts.map((burst) =>
          burst.particles.map((particle) => (
            <span
              key={`${burst.id}-${particle.id}`}
              className={`click-spark-particle ${particle.className}`}
            />
          ))
        )}
      </div>

      <style jsx global>{`
        ${particleRules}

        .click-spark-particle {
          position: absolute;
          border-radius: 9999px;
          opacity: 0.95;
          transform: translate(-50%, -50%);
          animation: click-spark-burst var(--spark-duration) var(--spark-easing) forwards;
          box-shadow: 0 0 14px currentColor;
        }

        @keyframes click-spark-burst {
          0% {
            transform: translate(-50%, -50%) scale(0.25);
            opacity: 1;
          }
          100% {
            transform: translate(calc(-50% + var(--spark-tx)), calc(-50% + var(--spark-ty)))
              scale(var(--spark-scale));
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
}