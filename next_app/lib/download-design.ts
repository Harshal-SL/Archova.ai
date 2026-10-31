import { toPng, toJpeg } from "html-to-image";
import { getNodesBounds, getViewportForBounds, type Node } from "@xyflow/react";

export type ImageFormat = "png" | "jpeg";

export interface DownloadDesignOptions {
  filename?: string;
  format?: ImageFormat;
  isDark?: boolean;
  quality?: number; // 0.1 to 1.0 for JPEG
  backgroundColor?: string;
  padding?: number;
}

/**
 * Downloads a React Flow canvas as a high-resolution PNG or JPEG file.
 * Captures all nodes cleanly even if they extend beyond the current viewport.
 */
export async function downloadReactFlowCanvas(
  containerEl: HTMLElement | null,
  nodes: Node[] = [],
  options: DownloadDesignOptions = {}
): Promise<void> {
  if (!containerEl) {
    throw new Error("Target container element not found for download");
  }

  const format = options.format || "png";
  const isDark = options.isDark ?? true;
  const defaultBg = isDark ? "#0D0D0F" : "#ffffff";
  const bg = options.backgroundColor || defaultBg;
  const padding = options.padding ?? 64;

  const dateStr = new Date().toISOString().slice(0, 10);
  const defaultFilename = `Archova-Design-${dateStr}.${format === "jpeg" ? "jpg" : "png"}`;
  const filename = options.filename || defaultFilename;

  // Find the React Flow viewport container
  const viewportEl = containerEl.querySelector<HTMLElement>(".react-flow__viewport");

  // Filter function to remove UI chrome (controls, minimap, panels)
  const filter = (node: HTMLElement) => {
    if (!node || !node.classList) return true;
    const cls = String(node.classList);
    if (
      cls.includes("react-flow__panel") ||
      cls.includes("react-flow__controls") ||
      cls.includes("react-flow__minimap") ||
      cls.includes("react-flow__attribution")
    ) {
      return false;
    }
    return true;
  };

  try {
    let dataUrl: string;

    if (viewportEl && nodes && nodes.length > 0) {
      // Calculate total bounding box of all nodes
      const bounds = getNodesBounds(nodes);
      const width = Math.max(900, Math.round(bounds.width + padding * 2));
      const height = Math.max(650, Math.round(bounds.height + padding * 2));

      // Calculate perfect viewport transform to fit all nodes cleanly inside the exported image
      const viewport = getViewportForBounds(
        bounds,
        width,
        height,
        0.2,
        2.5,
        padding
      );

      const captureOptions = {
        backgroundColor: bg,
        width,
        height,
        style: {
          width: `${width}px`,
          height: `${height}px`,
          transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})`,
        },
        filter,
        pixelRatio: 2, // 2x Retina resolution for ultra-sharp diagrams
        quality: options.quality ?? 0.95,
      };

      if (format === "jpeg") {
        dataUrl = await toJpeg(viewportEl, captureOptions);
      } else {
        dataUrl = await toPng(viewportEl, captureOptions);
      }
    } else {
      // Fallback: capture entire container directly
      const captureOptions = {
        backgroundColor: bg,
        filter,
        pixelRatio: 2,
        quality: options.quality ?? 0.95,
      };

      if (format === "jpeg") {
        dataUrl = await toJpeg(containerEl, captureOptions);
      } else {
        dataUrl = await toPng(containerEl, captureOptions);
      }
    }

    // Trigger browser download
    const link = document.createElement("a");
    link.download = filename;
    link.href = dataUrl;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (err) {
    console.error("Failed to export design image:", err);
    throw err;
  }
}

