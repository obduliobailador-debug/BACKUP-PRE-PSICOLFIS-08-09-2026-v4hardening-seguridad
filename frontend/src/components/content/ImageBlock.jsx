import React from "react";

import { cn } from "@/lib/utils";
import { AspectRatio } from "@/components/ui/aspect-ratio";

/**
 * ImageBlock — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7A)
 *
 * Centralises the visual/technical treatment of CONTENT images (semantic
 * <img>, not CSS background images). Uses the existing Radix AspectRatio
 * primitive when a ratio is requested.
 *
 * Accessibility — alt handling (never fabricated, never derived from filename):
 *   - Informative image  → caller MUST pass `alt`.
 *   - Decorative image   → pass `decorative` (renders alt="" + aria-hidden).
 *
 * Performance:
 *   - `loading` defaults to "lazy" but can be set to "eager" for critical
 *     LCP/Hero images. Not forced on any future Hero image.
 *
 * API:
 *   src         - image source (required)
 *   alt         - required for informative images
 *   decorative  - boolean; decorative images get alt="" + aria-hidden
 *   ratio       - number (e.g. 16/9); when set, wraps in AspectRatio
 *   objectFit   - "cover" | "contain" | "fill" | "none" | "scale-down"
 *   loading     - "lazy" (default) | "eager"
 *   rounded     - boolean (default true) — token-based radius
 *   className    - wrapper classes
 *   imgClassName - <img> classes
 */
const FIT = {
  cover: "object-cover",
  contain: "object-contain",
  fill: "object-fill",
  none: "object-none",
  "scale-down": "object-scale-down",
};

export function ImageBlock({
  src,
  alt,
  decorative = false,
  ratio,
  objectFit = "cover",
  loading = "lazy",
  rounded = true,
  className,
  imgClassName,
  ...props
}) {
  if (!decorative && (alt === undefined || alt === null)) {
    // Do NOT invent alt text. Warn in dev; render empty alt as a safe fallback.
    // eslint-disable-next-line no-console
    console.warn(
      "ImageBlock: informative image is missing `alt`. Pass `alt` or set `decorative`.",
    );
  }

  const computedAlt = decorative ? "" : alt ?? "";

  const img = (
    <img
      src={src}
      alt={computedAlt}
      aria-hidden={decorative || undefined}
      loading={loading}
      decoding="async"
      className={cn("h-full w-full", FIT[objectFit] ?? FIT.cover, imgClassName)}
      {...props}
    />
  );

  return (
    <div className={cn("overflow-hidden", rounded && "rounded-lg", className)}>
      {ratio ? <AspectRatio ratio={ratio}>{img}</AspectRatio> : img}
    </div>
  );
}

export default ImageBlock;
