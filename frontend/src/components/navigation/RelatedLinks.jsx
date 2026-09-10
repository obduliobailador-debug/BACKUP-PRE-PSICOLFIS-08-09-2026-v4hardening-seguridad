import React from "react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";

/**
 * RelatedLinks — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7C)
 *
 * Contextual navigation: "what makes sense to see next?". Data-driven; no
 * hardcoded PSICOLFISNET routes. Real destinations render as links; pending /
 * non-navigable destinations render as plain text (never href="#", never dead
 * buttons). Simple presentation (nav + list), not giant cards.
 *
 * API:
 *   title?   heading (rendered as H2 by default; override with titleAs)
 *   items    array of { label, href?, description?, pending? }
 *   className?
 */
export function RelatedLinks({
  title,
  titleAs: TitleTag = "h2",
  items = [],
  className,
}) {
  if (!Array.isArray(items) || items.length === 0) return null;

  return (
    <nav aria-label={title || "Enlaces relacionados"} className={cn("flex flex-col gap-4", className)}>
      {title ? (
        <TitleTag className="font-heading text-h3 text-foreground">{title}</TitleTag>
      ) : null}
      <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
        {items.map((item, i) => {
          const navigable = item.href && !item.pending;
          const inner = (
            <>
              <span className="font-medium">{item.label}</span>
              {item.description ? (
                <span className="block text-sm text-muted-foreground">{item.description}</span>
              ) : null}
            </>
          );
          return (
            <li key={item.href ? `${item.href}-${i}` : `${item.label}-${i}`}>
              {navigable ? (
                <Link
                  to={item.href}
                  className="block p-4 text-foreground transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  {inner}
                </Link>
              ) : (
                <span className="block p-4 text-muted-foreground">{inner}</span>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export default RelatedLinks;
