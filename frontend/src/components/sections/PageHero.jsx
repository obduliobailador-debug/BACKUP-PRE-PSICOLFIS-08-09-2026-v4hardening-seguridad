import React from "react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import { Section, Container } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Breadcrumbs } from "@/components/navigation/Breadcrumbs";

function ActionButton({ action }) {
  if (!action) return null;
  const { label, href, ...rest } = action;
  if (href) {
    return (
      <Button asChild {...rest}>
        <Link to={href}>{label}</Link>
      </Button>
    );
  }
  return <Button {...rest}>{label}</Button>;
}

/**
 * PageHero — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7B)
 *
 * Header for INTERIOR pages: orientation + context + hierarchy. Deliberately
 * more contained than Hero (no media two-column layout, a single optional
 * action). Reuses the 7A Breadcrumbs (does NOT duplicate breadcrumb logic).
 *
 * API:
 *   breadcrumbItems?  array for <Breadcrumbs items={...} />
 *   eyebrow?          string
 *   title             node (H1 by default; override with titleAs)
 *   titleAs?          element tag (default "h1")
 *   description?      node
 *   action?           { label, href?, ...buttonProps } (single, optional)
 *   variant?          "default" | "compact"
 *   background?       "default" | "warm" | "transparent" (Section)
 */
export function PageHero({
  breadcrumbItems,
  eyebrow,
  title,
  titleAs: TitleTag = "h1",
  description,
  action,
  variant = "default",
  background = "warm",
  className,
}) {
  const compact = variant === "compact";

  return (
    <Section
      background={background}
      spacing={compact ? "compact" : "default"}
      className={className}
    >
      <Container>
        <div className="flex flex-col gap-4">
          {breadcrumbItems && breadcrumbItems.length ? (
            <Breadcrumbs items={breadcrumbItems} />
          ) : null}

          <div className="flex max-w-3xl flex-col gap-3">
            {eyebrow ? (
              <p className="text-sm font-semibold uppercase tracking-wide text-secondary">
                {eyebrow}
              </p>
            ) : null}
            <TitleTag
              className={cn(
                "font-heading text-foreground",
                compact ? "text-h2" : "text-h1",
              )}
            >
              {title}
            </TitleTag>
            {description ? (
              <p className="text-body-lg text-muted-foreground">{description}</p>
            ) : null}
          </div>

          {action ? (
            <div className="mt-1">
              <ActionButton action={action} />
            </div>
          ) : null}
        </div>
      </Container>
    </Section>
  );
}

export default PageHero;
