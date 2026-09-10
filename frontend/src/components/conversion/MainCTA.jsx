import React from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { primaryCta } from "@/components/navigation/navigationConfig";

/**
 * MainCTA — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7C)
 *
 * Reusable representation of the system's matrix action. Built ON TOP of the
 * Button primitive (does not duplicate it). Centralises the approved default
 * label and a consistent presentation; the destination is configurable.
 *
 * Defaults are taken from navigationConfig.primaryCta:
 *   label "Cuéntanos qué necesitas mejorar", href "/cuentanos", pending true.
 *
 * PENDING handling: while the destination does not exist, MainCTA renders a
 * real DISABLED button (semantically "action not yet available") — never an
 * href="#" link nor a fake/dead button. Once the route exists, pass
 * pending={false} (or flip it in navigationConfig) and it becomes a live link.
 *
 * API:
 *   label?    (default = approved CTA label)
 *   href?     (default = primaryCta.href)
 *   pending?  (default = primaryCta.pending)
 *   variant?, size?, className?, ...buttonProps
 */
export const DEFAULT_CTA_LABEL = primaryCta.label;

export function MainCTA({
  label = primaryCta.label,
  href = primaryCta.href,
  pending = primaryCta.pending,
  variant = "default",
  size = "lg",
  className,
  ...props
}) {
  const navigable = href && !pending;

  if (navigable) {
    return (
      <Button asChild variant={variant} size={size} className={className} {...props}>
        <Link to={href}>{label}</Link>
      </Button>
    );
  }

  return (
    <Button
      type="button"
      variant={variant}
      size={size}
      className={className}
      disabled
      aria-disabled="true"
      {...props}
    >
      {label}
    </Button>
  );
}

export default MainCTA;
