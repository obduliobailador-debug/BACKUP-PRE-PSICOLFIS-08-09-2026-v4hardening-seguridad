import React from "react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import { Container } from "./Container";
import {
  footerNavGroups,
  footerResources,
  footerLegal,
  footerContact,
  footerBrand,
} from "./footerConfig";

/**
 * Footer — PSICOLFISNET 2.0 global footer (FASE 1 · BLOQUE 6)
 *
 * Modular, reusable structural asset: curated secondary navigation + trust /
 * legal / contact blocks. Sober and contemporary; uses only BLOQUE 2 tokens,
 * the BLOQUE 3 Container and approved typography. Not integrated into pages
 * here — that will happen when pages are built/migrated.
 *
 * PENDING policy (BLOQUE 6, PASO 12): destinations whose real route does not
 * exist yet are rendered as NON-navigable text (accessible, not interactive) —
 * never as broken links or dead buttons. Only real routes become links.
 */

// A single destination: real route → Link; pending/no route → static text.
function FooterItem({ label, href, pending }) {
  if (pending || !href) {
    return (
      <span className="block py-1 text-sm text-primary-foreground/60">
        {label}
      </span>
    );
  }
  return (
    <Link
      to={href}
      className="block rounded py-1 text-sm text-primary-foreground/80 transition-colors hover:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-foreground/60 focus-visible:ring-offset-2 focus-visible:ring-offset-primary"
    >
      {label}
    </Link>
  );
}

// Column heading: linked when it has a real route, otherwise plain text.
function ColumnHeading({ heading, href, pending }) {
  const base = "mb-2 font-heading text-sm font-semibold text-primary-foreground";
  if (pending || !href) {
    return <p className={base}>{heading}</p>;
  }
  return (
    <p className={base}>
      <Link
        to={href}
        className="rounded transition-colors hover:text-primary-foreground/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-foreground/60 focus-visible:ring-offset-2 focus-visible:ring-offset-primary"
      >
        {heading}
      </Link>
    </p>
  );
}

export function Footer({ className }) {
  const year = new Date().getFullYear();

  return (
    <footer className={cn("bg-primary text-primary-foreground", className)}>
      <Container>
        <div className="grid gap-10 py-14 lg:grid-cols-[1.1fr_2fr]">
          {/* Brand + primary contact action */}
          <div className="flex flex-col gap-6">
            <Link
              to={footerBrand.href}
              aria-label={`${footerBrand.label} — Inicio`}
              className="inline-block rounded font-heading text-2xl font-bold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-foreground/60 focus-visible:ring-offset-2 focus-visible:ring-offset-primary"
            >
              {footerBrand.label}
            </Link>

            <div>
              <p className="text-xs uppercase tracking-wide text-primary-foreground/60">
                {footerContact.heading}
              </p>
              {/* CTA matriz. Destination /cuentanos is pending, so it is shown
                  as prominent NON-interactive text (not a broken link/button)
                  per PASO 12. It becomes a live CTA once its route exists. */}
              <p className="mt-1 max-w-xs font-heading text-lg font-semibold text-primary-foreground">
                {footerContact.cta.label}
              </p>
            </div>
          </div>

          {/* Curated secondary navigation */}
          <nav aria-label="Navegación del pie">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {footerNavGroups.map((group) => (
                <div key={group.heading}>
                  <ColumnHeading
                    heading={group.heading}
                    href={group.href}
                    pending={group.pending}
                  />
                  <ul>
                    {group.items.map((item) => (
                      <li key={item.href ?? item.label}>
                        <FooterItem
                          label={item.label}
                          href={item.href}
                          pending={item.pending}
                        />
                      </li>
                    ))}
                  </ul>
                </div>
              ))}

              {/* Recursos (single, pending) */}
              <div>
                <ColumnHeading
                  heading={footerResources.heading}
                  href={footerResources.href}
                  pending={footerResources.pending}
                />
              </div>

              {/* Legal (real destinations on /legal) */}
              <div>
                <ColumnHeading heading={footerLegal.heading} href={null} pending />
                <ul>
                  {footerLegal.items.map((item) => (
                    <li key={item.label}>
                      <FooterItem
                        label={item.label}
                        href={item.href}
                        pending={item.pending}
                      />
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </nav>
        </div>

        {/* Bottom strip */}
        <div className="flex flex-col gap-3 border-t border-primary-foreground/15 py-6 text-sm text-primary-foreground/70 sm:flex-row sm:items-center sm:justify-between">
          <p>© {year} PSICOLFISNET</p>
          <nav aria-label="Enlaces legales">
            <ul className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <li>
                <Link
                  to="/legal#aviso-legal"
                  className="rounded transition-colors hover:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-foreground/60 focus-visible:ring-offset-2 focus-visible:ring-offset-primary"
                >
                  Aviso legal
                </Link>
              </li>
              <li>
                <Link
                  to="/legal#privacidad"
                  className="rounded transition-colors hover:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-foreground/60 focus-visible:ring-offset-2 focus-visible:ring-offset-primary"
                >
                  Privacidad
                </Link>
              </li>
              <li>
                <Link
                  to="/legal#cookies"
                  className="rounded transition-colors hover:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-foreground/60 focus-visible:ring-offset-2 focus-visible:ring-offset-primary"
                >
                  Cookies
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </Container>
    </footer>
  );
}

export default Footer;
