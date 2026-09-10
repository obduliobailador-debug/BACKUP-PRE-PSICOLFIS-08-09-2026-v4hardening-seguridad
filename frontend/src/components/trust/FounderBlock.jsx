import React from "react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import { Section, Container } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { ImageBlock } from "@/components/content/ImageBlock";

/**
 * FounderBlock — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7C)
 *
 * OPTIONAL trust piece presenting the person behind PSICOLFISNET when a page
 * needs that context. PSICOLFISNET has its own personality and must NOT depend
 * on the founder figure: this block is optional and assumes nothing.
 * Nothing (name/bio/photo) is hardcoded. Reuses ImageBlock.
 *
 * API:
 *   name?, role?, text?
 *   image?   { src, alt }   (optional)
 *   action?  { label, href? }
 *   background?, spacing?
 */
export function FounderBlock({
  name,
  role,
  text,
  image,
  action,
  background = "default",
  spacing = "default",
  className,
}) {
  return (
    <Section background={background} spacing={spacing} className={className}>
      <Container>
        <div
          className={cn(
            "grid items-center gap-8",
            image ? "md:grid-cols-[auto_1fr]" : "",
          )}
        >
          {image ? (
            <div className="w-full max-w-[220px]">
              <ImageBlock src={image.src} alt={image.alt} ratio={1} objectFit="cover" />
            </div>
          ) : null}

          <div className="flex flex-col gap-3">
            {name ? (
              <p className="font-heading text-h3 text-foreground">{name}</p>
            ) : null}
            {role ? (
              <p className="text-sm font-semibold uppercase tracking-wide text-secondary">{role}</p>
            ) : null}
            {text ? <div className="text-body-lg text-muted-foreground">{text}</div> : null}
            {action ? (
              <div className="mt-2">
                {action.href ? (
                  <Button asChild variant="outline">
                    <Link to={action.href}>{action.label}</Link>
                  </Button>
                ) : (
                  <Button variant="outline">{action.label}</Button>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </Container>
    </Section>
  );
}

export default FounderBlock;
