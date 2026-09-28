import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const alertVariants = cva(
  "relative w-full rounded-2xl border p-4 text-xs sm:text-sm [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-2px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 backdrop-blur-md transition-all",
  {
    variants: {
      variant: {
        default:
          "border-neutral-700/70 bg-neutral-900/70 text-neutral-200 [&>svg]:text-neutral-300",
        destructive:
          "border-red-900/60 bg-red-950/50 text-red-200 [&>svg]:text-red-400 shadow-[0_0_20px_rgba(239,68,68,0.1)]",
        success:
          "border-emerald-800/60 bg-emerald-950/50 text-emerald-200 [&>svg]:text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.1)]",
        info:
          "border-blue-800/60 bg-blue-950/50 text-blue-200 [&>svg]:text-blue-400 shadow-[0_0_20px_rgba(59,130,246,0.1)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
));
Alert.displayName = "Alert";

const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-semibold leading-none tracking-tight", className)}
    {...props}
  />
));
AlertTitle.displayName = "AlertTitle";

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-xs leading-relaxed opacity-90", className)}
    {...props}
  />
));
AlertDescription.displayName = "AlertDescription";

export { Alert, AlertTitle, AlertDescription };
