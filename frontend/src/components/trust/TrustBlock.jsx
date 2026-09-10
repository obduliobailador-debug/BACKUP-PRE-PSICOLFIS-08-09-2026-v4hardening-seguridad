import React from "react";

import { cn } from "@/lib/utils";
import { Section, Container } from "@/components/layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

/**
 * TrustBlock — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7C)
 *
 * Reusable trust block. Shows VERIFIABLE arguments (methodology, privacy,
 * transparency, experience, support, evidence, working criteria) provided by
 * the caller. Reuses Card. No fake seals/certifications/decorative stats.
 *
 * API:
 *   eyebrow?, title?, description?
 *   items      array of { title, description?, icon? }
 *   columns?   2 | 3   (default 3)
 *   background?, spacing?
 */
const COLS = {
  2: "sm:grid-cols-2",
  3: "sm:grid-cols-2 lg:grid-cols-3",
};

export function TrustBlock({
  eyebrow,
  title,
  titleAs: TitleTag = "h2",
  description,
  items = [],
  columns = 3,
  background = "warm",
  spacing = "default",
  className,
}) {
  const hasItems = Array.isArray(items) && items.length > 0;

  return (
    <Section background={background} spacing={spacing} className={className}>
      <Container>
        <div className="flex max-w-3xl flex-col gap-3">
          {eyebrow ? (
            <p className="text-sm font-semibold uppercase tracking-wide text-secondary">{eyebrow}</p>
          ) : null}
          {title ? (
            <TitleTag className="font-heading text-h2 text-foreground">{title}</TitleTag>
          ) : null}
          {description ? (
            <p className="text-body-lg text-muted-foreground">{description}</p>
          ) : null}
        </div>

        {hasItems ? (
          <ul className={cn("mt-8 grid gap-6", items.length > 1 && (COLS[columns] ?? COLS[3]))}>
            {items.map((item, i) => (
              <li key={item.title ? `${item.title}-${i}` : i}>
                <Card className="h-full">
                  <CardHeader className="gap-2">
                    {item.icon ? (
                      <span
                        className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-background text-secondary"
                        aria-hidden="true"
                      >
                        {item.icon}
                      </span>
                    ) : null}
                    <CardTitle className="font-heading text-h3">{item.title}</CardTitle>
                  </CardHeader>
                  {item.description ? (
                    <CardContent className="text-muted-foreground">{item.description}</CardContent>
                  ) : null}
                </Card>
              </li>
            ))}
          </ul>
        ) : null}
      </Container>
    </Section>
  );
}

export default TrustBlock;
