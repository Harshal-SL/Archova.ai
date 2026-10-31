"use client";

import React, { useState, useRef, useEffect } from "react";
import { Download, RefreshCw, Image, FileImage, ChevronDown } from "lucide-react";
import { downloadReactFlowCanvas, type ImageFormat } from "@/lib/download-design";
import { useAppStore } from "@/lib/store";
import type { Node } from "@xyflow/react";

interface DownloadDesignDropdownProps {
  getContainerElement?: () => HTMLElement | null;
  containerSelector?: string;
  nodes?: Node[];
  designTitle?: string;
  className?: string;
}

export default function DownloadDesignDropdown({
  getContainerElement,
  containerSelector,
  nodes = [],
  designTitle = "Architecture-Design",
  className = "",
}: DownloadDesignDropdownProps) {
  const { theme } = useAppStore();
  const isDark = theme === "dark";

  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState<ImageFormat | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as HTMLElement)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleDownload = async (format: ImageFormat) => {
    if (isExporting) return;
    setIsExporting(format);
    setIsOpen(false);

    try {
      let targetEl: HTMLElement | null = null;
      if (getContainerElement) {
        targetEl = getContainerElement();
      } else if (containerSelector) {
        targetEl = document.querySelector<HTMLElement>(containerSelector);
      } else {
        // Fallback: look for the nearest React Flow wrapper
        targetEl =
          dropdownRef.current?.closest(".react-flow") as HTMLElement ||
          document.querySelector<HTMLElement>(".react-flow");
      }

      const sanitizedTitle = designTitle.replace(/[^a-zA-Z0-9_-]/g, "-").toLowerCase();
      const filename = `archova-${sanitizedTitle}-${new Date().toISOString().slice(0, 10)}.${format === "jpeg" ? "jpg" : "png"}`;

      await downloadReactFlowCanvas(targetEl, nodes, {
        filename,
        format,
        isDark,
        quality: 0.95,
      });
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setIsExporting(null);
    }
  };

  return (
    <div ref={dropdownRef} className={`relative inline-block pointer-events-auto ${className}`}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={!!isExporting}
        className="flex items-center gap-1.5 rounded-xl border border-neutral-200/80 bg-white/70 px-3 py-1.5 text-xs font-semibold text-neutral-700 backdrop-blur-md hover:border-black hover:text-black dark:border-[#262626] dark:bg-[#0D0D0F] dark:text-neutral-300 dark:hover:bg-[#161619] dark:hover:border-white/20 dark:hover:text-white shadow-2xs cursor-pointer transition-all duration-150 disabled:opacity-50"
        title="Download Architecture Design as PNG or JPEG"
      >
        {isExporting ? (
          <RefreshCw className="h-3.5 w-3.5 animate-spin text-[#005dff]" />
        ) : (
          <Download className="h-3.5 w-3.5" />
        )}
        <span>{isExporting ? `Exporting ${isExporting.toUpperCase()}...` : "Download"}</span>
        <ChevronDown className={`h-3 w-3 text-neutral-400 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-1.5 z-50 w-52 rounded-xl border border-neutral-200 bg-white/95 p-1.5 shadow-xl backdrop-blur-xl animate-in fade-in-50 zoom-in-95 duration-100 dark:border-neutral-800 dark:bg-[#0D0D0F]/95">
          <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
            Export Design Format
          </div>

          {/* PNG Option */}
          <button
            type="button"
            onClick={() => handleDownload("png")}
            className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-xs font-medium text-neutral-700 hover:bg-neutral-100 hover:text-black dark:text-neutral-200 dark:hover:bg-neutral-800/80 dark:hover:text-white transition-colors cursor-pointer"
          >
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-500/10 text-blue-500 dark:bg-blue-500/20">
              <FileImage className="h-3.5 w-3.5" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-black dark:text-white">PNG Image (.png)</span>
              <span className="text-[10px] text-neutral-400 dark:text-neutral-500">High-res lossless quality</span>
            </div>
          </button>

          {/* JPEG Option */}
          <button
            type="button"
            onClick={() => handleDownload("jpeg")}
            className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-xs font-medium text-neutral-700 hover:bg-neutral-100 hover:text-black dark:text-neutral-200 dark:hover:bg-neutral-800/80 dark:hover:text-white transition-colors cursor-pointer"
          >
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-amber-500/10 text-amber-500 dark:bg-amber-500/20">
              <Image className="h-3.5 w-3.5" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-black dark:text-white">JPEG Image (.jpg)</span>
              <span className="text-[10px] text-neutral-400 dark:text-neutral-500">Compact standard raster</span>
            </div>
          </button>
        </div>
      )}
    </div>
  );
}

