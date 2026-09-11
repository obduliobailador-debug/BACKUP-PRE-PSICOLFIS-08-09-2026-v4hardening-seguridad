import { useEffect } from "react";

import { SEO, pageTitle, canonicalUrl } from "./seoConfig";

/**
 * SEOHead — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 9)
 *
 * Dependency-free <head> manager for a React SPA. Imperatively upserts the
 * document title and the relevant meta/link tags via useEffect (no new library,
 * no react-helmet). Tags it creates are marked with data-seo-head so they can
 * be cleaned up on unmount, preventing stale tags across route changes.
 *
 * Never renders empty tags and never invents values for optional fields.
 *
 * API:
 *   title?          string  → "title | PSICOLFISNET" (brand fallback at root)
 *   description?    string  → meta description + og/twitter description (only if provided)
 *   canonicalPath?  string  → resolved against SEO.baseUrl (e.g. "/soluciones")
 *   noIndex?        boolean → robots "noindex,nofollow" (default "index,follow")
 *   ogType?         string  → og:type (default "website")
 *   image?          { url|src, alt?, width?, height? }  → og/twitter image (only if valid)
 */
export function SEOHead({
  title,
  description,
  canonicalPath,
  noIndex = false,
  ogType = SEO.defaultOgType,
  image,
}) {
  useEffect(() => {
    const created = [];
    const restore = [];

    const ensure = (selector, create) => {
      let el = document.head.querySelector(selector);
      if (!el) {
        el = create();
        el.setAttribute("data-seo-head", "1");
        document.head.appendChild(el);
        created.push(el);
      }
      return el;
    };

    // Modify a reused (legacy) attribute, remembering its exact prior state so
    // it can be restored on unmount. If the attribute didn't exist, restoring
    // means removing it again (never leaving "null"/"undefined").
    const setAttr = (el, name, value) => {
      if (created.includes(el)) {
        el.setAttribute(name, value);
        return;
      }
      const had = el.hasAttribute(name);
      const prev = had ? el.getAttribute(name) : null;
      restore.push(() => (had ? el.setAttribute(name, prev) : el.removeAttribute(name)));
      el.setAttribute(name, value);
    };

    const setMeta = (attr, key, value) => {
      if (!value) return;
      const el = ensure(`meta[${attr}="${key}"]`, () => {
        const m = document.createElement("meta");
        m.setAttribute(attr, key);
        return m;
      });
      setAttr(el, "content", value);
    };

    // --- title ---
    const fullTitle = pageTitle(title);
    const previousTitle = document.title;
    document.title = fullTitle;

    // --- canonical + og:url ---
    const url = canonicalPath ? canonicalUrl(canonicalPath) : undefined;
    if (url) {
      const link = ensure('link[rel="canonical"]', () => {
        const l = document.createElement("link");
        l.setAttribute("rel", "canonical");
        return l;
      });
      setAttr(link, "href", url);
    }

    // --- robots ---
    setMeta("name", "robots", noIndex ? "noindex,nofollow" : "index,follow");

    // --- description (only when provided) ---
    setMeta("name", "description", description);

    // --- Open Graph ---
    setMeta("property", "og:site_name", SEO.siteName);
    setMeta("property", "og:type", ogType);
    setMeta("property", "og:title", fullTitle);
    setMeta("property", "og:description", description);
    setMeta("property", "og:url", url);

    // --- image (only when a valid image is provided) ---
    const imgUrl = image ? image.url || image.src : undefined;
    if (imgUrl) {
      setMeta("property", "og:image", imgUrl);
      if (image.alt) setMeta("property", "og:image:alt", image.alt);
      if (image.width) setMeta("property", "og:image:width", String(image.width));
      if (image.height) setMeta("property", "og:image:height", String(image.height));
    }

    // --- Twitter (standard, no invented accounts) ---
    setMeta("name", "twitter:card", imgUrl ? "summary_large_image" : "summary");
    setMeta("name", "twitter:title", fullTitle);
    setMeta("name", "twitter:description", description);
    if (imgUrl) setMeta("name", "twitter:image", imgUrl);

    return () => {
      // Restore reused legacy tags to their exact prior state, then remove
      // only the tags this instance created; restore previous title.
      restore.forEach((fn) => fn());
      created.forEach((el) => el.parentNode && el.parentNode.removeChild(el));
      document.title = previousTitle;
    };
  }, [title, description, canonicalPath, noIndex, ogType, image]);

  return null;
}

export default SEOHead;
