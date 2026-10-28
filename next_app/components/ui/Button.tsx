import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "relative group inline-flex items-center justify-center font-medium transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:pointer-events-none disabled:cursor-not-allowed overflow-hidden rounded-xl",
  {
    variants: {
      variant: {
        default:
          "bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-400 hover:border-blue-400/60 shadow-sm",
        solid:
          "bg-neutral-900 hover:bg-neutral-800 text-white border border-neutral-700/80 hover:border-blue-500/80 shadow-md",
        glow:
          "bg-gradient-to-b from-neutral-900 to-black text-white border border-neutral-700 hover:border-blue-500/80 shadow-[0_0_25px_rgba(59,130,246,0.15)] hover:shadow-[0_0_35px_rgba(59,130,246,0.35)]",
        primary:
          "bg-white text-black hover:bg-neutral-100 border border-neutral-200 font-semibold shadow-md",
        ghost:
          "border-transparent bg-transparent hover:border-neutral-700 hover:bg-white/5 text-neutral-300",
      },
      size: {
        default: "px-6 py-2.5 text-sm",
        sm: "px-3.5 py-1.5 text-xs",
        lg: "px-8 py-3.5 text-base font-semibold",
      },
    },
    defaultVariants: {
      variant: "solid",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  neon?: boolean;
  shimmer?: boolean;
  shimmerColor?: string;
  shimmerDuration?: string;
  shimmerSize?: string;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      neon = false,
      shimmer = true,
      shimmerColor = "#ffffff",
      shimmerDuration = "3s",
      shimmerSize = "1.5px",
      size,
      variant,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        style={
          {
            "--spread": "90deg",
            "--shimmer-color": shimmerColor,
            "--speed": shimmerDuration,
          } as React.CSSProperties
        }
        className={cn(
          buttonVariants({ variant, size }),
          shimmer && "transform-gpu transition-transform duration-300 ease-in-out active:translate-y-px",
          className
        )}
        ref={ref}
        {...props}
      >
        {shimmer && (
          <>
            {/* 1. Masked Rotating perimeter border beam - confined strictly to outer border */}
            <div
              className="absolute -inset-px pointer-events-none overflow-hidden rounded-[inherit] z-0"
              style={{
                padding: shimmerSize,
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

            {/* 2. Highlight */}
            <div
              className={cn(
                "inset-0 absolute size-full pointer-events-none rounded-[inherit]",
                "px-4 py-1.5 text-sm font-medium shadow-[inset_0_-8px_10px_#ffffff1f]",
                "transform-gpu transition-all duration-300 ease-in-out",
                "group-hover:shadow-[inset_0_-6px_10px_#ffffff3f]",
                "group-active:shadow-[inset_0_-10px_10px_#ffffff3f]"
              )}
            />
          </>
        )}
        {neon && (
          <>
            <span
              className="absolute h-px opacity-0 group-hover:opacity-100 transition-all duration-500 ease-in-out inset-x-0 top-0 bg-gradient-to-r w-3/4 mx-auto from-transparent via-blue-500 to-transparent pointer-events-none"
              aria-hidden="true"
            />
            <span
              className="absolute opacity-40 group-hover:opacity-100 transition-all duration-500 ease-in-out inset-x-0 h-px -bottom-px bg-gradient-to-r w-3/4 mx-auto from-transparent via-blue-500 to-transparent pointer-events-none"
              aria-hidden="true"
            />
          </>
        )}
        <span className="relative z-10 flex items-center justify-center gap-2">
          {children}
        </span>
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };
