"use client";

import React, { CSSProperties } from "react";
import { cn } from "@/lib/utils";

export interface ShimmerButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  shimmerColor?: string;
  shimmerSize?: string;
  borderRadius?: string;
  shimmerDuration?: string;
  background?: string;
  className?: string;
  children?: React.ReactNode;
}

const ShimmerButton = React.forwardRef<HTMLButtonElement, ShimmerButtonProps>(
  (
    {
      shimmerColor = "#ffffff",
      shimmerSize = "1.5px",
      shimmerDuration = "3s",
      borderRadius = "100px",
      background = "rgba(0, 0, 0, 1)",
      className,
      children,
      style,
      ...props
    },
    ref,
  ) => {
    // Ensure cut is at least 1.5px so the border beam is clearly visible
    const cut = shimmerSize === "0.05em" || !shimmerSize ? "1.5px" : shimmerSize;

    const isLight =
      background === "#ffffff" ||
      background === "white" ||
      background.startsWith("#fff") ||
      background.includes("255, 255, 255") ||
      shimmerColor === "#000000" ||
      shimmerColor === "black" ||
      shimmerColor.includes("0, 0, 0");

    return (
      <button
        style={
          {
            "--spread": "90deg",
            "--shimmer-color": shimmerColor,
            "--radius": borderRadius,
            "--speed": shimmerDuration,
            "--cut": cut,
            "--bg": background,
            ...style,
          } as CSSProperties
        }
        className={cn(
          "group relative z-0 flex cursor-pointer items-center justify-center overflow-hidden whitespace-nowrap px-6 py-3 [border-radius:var(--radius)]",
          isLight ? "text-black" : "text-white",
          "transform-gpu transition-transform duration-300 ease-in-out active:translate-y-px bg-transparent",
          className,
        )}
        ref={ref}
        {...props}
      >
        {/* Base rim backdrop for light buttons so black shimmer has crisp high contrast */}
        {isLight && (
          <div
            className="absolute inset-0 pointer-events-none -z-35 bg-white"
            style={{ borderRadius: "var(--radius)" }}
          />
        )}

        {/* 1. Masked Perimeter Border Beam - Strictly confined to outer border */}
        <div
          className="absolute inset-0 pointer-events-none overflow-hidden"
          style={{
            borderRadius: "var(--radius)",
            padding: "var(--cut)",
            WebkitMask:
              "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
            WebkitMaskComposite: "xor",
            mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
            maskComposite: "exclude",
          }}
        >
          <div
            className="animate-spin-around absolute -inset-[200%] w-auto aspect-square m-auto pointer-events-none"
            style={{
              background: `conic-gradient(from 0deg, transparent 0deg, transparent 40deg, var(--shimmer-color, #ffffff) 90deg, transparent 140deg, transparent 360deg)`,
            }}
          />
        </div>

        {/* 2. Subtle background border track */}
        <div
          className={cn(
            "absolute inset-0 pointer-events-none -z-25 border",
            isLight ? "border-neutral-200/80" : "border-white/10"
          )}
          style={{ borderRadius: "var(--radius)" }}
        />

        {/* 3. Backdrop: covers button center with --bg, exposing only the --cut border gap */}
        <div
          className="absolute -z-20 pointer-events-none transition-colors"
          style={{
            inset: "var(--cut)",
            background: "var(--bg)",
            borderRadius: "calc(var(--radius) - var(--cut))",
          }}
        />

        {/* 4. Inset highlight sheen */}
        <div
          className={cn(
            "inset-0 absolute size-full pointer-events-none",
            "px-4 py-1.5 text-sm font-medium",
            isLight
              ? "shadow-[inset_0_-4px_8px_rgba(0,0,0,0.06)]"
              : "shadow-[inset_0_-8px_10px_#ffffff1f] group-hover:shadow-[inset_0_-6px_10px_#ffffff3f] group-active:shadow-[inset_0_-10px_10px_#ffffff3f]",
            "transform-gpu transition-all duration-300 ease-in-out",
          )}
          style={{ borderRadius: "var(--radius)" }}
        />

        {/* 6. Button Content */}
        <span className="relative z-10 flex items-center justify-center gap-2">
          {children}
        </span>
      </button>
    );
  },
);

ShimmerButton.displayName = "ShimmerButton";

export { ShimmerButton };
export default ShimmerButton;
