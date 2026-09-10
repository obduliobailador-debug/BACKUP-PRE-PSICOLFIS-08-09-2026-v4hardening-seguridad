/**
 * contentFamilies — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 8)
 *
 * Stable EDITORIAL vocabulary to classify future page content. A family
 * describes the editorial TYPE of a page; it does NOT control routing
 * (React Router stays decoupled) and does NOT generate routes.
 *
 * Derived from the real primary navigation:
 *   home          → Inicio
 *   audience      → "Para quién" (Particulares / Autónomos / Empresas)
 *   solution      → "Soluciones"
 *   sector        → "Sectores"
 *   technology    → "Tecnología" / Productos
 *   resource      → "Recursos"
 *   institutional → "PSICOLFISNET" (quién está detrás, confianza y privacidad)
 */
export const CONTENT_FAMILIES = Object.freeze({
  HOME: "home",
  AUDIENCE: "audience",
  SOLUTION: "solution",
  SECTOR: "sector",
  TECHNOLOGY: "technology",
  RESOURCE: "resource",
  INSTITUTIONAL: "institutional",
});

/** @typedef {"home"|"audience"|"solution"|"sector"|"technology"|"resource"|"institutional"} ContentFamily */

/** All valid family values (for reference/validation by future pages). */
export const CONTENT_FAMILY_VALUES = Object.freeze(Object.values(CONTENT_FAMILIES));

/** @param {string} value @returns {boolean} */
export function isContentFamily(value) {
  return CONTENT_FAMILY_VALUES.includes(value);
}
