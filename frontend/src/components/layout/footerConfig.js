/**
 * footerConfig — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 6)
 *
 * Footer-specific configuration. Secondary-navigation groups are DERIVED from
 * navigationConfig.js (single source of truth) — labels/URLs are not rewritten.
 * Only genuinely footer-specific data (legal + contact) is declared here.
 *
 * `pending: true` marks an approved destination whose real page/route does NOT
 * exist yet. The Footer renders pending destinations as NON-navigable text
 * (never as broken links / dead buttons). See the block report.
 */
import { navigation, primaryCta } from "@/components/navigation/navigationConfig";

const byLabel = (label) => navigation.find((n) => n.label === label);

// Curated secondary-navigation columns (NOT a dump of the whole site).
export const footerNavGroups = [
  {
    heading: "PSICOLFISNET",
    href: null, // /psicolfisnet route not created yet
    pending: true,
    items: byLabel("PSICOLFISNET")?.items ?? [],
  },
  {
    heading: "Para quién",
    href: null, // /para-quien route not created yet
    pending: true,
    items: byLabel("Para quién")?.items ?? [],
  },
  {
    heading: "Soluciones",
    href: "/soluciones", // real index route exists
    pending: false,
    items: byLabel("Soluciones")?.items ?? [],
  },
  {
    heading: "Sectores",
    href: null, // /sectores route not created yet
    pending: true,
    items: byLabel("Sectores")?.items ?? [],
  },
];

// Recursos: single destination, still pending.
const recursos = byLabel("Recursos");
export const footerResources = {
  heading: "Recursos",
  href: recursos?.href ?? "/recursos",
  pending: recursos?.pending ?? true,
};

// Legal — ONLY real destinations. The three sections live on the single real
// /legal page (section ids: #aviso-legal, #privacidad, #cookies).
export const footerLegal = {
  heading: "Legal",
  items: [
    { label: "Aviso legal", href: "/legal#aviso-legal", pending: false },
    { label: "Privacidad", href: "/legal#privacidad", pending: false },
    { label: "Cookies", href: "/legal#cookies", pending: false },
    // No dedicated page/route yet:
    { label: "Condiciones de contratación", href: null, pending: true },
  ],
};

// Contact — primary action is the CTA matriz. Contact CHANNELS are intentionally
// omitted: all inherited data (email obdulio@psicolfis.net, domain psicolfis.net)
// belongs to "PSICOLFIS.NET" and cannot be confirmed as PSICOLFISNET 2.0 data.
export const footerContact = {
  heading: "Contacto",
  cta: primaryCta, // "Cuéntanos qué necesitas mejorar" — /cuentanos (pending)
};

// Discreet typographic brand presence (the legacy PNG is on a white background
// and reads "PSICOLFIS.NET"; a typographic wordmark is used for reliable
// contrast on the footer — no logo is created or redesigned).
export const footerBrand = {
  label: "PSICOLFISNET",
  href: "/", // Inicio route exists
};
