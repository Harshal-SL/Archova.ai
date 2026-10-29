"use client";

import React, { useEffect, useState, useRef } from "react";
import { AnimatePresence, motion, MotionConfig } from "framer-motion";
import { ChevronDownIcon, ChevronUp, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type TSelectData = {
  id: string;
  label: string;
  value: string;
  description?: string;
  icon?: string | React.ReactNode;
  disabled?: boolean;
  custom?: React.ReactNode;
};

export type SelectProps = {
  id?: string;
  data?: TSelectData[];
  onChange?: (value: string) => void;
  defaultValue?: string;
  value?: string;
  title?: string;
  placeholder?: string;
  className?: string;
  direction?: "up" | "down";
  dropup?: boolean;
};

export default function Select({
  id: customId,
  data = [],
  onChange,
  defaultValue,
  value,
  title = "Select Option",
  placeholder,
  className,
  direction,
  dropup = false,
}: SelectProps) {
  const autoId = React.useId();
  const selectId = customId || autoId;
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const isExplicitDropup = direction === "up" || Boolean(dropup);
  const [resolvedDirection, setResolvedDirection] = useState<"up" | "down">(
    isExplicitDropup ? "up" : (direction || "down")
  );

  useEffect(() => {
    if (direction === "up" || dropup) {
      setResolvedDirection("up");
    } else if (direction === "down" && !dropup) {
      setResolvedDirection("down");
    } else if (containerRef.current && typeof window !== "undefined") {
      const rect = containerRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      if (spaceBelow < 280 && rect.top > 280) {
        setResolvedDirection("up");
      } else {
        setResolvedDirection("down");
      }
    }
  }, [direction, dropup, open]);

  const isDropup = resolvedDirection === "up";

  const selectedValue = value !== undefined ? value : defaultValue;

  const [selected, setSelected] = useState<TSelectData | undefined>(() => {
    if (selectedValue) {
      return data.find((i) => i.value === selectedValue) || data[0];
    }
    return data[0];
  });

  // Sync when controlled value or data changes
  useEffect(() => {
    if (selectedValue !== undefined) {
      const item = data.find((i) => i.value === selectedValue);
      if (item) {
        setSelected(item);
      }
    } else if (data.length > 0 && !selected) {
      setSelected(data[0]);
    }
  }, [selectedValue, data]);

  // Click outside listener to dismiss dropdown cleanly
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open]);

  const onSelect = (val: string) => {
    const item = data.find((i) => i.value === val);
    if (item && !item.disabled) {
      setSelected(item);
      onChange?.(val);
      setOpen(false);
    }
  };

  return (
    <MotionConfig
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 25,
      }}
    >
      <div
        ref={containerRef}
        className={cn(
          "relative flex items-center justify-center select-none",
          open ? "z-[9999]" : "z-auto",
          className
        )}
      >
        <AnimatePresence mode="popLayout">
          {!open ? (
            <motion.div
              whileTap={{ scale: 0.96 }}
              animate={{ borderRadius: 16 }}
              layout
              layoutId={`dropdown-${selectId}`}
              onClick={() => setOpen(true)}
              className="overflow-hidden rounded-2xl border border-neutral-200/80 bg-white/70 text-neutral-900 shadow-2xs backdrop-blur-md hover:border-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-100 dark:hover:bg-[#161619] dark:hover:border-white/20 transition-colors cursor-pointer"
            >
              <SelectItem
                direction={resolvedDirection}
                item={selected || { id: "empty", label: placeholder || "Select...", value: "" }}
              />
            </motion.div>
          ) : (
            <motion.div
              layout
              animate={{ borderRadius: 18 }}
              layoutId={`dropdown-${selectId}`}
              className={cn(
                "absolute right-0 z-[9999] w-72 sm:w-80 overflow-hidden rounded-[18px] border border-neutral-200/80 bg-white/95 text-neutral-900 py-2 shadow-2xl backdrop-blur-2xl dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-100",
                isDropup ? "bottom-0 origin-bottom" : "top-0 origin-top"
              )}
            >
              <Head setOpen={setOpen} title={title} />
              <div className="w-full max-h-72 overflow-y-auto px-1">
                {data.map((item) => (
                  <SelectItem
                    order={item.value}
                    noDescription={false}
                    key={item.id}
                    item={item}
                    isSelected={selected?.value === item.value}
                    onChange={onSelect}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </MotionConfig>
  );
}

const Head = ({ setOpen, title }: { setOpen: (open: boolean) => void; title: string }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ delay: 0.08 }}
      layout
      className="flex items-center justify-between px-3.5 py-2 border-b border-neutral-200/80 dark:border-[#262626] mb-1"
    >
      <motion.strong layout className="text-xs font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-200">
        {title}
      </motion.strong>
      <button
        type="button"
        onClick={() => setOpen(false)}
        className="flex h-5 w-5 items-center justify-center rounded-full border border-neutral-200/80 bg-white/70 hover:bg-neutral-100 text-neutral-700 dark:border-[#262626] dark:bg-[#161619] dark:hover:bg-[#202024] dark:text-neutral-300 cursor-pointer transition-colors"
      >
        <X size={12} />
      </button>
    </motion.div>
  );
};

type SelectItemProps = {
  item?: TSelectData;
  noDescription?: boolean;
  order?: string;
  isSelected?: boolean;
  onChange?: (val: string) => void;
  direction?: "up" | "down";
};

const itemAnimation = {
  hidden: { opacity: 0, y: 8 },
  visible: (custom: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: custom * 0.04, duration: 0.3 },
  }),
  exit: { opacity: 0, y: 8, transition: { duration: 0.15 } },
};

const SelectItem = ({
  item,
  noDescription = true,
  order,
  isSelected,
  onChange,
  direction = "down",
}: SelectItemProps) => {
  return (
    <motion.div
      className={cn(
        "group flex cursor-pointer items-center justify-between gap-2 px-3 py-1.5 transition-colors rounded-xl",
        noDescription ? "px-3 py-1.5" : "my-0.5",
        isSelected && !noDescription
          ? "bg-[#005dff]/10 text-[#005dff] dark:bg-[#005dff]/20 dark:text-white font-bold"
          : "hover:bg-neutral-100 text-neutral-800 dark:hover:bg-[#161619] dark:text-neutral-200",
        item?.disabled && "opacity-40 pointer-events-none"
      )}
      variants={!noDescription ? itemAnimation : undefined}
      initial={!noDescription ? "hidden" : undefined}
      animate={!noDescription ? "visible" : undefined}
      exit={!noDescription ? "exit" : undefined}
      custom={order ? 1 : 0}
      onClick={() => onChange?.(item?.value || "")}
    >
      <div className="flex items-center gap-2.5 min-w-0">
        {item?.icon && (
          <motion.div
            layout
            className={cn(
              "flex shrink-0 items-center justify-center rounded-lg border border-neutral-200/80 bg-white/70 dark:border-[#262626] dark:bg-[#161619]",
              noDescription ? "h-5 w-5 text-xs" : "h-7 w-7 text-sm"
            )}
          >
            {item.icon}
          </motion.div>
        )}
        <motion.div layout className="flex flex-col min-w-0">
          <motion.strong className="text-xs font-semibold truncate leading-tight">
            {item?.label}
          </motion.strong>
          {!noDescription && item?.description && (
            <span className="truncate text-[10px] text-neutral-500 dark:text-neutral-400 mt-0.5">
              {item.description}
            </span>
          )}
        </motion.div>
      </div>

      {noDescription ? (
        <motion.div layout className="flex items-center justify-center pl-2">
          {direction === "up" ? (
            <ChevronUp className="text-neutral-500 group-hover:text-black dark:text-neutral-400 dark:group-hover:text-white transition-colors" size={14} />
          ) : (
            <ChevronDownIcon className="text-neutral-500 group-hover:text-black dark:text-neutral-400 dark:group-hover:text-white transition-colors" size={14} />
          )}
        </motion.div>
      ) : item?.custom ? (
        <div className="shrink-0 pl-2">{item.custom}</div>
      ) : isSelected ? (
        <div className="h-1.5 w-1.5 rounded-full bg-[#005dff] shrink-0" />
      ) : null}
    </motion.div>
  );
};
