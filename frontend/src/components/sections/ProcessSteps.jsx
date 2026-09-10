import React from "react";

import { cn } from "@/lib/utils";
import { Section, Container } from "@/components/layout";

/**
 * ProcessSteps — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7C)
 *
 * Explains what happens and in what order. Accepts a VARIABLE number of steps
 * (works with 2, 3, 4+). Rendered as a semantic ordered list <ol>. No arrows,
 * lines or complex diagrams. Content comes from the caller.
 *
 * API:
 *   eyebrow?, title?, description?
 *   steps        array of { title, description?, icon?, label? }
 *   background?, spacing?
 */
const COLS = {
  2: "md:grid-cols-2",
  3: "md:grid-cols-3",
  4: "sm:grid-cols-2 lg:grid-cols-4",
};

export function ProcessSteps({
  eyebrow,
  title,
  titleAs: TitleTag = "h2",
  description,
  steps = [],
  background = "default",
  spacing = "default",
  className,
}) {
  const hasSteps = Array.isArray(steps) && steps.length > 0;
  const colClass = COLS[Math.min(steps.length, 4)] ?? COLS[4];

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

        {hasSteps ? (
          <ol className={cn("mt-8 grid gap-6", steps.length > 1 && colClass)}>
            {steps.map((step, i) => (
              <li
                key={step.title ? `${step.title}-${i}` : i}
                className="flex flex-col gap-2 rounded-lg border border-border bg-card p-5"
              >
                <div className="flex items-center gap-3">
                  <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                    {step.label ?? i + 1}
                  </span>
                  {step.icon ? (
                    <span className="text-secondary" aria-hidden="true">{step.icon}</span>
                  ) : null}
                </div>
                {step.title ? (
                  <p className="font-heading text-base font-semibold text-foreground">{step.title}</p>
                ) : null}
                {step.description ? (
                  <p className="text-sm text-muted-foreground">{step.description}</p>
                ) : null}
              </li>
            ))}
          </ol>
        ) : null}
      </Container>
    </Section>
  );
}

export default ProcessSteps;
