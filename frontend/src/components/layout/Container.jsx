import React from "react";
import { cn } from "@/lib/utils";

/**
 * Container — PSICOLFISNET 2.0 structural infrastructure (FASE 1 · BLOQUE 3)
 *
 * Centralises horizontal layout so pages never redefine their own
 * max-width / side padding / centering. Mobile-first.
 *
 * Consumes the BLOQUE 2 token/scale system (native Tailwind spacing).
 * The single source of truth for content width lives here.
 *
 * Props:
 *   as    - element/component to render (default: "div")
 *   size  - "default" | "wide" | "narrow" | "fluid"
 *   className - extra classes (merged, can override)
 */
const SIZES = {
  // Brand content width (matches the legacy 1400px rhythm), defined once.
  default: "max-w-[1400px]",
  // Full-bleed-ish for media-heavy blocks.
  wide: "max-w-[1600px]",
  // Comfortable reading measure for text/legal pages.
  narrow: "max-w-3xl",
  // No max width; fills available space.
  fluid: "max-w-none",
};

export function Container({
  as: Comp = "div",
  size = "default",
  className,
  children,
  ...props
}) {
  return (
    <Comp
      className={cn(
        // centered, full-width up to the cap, coherent side padding
        "mx-auto w-full px-5 sm:px-6 lg:px-10",
        SIZES[size] ?? SIZES.default,
        className,
      )}
      {...props}
    >
      {children}
    </Comp>
  );
}

export default Container;
