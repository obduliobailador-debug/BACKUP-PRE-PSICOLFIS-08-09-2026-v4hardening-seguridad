import React from "react";

import { cn } from "@/lib/utils";
import { Section, Container } from "@/components/layout";
import { MainCTA } from "./MainCTA";

/**
 * CTASection — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7C)
 *
 * Full page-closing block: context + closure + ONE dominant action. Uses
 * Section + Container and token-based background. Not to be confused with
 * MainCTA (which is only the action). Defaults its action to <MainCTA />.
 *
 * API:
 *   eyebrow?, title, description?
 *   action?    node (default <MainCTA />)
 *   support?   node (optional trust support under the action)
 *   align?     "center" | "left"  (default "center")
 *   background?  "default" | "warm" | "transparent"  (default "warm")
 *   spacing?
 */
export function CTASection({
  eyebrow,
  title,
  titleAs: TitleTag = "h2",
  description,
  action,
  support,
  align = "center",
  background = "warm",
  spacing = "spacious",
  className,
}) {
  const centered = align === "center";
  const resolvedAction = action ?? <MainCTA />;

  return (
    <Section background={background} spacing={spacing} className={className}>
      <Container>
        <div
          className={cn(
            "flex flex-col gap-5",
            centered && "mx-auto max-w-2xl items-center text-center",
          )}
        >
          {eyebrow ? (
            <p className="text-sm font-semibold uppercase tracking-wide text-secondary">{eyebrow}</p>
          ) : null}
          {title ? (
            <TitleTag className="font-heading text-h2 text-foreground">{title}</TitleTag>
          ) : null}
          {description ? (
            <p className="text-body-lg text-muted-foreground">{description}</p>
          ) : null}
          <div className={cn("mt-2", centered && "flex justify-center")}>{resolvedAction}</div>
          {support ? (
            <div className="text-sm text-muted-foreground">{support}</div>
          ) : null}
        </div>
      </Container>
    </Section>
  );
}

export default CTASection;
