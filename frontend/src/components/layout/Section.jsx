import React from "react";
import { cn } from "@/lib/utils";

/**
 * Section — PSICOLFISNET 2.0 structural infrastructure (FASE 1 · BLOQUE 3)
 *
 * Centralises vertical rhythm and section background so blocks share the
 * same spacing logic across the future site. Mobile-first.
 *
 * Backgrounds consume BLOQUE 2 tokens (background / background-warm).
 * Vertical spacing uses the native Tailwind scale (no arbitrary values).
 *
 * Renders a semantic <section> by default; override with `as` when needed.
 *
 * Props:
 *   as         - element/component to render (default: "section")
 *   background - "default" | "warm" | "transparent"
 *   spacing    - "compact" | "default" | "spacious"
 *   className  - extra classes (merged, can override)
 */
const BACKGROUNDS = {
  default: "bg-background",
  warm: "bg-background-warm",
  transparent: "bg-transparent",
};

const SPACINGS = {
  compact: "py-10 sm:py-12 lg:py-16", // 40 / 48 / 64
  default: "py-16 sm:py-20 lg:py-24", // 64 / 80 / 96
  spacious: "py-20 sm:py-28 lg:py-32", // 80 / 112 / 128
};

export function Section({
  as: Comp = "section",
  background = "default",
  spacing = "default",
  className,
  children,
  ...props
}) {
  return (
    <Comp
      className={cn(
        BACKGROUNDS[background] ?? BACKGROUNDS.default,
        SPACINGS[spacing] ?? SPACINGS.default,
        className,
      )}
      {...props}
    >
      {children}
    </Comp>
  );
}

export default Section;
