import { useEffect } from "react";

/**
 * StructuredData — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 9)
 *
 * Minimal, reusable JSON-LD injector. Receives an ALREADY-VALID schema object
 * (or array of objects) and serialises it into a <script type="application/ld+json">.
 * Uses textContent (NOT dangerouslySetInnerHTML). Cleans up on unmount.
 *
 * It invents nothing: no Organization/LocalBusiness/Person/Product/Review/FAQ/
 * BreadcrumbList are created here. Concrete schemas arrive with real, verifiable
 * content in later blocks — this is only the safe injection infrastructure.
 *
 * API:
 *   data  object | object[]   a valid schema.org JSON-LD payload
 */
export function StructuredData({ data }) {
  useEffect(() => {
    if (!data) return undefined;

    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.setAttribute("data-seo-jsonld", "1");
    try {
      script.textContent = JSON.stringify(data);
    } catch (e) {
      // Invalid payload → do not inject anything.
      console.warn("StructuredData: could not serialise JSON-LD payload.", e);
      return undefined;
    }
    document.head.appendChild(script);

    return () => {
      if (script.parentNode) script.parentNode.removeChild(script);
    };
  }, [data]);

  return null;
}

export default StructuredData;
