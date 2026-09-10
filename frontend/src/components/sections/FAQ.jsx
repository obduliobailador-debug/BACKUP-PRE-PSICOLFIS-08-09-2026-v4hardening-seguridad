import React from "react";

import { Section, Container } from "@/components/layout";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

/**
 * FAQ — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7C)
 *
 * Uses the accessible shadcn/Radix Accordion (keyboard, focus, aria, states all
 * handled by Radix). Data-driven; no hardcoded questions. `single` mode by
 * default. No search, categories or extra features.
 *
 * API:
 *   eyebrow?, title?, description?
 *   items    array of { question, answer }
 *   type?    "single" | "multiple"  (default "single")
 *   background?, spacing?
 */
export function FAQ({
  eyebrow,
  title,
  titleAs: TitleTag = "h2",
  description,
  items = [],
  type = "single",
  background = "default",
  spacing = "default",
  className,
}) {
  const hasItems = Array.isArray(items) && items.length > 0;
  const single = type === "single";

  return (
    <Section background={background} spacing={spacing} className={className}>
      <Container>
        <div className="mx-auto flex max-w-3xl flex-col gap-3">
          {eyebrow ? (
            <p className="text-sm font-semibold uppercase tracking-wide text-secondary">{eyebrow}</p>
          ) : null}
          {title ? (
            <TitleTag className="font-heading text-h2 text-foreground">{title}</TitleTag>
          ) : null}
          {description ? (
            <p className="text-body-lg text-muted-foreground">{description}</p>
          ) : null}

          {hasItems ? (
            <Accordion
              type={type}
              collapsible={single ? true : undefined}
              className="mt-4 w-full"
            >
              {items.map((item, i) => (
                <AccordionItem key={`faq-${i}`} value={`faq-${i}`}>
                  <AccordionTrigger className="text-left">{item.question}</AccordionTrigger>
                  <AccordionContent className="text-muted-foreground">
                    {item.answer}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          ) : null}
        </div>
      </Container>
    </Section>
  );
}

export default FAQ;
