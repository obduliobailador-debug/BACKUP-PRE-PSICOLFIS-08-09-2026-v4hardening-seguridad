import React from "react";

import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { ImageBlock } from "@/components/content/ImageBlock";

/**
 * Testimonial — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7C)
 *
 * Reusable piece for REAL testimonials. Correct citation semantics
 * (<figure> + <blockquote> + <figcaption>). No carousel, no auto stars, no
 * invented ratings. Content is provided by the caller (never invented).
 * Reuses Card + ImageBlock.
 *
 * API:
 *   quote          required
 *   author?, role?, organization?
 *   image?         { src, alt }
 *   className?
 */
export function Testimonial({
  quote,
  author,
  role,
  organization,
  image,
  className,
}) {
  if (!quote) return null;

  const hasMeta = author || role || organization || image;

  return (
    <Card className={cn("h-full", className)}>
      <CardContent className="pt-6">
        <figure className="flex flex-col gap-4">
          <blockquote className="text-body-lg text-foreground">{quote}</blockquote>
          {hasMeta ? (
            <figcaption className="flex items-center gap-3">
              {image ? (
                <div className="h-10 w-10 shrink-0">
                  <ImageBlock src={image.src} alt={image.alt} ratio={1} objectFit="cover" />
                </div>
              ) : null}
              <div className="text-sm">
                {author ? (
                  <span className="font-semibold text-foreground">{author}</span>
                ) : null}
                {(role || organization) ? (
                  <span className="block text-muted-foreground">
                    {[role, organization].filter(Boolean).join(" · ")}
                  </span>
                ) : null}
              </div>
            </figcaption>
          ) : null}
        </figure>
      </CardContent>
    </Card>
  );
}

export default Testimonial;
