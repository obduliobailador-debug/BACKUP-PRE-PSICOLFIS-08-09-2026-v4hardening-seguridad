import React from "react";

import { cn } from "@/lib/utils";
import { Section, Container } from "@/components/layout";

/**
 * ProblemBlock — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7B)
 *
 * Helps the visitor recognise themselves ("yes, this is about me"). Neutral,
 * no fear language, no tech feature lists — content is provided by the caller.
 * Works with ONE or MANY items without breaking the composition.
 *
 * API:
 *   eyebrow?      string
 *   title         node (section heading; H2 by default, override with titleAs)
 *   titleAs?      element tag (default "h2")
 *   description?  node
 *   items         array of { title?, description?, icon? }  (variable length)
 *   example?      node (optional example/callout)
 *   media?        node (optional visual support, e.g. <ImageBlock/>)
 *   background?   "default" | "warm" | "transparent" (Section)
 *   spacing?      Section spacing (default "default")
 */
export function ProblemBlock({
  eyebrow,
  title,
  titleAs: TitleTag = "h2",
  description,
  items = [],
  example,
  media,
  background = "default",
  spacing = "default",
  className,
}) {
  const hasItems = Array.isArray(items) && items.length > 0;

  return (
    <Section background={background} spacing={spacing} className={className}>
      <Container>
        <div className="flex max-w-3xl flex-col gap-3">
          {eyebrow ? (
            <p className="text-sm font-semibold uppercase tracking-wide text-secondary">
              {eyebrow}
            </p>
          ) : null}
          {title ? (
            <TitleTag className="font-heading text-h2 text-foreground">{title}</TitleTag>
          ) : null}
          {description ? (
            <p className="text-body-lg text-muted-foreground">{description}</p>
          ) : null}
        </div>

        {hasItems ? (
          <ul
            className={cn(
              "mt-8 grid gap-6",
              items.length > 1 && "sm:grid-cols-2",
            )}
          >
            {items.map((item, i) => (
              <li
                key={item.title ? `${item.title}-${i}` : i}
                className="flex gap-3 rounded-lg border border-border bg-card p-5"
              >
                {item.icon ? (
                  <span className="mt-0.5 shrink-0 text-secondary" aria-hidden="true">
                    {item.icon}
                  </span>
                ) : null}
                <div className="flex flex-col gap-1">
                  {item.title ? (
                    <p className="font-heading text-base font-semibold text-foreground">
                      {item.title}
                    </p>
                  ) : null}
                  {item.description ? (
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        ) : null}

        {example ? <div className="mt-8 max-w-3xl">{example}</div> : null}
        {media ? <div className="mt-8">{media}</div> : null}
      </Container>
    </Section>
  );
}

export default ProblemBlock;
