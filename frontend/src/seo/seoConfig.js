/**
 * seoConfig — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 9)
 *
 * Single source of GLOBAL, stable SEO data. Only authorised canonical values
 * are declared here. No invented claim / description / address / phone / email
 * / legal logo / social profiles.
 */
export const SEO = Object.freeze({
  siteName: "PSICOLFISNET",
  baseUrl: "https://www.psicolfis.net",
  locale: "es_ES",
  defaultOgType: "website",
});

/**
 * Build a page <title>: "Título de página | PSICOLFISNET".
 * Root/no title falls back to the brand alone.
 * @param {string} [title]
 * @returns {string}
 */
export function pageTitle(title) {
  const t = (title || "").trim();
  return t ? `${t} | ${SEO.siteName}` : SEO.siteName;
}

/**
 * Resolve a robust absolute canonical URL from a clean path.
 * Avoids double slashes, duplicated domain and accidental relative canonicals.
 * Query/hash are stripped unless already absolute and explicitly passed.
 * @param {string} [path]  e.g. "/soluciones"
 * @returns {string}
 */
export function canonicalUrl(path = "/") {
  const base = SEO.baseUrl.replace(/\/+$/, "");

  // If an absolute URL is passed, trust it (explicit decision).
  if (/^https?:\/\//i.test(path)) return path;

  const clean = String(path).split(/[?#]/)[0];
  if (!clean || clean === "/") return `${base}/`;
  return `${base}/${clean.replace(/^\/+/, "").replace(/\/+$/, "")}`;
}
