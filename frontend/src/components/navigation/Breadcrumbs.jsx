import React from "react";
import { Link } from "react-router-dom";

import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

/**
 * Breadcrumbs — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 7A)
 *
 * Thin, DATA-DRIVEN layer on top of the shadcn Breadcrumb primitive
 * (which already provides the correct semantics: <nav aria-label>, list,
 * aria-current="page", screen-reader-friendly separators). This wrapper adds
 * the recognizable function of rendering from an `items` array without
 * hardcoding any PSICOLFISNET route inside the component.
 *
 * API:
 *   <Breadcrumbs items={[
 *     { label: "Inicio", href: "/" },
 *     { label: "Soluciones", href: "/soluciones" },
 *     { label: "Automatización" },   // last = current page (no link)
 *   ]} />
 *
 * Rules:
 *   - The LAST item is the current page: rendered as BreadcrumbPage
 *     (aria-current="page"), never a link.
 *   - A non-last item WITH href → link (React Router). WITHOUT href → plain text.
 *   - Long labels wrap (primitive uses break-words) without breaking layout.
 */
export function Breadcrumbs({ items = [], className, ...props }) {
  if (!Array.isArray(items) || items.length === 0) return null;

  return (
    <Breadcrumb className={className} {...props}>
      <BreadcrumbList>
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <React.Fragment key={`${item.label}-${index}`}>
              <BreadcrumbItem>
                {isLast ? (
                  <BreadcrumbPage>{item.label}</BreadcrumbPage>
                ) : item.href ? (
                  <BreadcrumbLink asChild>
                    <Link to={item.href}>{item.label}</Link>
                  </BreadcrumbLink>
                ) : (
                  <span>{item.label}</span>
                )}
              </BreadcrumbItem>
              {!isLast && <BreadcrumbSeparator />}
            </React.Fragment>
          );
        })}
      </BreadcrumbList>
    </Breadcrumb>
  );
}

export default Breadcrumbs;
