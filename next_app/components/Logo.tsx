import Image from "next/image";
import { cn } from "@/lib/utils";

interface LogoProps {
  size?: number;
  className?: string;
  imageClassName?: string;
  priority?: boolean;
}

export function Logo({
  size = 32,
  className,
  imageClassName,
  priority = false,
}: LogoProps) {
  return (
    <div
      className={cn(
        "relative flex items-center justify-center overflow-hidden rounded-xl bg-black border border-white/10 shadow-xs transition-transform duration-200 shrink-0",
        className
      )}
      style={{ width: size, height: size }}
    >
      <Image
        src="/logo.png"
        alt="Archova.ai Logo"
        width={size}
        height={size}
        priority={priority}
        className={cn("h-full w-full object-cover", imageClassName)}
      />
    </div>
  );
}

export default Logo;

