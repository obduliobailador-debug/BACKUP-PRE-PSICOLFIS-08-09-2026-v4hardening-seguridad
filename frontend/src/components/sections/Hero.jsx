import React from "react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import { Section, Container } from "@/components/layout";
import { Button } from "@/components/ui/button";

/**
 * Hero — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7B)
 *
 * High-prominence entry section. Content is provided via props (no hardcoded
 * copy, routes, images, sectors or solutions). Composes with ImageBlock when a
 * `media` node is passed. Priority is ONE dominant action.
 *
 * API:
 *   eyebrow?         string
 *   title            node (rendered as H1 by default; override with titleAs)
 *   titleAs?         element tag for the title (default "h1")
 *   description?     node
 *   primaryAction?   { label, href?, ...buttonProps }  (dominant)
 *   secondaryAction? { label, href?, ...buttonProps }  (outline)
 *   media?           node (e.g. <ImageBlock .../>)
 *   align?           "left" | "center"   (default "left")
 *   background?      "default" | "warm" | "transparent"  (forwarded to Section)
 *   spacing?         Section spacing (default "spacious")
 */
function ActionButton({ action, variant = "default", size = "lg" }) {
  if (!action) return null;
  const { label, href, ...rest } = action;
  if (href) {
    return (
      <Button asChild variant={variant} size={size} {...rest}>
        <Link to={href}>{label}</Link>
      </Button>
    );
  }
  return (
    <Button variant={variant} size={size} {...rest}>
      {label}
    </Button>
  );
}

export function Hero({
  eyebrow,
  title,
  titleAs: TitleTag = "h1",
  description,
  primaryAction,
  secondaryAction,
  media,
  align = "left",
  background = "default",
  spacing = "spacious",
  className,
}) {
  const centered = align === "center";
  const hasActions = Boolean(primaryAction || secondaryAction);

  const text = (
    <div
      className={cn(
        "flex flex-col gap-5",
        centered && "items-center text-center",
        centered && "mx-auto max-w-2xl",
      )}
    >
      {eyebrow ? (
        <p className="text-sm font-semibold uppercase tracking-wide text-secondary">
          {eyebrow}
        </p>
      ) : null}
      <TitleTag className="font-heading text-h1 text-foreground">{title}</TitleTag>
      {description ? (
        <p className="text-body-lg text-muted-foreground">{description}</p>
      ) : null}
      {hasActions ? (
        <div
          className={cn(
            "mt-2 flex flex-col gap-3 sm:flex-row",
            centered && "sm:justify-center",
          )}
        >
          <ActionButton action={primaryAction} variant="default" />
          <ActionButton action={secondaryAction} variant="outline" />
        </div>
      ) : null}
    </div>
  );

  return (
    <Section background={background} spacing={spacing} className={className}>
      <Container>
        {media && !centered ? (
          <div className="grid items-center gap-10 lg:grid-cols-2">
            {text}
            <div className="order-first lg:order-last">{media}</div>
          </div>
        ) : (
          <div className="flex flex-col gap-10">
            {text}
            {media ? <div className={cn(centered && "mx-auto w-full max-w-3xl")}>{media}</div> : null}
          </div>
        )}
      </Container>
    </Section>
  );
}

export default Hero;
