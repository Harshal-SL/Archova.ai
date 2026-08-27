"use client";

import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

const symbols = [
  "∑", "∫", "π", "√", "∞", "Δ", "θ", "λ", "μ", "σ",
  "φ", "ω", "α", "β", "γ", "∂", "∇", "±", "≈", "≠",
  "≤", "≥", "∈", "∩", "∪", "∀", "∃", "⊂", "×", "÷",
  "ℝ", "ℕ","*","(",")","%","^","!","#","-","~",
];

const bubbles = [
  { id: 1,  sym: 0,  size: 13, left: 4,  delay: 0,  duration: 11, drift: 20  },
  { id: 2,  sym: 1,  size: 18, left: 9,  delay: 2,  duration: 14, drift: -18 },
  { id: 3,  sym: 2,  size: 11, left: 15, delay: 5,  duration: 9,  drift: 15  },
  { id: 4,  sym: 3,  size: 20, left: 21, delay: 1,  duration: 16, drift: -14 },
  { id: 5,  sym: 4,  size: 14, left: 27, delay: 7,  duration: 12, drift: 22  },
  { id: 6,  sym: 5,  size: 16, left: 33, delay: 4,  duration: 15, drift: -12 },
  { id: 7,  sym: 6,  size: 12, left: 39, delay: 9,  duration: 10, drift: 18  },
  { id: 8,  sym: 7,  size: 22, left: 45, delay: 2,  duration: 18, drift: -20 },
  { id: 9,  sym: 8,  size: 15, left: 51, delay: 6,  duration: 13, drift: 14  },
  { id: 10, sym: 9,  size: 19, left: 57, delay: 11, duration: 16, drift: -16 },
  { id: 11, sym: 10, size: 11, left: 63, delay: 4,  duration: 8,  drift: 20  },
  { id: 12, sym: 11, size: 20, left: 69, delay: 8,  duration: 17, drift: -18 },
  { id: 13, sym: 12, size: 13, left: 75, delay: 0,  duration: 11, drift: 12  },
  { id: 14, sym: 13, size: 17, left: 81, delay: 5,  duration: 14, drift: -14 },
  { id: 15, sym: 14, size: 12, left: 87, delay: 13, duration: 9,  drift: 16  },
  { id: 16, sym: 15, size: 18, left: 93, delay: 3,  duration: 15, drift: -10 },
  { id: 17, sym: 16, size: 14, left: 12, delay: 15, duration: 12, drift: 18  },
  { id: 18, sym: 17, size: 20, left: 24, delay: 10, duration: 17, drift: -22 },
  { id: 19, sym: 18, size: 11, left: 36, delay: 7,  duration: 10, drift: 14  },
  { id: 20, sym: 19, size: 15, left: 48, delay: 14, duration: 13, drift: -12 },
  { id: 21, sym: 20, size: 19, left: 60, delay: 16, duration: 15, drift: 20  },
  { id: 22, sym: 21, size: 13, left: 72, delay: 8,  duration: 11, drift: -16 },
  { id: 23, sym: 22, size: 17, left: 84, delay: 12, duration: 14, drift: 14  },
  { id: 24, sym: 23, size: 12, left: 96, delay: 4,  duration: 9,  drift: -18 },
  { id: 25, sym: 24, size: 22, left: 6,  delay: 18, duration: 18, drift: 16  },
  { id: 26, sym: 25, size: 14, left: 18, delay: 6,  duration: 12, drift: -14 },
  { id: 27, sym: 26, size: 18, left: 30, delay: 17, duration: 16, drift: 20  },
  { id: 28, sym: 27, size: 11, left: 42, delay: 3,  duration: 8,  drift: -10 },
  { id: 29, sym: 28, size: 15, left: 54, delay: 13, duration: 13, drift: 18  },
  { id: 30, sym: 29, size: 20, left: 66, delay: 9,  duration: 17, drift: -20 },
  { id: 31, sym: 30, size: 12, left: 78, delay: 2,  duration: 10, drift: 12  },
  { id: 32, sym: 31, size: 17, left: 90, delay: 16, duration: 14, drift: -16 },
];

export default function BubbleBg() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const update = () =>
      setIsDark(document.documentElement.classList.contains("dark"));
    update();
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => observer.disconnect();
  }, []);

  return (
    <div className="bubble-layer">
      {bubbles.map((b) => (
        <span
          key={b.id}
          className="bubble-item"
          style={{
            left: `${b.left}%`,
            fontSize: `${b.size}px`,
            animationDuration: `${b.duration}s`,
            animationDelay: `${b.delay}s`,
            "--bdrift": `${b.drift}px`,
            color: isDark
              ? `rgba(255,255,255,${0.12 + (b.id % 5) * 0.07})`
              : `rgba(0,0,0,${0.10 + (b.id % 5) * 0.06})`,
            textShadow: isDark
              ? "0 0 8px rgba(180,180,255,0.3)"
              : "0 0 6px rgba(80,80,120,0.15)",
          } as CSSProperties}
        >
          {symbols[b.sym]}
        </span>
      ))}
    </div>
  );
}

