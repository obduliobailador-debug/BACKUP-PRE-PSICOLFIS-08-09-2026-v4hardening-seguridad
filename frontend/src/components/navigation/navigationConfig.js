/**
 * navigationConfig — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 4)
 *
 * SINGLE SOURCE OF TRUTH for the primary navigation.
 * Consumed by MainNavigation (desktop) now, and by MobileNavigation
 * (BLOQUE 5) later. Presentation reads this config; it does not redeclare
 * menu content inside JSX.
 *
 * `pending: true` marks an APPROVED destination whose real page/route does
 * NOT exist yet. This block does NOT create pages or register routes for
 * them — it only records the architectural direction. See the block report.
 *
 * Route reality check (App.js) at build time of this block:
 *   Real public routes: "/" (Home), "/soluciones" (index), "/soluciones/:slug",
 *                       "/agentes", "/legal".
 *   Everything else below is a pending destination (no page yet).
 */

// Primary CTA ("CTA matriz"). Opens a conversation before the diagnosis.
export const primaryCta = {
  label: "Cuéntanos qué necesitas mejorar",
  href: "/cuentanos",
  pending: true, // route/page not created in this block
};

export const navigation = [
  { type: "link", label: "Inicio", href: "/", end: true, pending: false },

  {
    type: "group",
    label: "Para quién",
    basePath: "/para-quien",
    // "¿PSICOLFISNET trabaja con alguien como yo?"
    items: [
      { label: "Particulares", href: "/para-quien/particulares", pending: true },
      { label: "Autónomos y profesionales", href: "/para-quien/autonomos-profesionales", pending: true },
      { label: "Empresas", href: "/para-quien/empresas", pending: true },
    ],
  },

  {
    type: "group",
    label: "Soluciones",
    basePath: "/soluciones", // index route exists
    // "¿PSICOLFISNET puede ayudarme con este problema?"
    items: [
      { label: "Diagnóstico PSICOLFISNET", href: "/soluciones/diagnostico", pending: true },
      { label: "Automatización y ahorro de tiempo", href: "/soluciones/automatizacion", pending: true },
      { label: "Captación y seguimiento", href: "/soluciones/captacion-seguimiento", pending: true },
      { label: "Atención al cliente", href: "/soluciones/atencion-cliente", pending: true },
      { label: "Presencia digital", href: "/soluciones/presencia-digital", pending: true },
      { label: "Soluciones personalizadas", href: "/soluciones/personalizadas", pending: true },
    ],
  },

  {
    type: "group",
    label: "Sectores",
    basePath: "/sectores",
    // "¿Conocen realmente mi tipo de negocio?"
    items: [
      { label: "Asesorías y despachos profesionales", href: "/sectores/asesorias-despachos", pending: true },
      { label: "Hostelería y restauración", href: "/sectores/hosteleria", pending: true },
      { label: "Consultores, coaches y formadores", href: "/sectores/consultores-coaches-formadores", pending: true },
    ],
  },

  {
    type: "group",
    label: "Tecnología",
    basePath: "/tecnologia",
    // Trust/checking layer — intentionally NON-dominant. Must never shift the
    // focus from problem→solution towards tool→technology.
    secondary: true,
    items: [
      { label: "Tecnología", href: "/tecnologia", pending: true },
      { label: "Productos PSICOLFISNET", href: "/productos", pending: true },
    ],
  },

  // Direct entry, no dropdown in this phase. Gateway to future resources.
  { type: "link", label: "Recursos", href: "/recursos", pending: true },

  {
    type: "group",
    label: "PSICOLFISNET",
    basePath: "/psicolfisnet",
    // Confidence generator.
    items: [
      { label: "Quién está detrás de PSICOLFISNET", href: "/psicolfisnet/quien-esta-detras", pending: true },
      { label: "Confianza y privacidad", href: "/confianza-privacidad", pending: true },
    ],
  },
];

// Brand asset (reused existing wordmark; NOT redesigned).
export const brand = {
  label: "PSICOLFISNET",
  href: "/", // Inicio route exists
  logoSrc: "/images/legacy/psicolfisnet-con-nombre.png",
};
