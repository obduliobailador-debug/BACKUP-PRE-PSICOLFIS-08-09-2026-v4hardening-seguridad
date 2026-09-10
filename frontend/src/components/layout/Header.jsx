import React from "react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Container } from "./Container";
import { MainNavigation } from "@/components/navigation/MainNavigation";
import { MobileNavigation } from "@/components/navigation/MobileNavigation";
import { brand, primaryCta } from "@/components/navigation/navigationConfig";

/**
 * Header — PSICOLFISNET 2.0 global header (FASE 1 · BLOQUE 4)
 *
 * ONE reusable global header: brand → primary navigation → CTA matriz.
 * Sober, contained height, token-based background with a discreet bottom
 * border. No shadows / glassmorphism / decorative effects.
 *
 * Uses the BLOQUE 3 Container and BLOQUE 2 tokens. Desktop navigation shows
 * from `xl` upwards (where the full nav + long CTA fit cleanly); below that it
 * is hidden and a slot is reserved for MobileNavigation (BLOQUE 5).
 *
 * Props:
 *   mobileTrigger - optional override for the <xl slot. Defaults to the
 *                   BLOQUE 5 MobileNavigation (hamburger + panel).
 */
export function Header({ className, mobileTrigger }) {
  return (
    <header
      className={cn("w-full border-b border-border bg-background", className)}
    >
      <Container>
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Brand → Inicio */}
          <Link
            to={brand.href}
            aria-label={`${brand.label} — Inicio`}
            className="flex shrink-0 items-center rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <img
              src={brand.logoSrc}
              alt={brand.label}
              className="h-8 w-auto"
            />
          </Link>

          {/* Desktop / tablet-wide navigation */}
          <MainNavigation className="hidden xl:flex" />

          {/* Right side: CTA matriz (desktop) + mobile slot (BLOQUE 5) */}
          <div className="flex items-center gap-2">
            <Button asChild className="hidden xl:inline-flex">
              <Link to={primaryCta.href}>{primaryCta.label}</Link>
            </Button>

            {/* Mobile/tablet navigation (< xl): BLOQUE 5 MobileNavigation. */}
            <div className="xl:hidden">{mobileTrigger ?? <MobileNavigation />}</div>
          </div>
        </div>
      </Container>
    </header>
  );
}

export default Header;
