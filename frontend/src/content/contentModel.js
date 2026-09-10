/**
 * contentModel — PSICOLFISNET 2.0 (FASE 1 · BLOQUE 8)
 *
 * ARCHITECTURE (data / presentation / composition are kept separate):
 *   CONTENT    = plain JS data objects (this layer)
 *   COMPONENTS = presentation (BLOQUE 7)
 *   PAGES      = composition (FASE 2+)
 *
 * A page's content is a single readable JS object matching the shapes below.
 * Every block is OPTIONAL: a page includes only the blocks it needs, and the
 * ORDER is decided by each page's composition, NOT by this model. There is no
 * generic "section renderer" / type list — this is intentionally NOT a CMS/DSL.
 *
 * Field names align EXACTLY with the existing BLOQUE 7 component APIs, so the
 * page can spread data straight into a component, e.g.:
 *   <PageHero {...content.hero} />           (image → page maps to <ImageBlock/>)
 *   <ProblemBlock {...content.problems} />
 *   <ProcessSteps {...content.process} />    (uses `steps`, see below)
 *   <FAQ {...content.faq} />
 *   <CTASection {...content.cta} />
 *
 * Images and actions are described as DATA only (never JSX / React / functions
 * / href="#"). The page turns image data into <ImageBlock/> at composition time.
 */

/**
 * The approved matrix CTA lives in a SINGLE source of truth
 * (navigationConfig.primaryCta: label "Cuéntanos qué necesitas mejorar",
 * href "/cuentanos", pending true). Re-exported here so content can reference
 * it WITHOUT copying the literal. Example: `cta: { action: matrixCta }`.
 */
export { primaryCta as matrixCta } from "@/components/navigation/navigationConfig";

/**
 * @typedef {Object} ActionContent
 * @property {string} label
 * @property {string} [href]
 * @property {boolean} [pending]   // true when the destination route does not exist yet
 */

/**
 * @typedef {Object} ImageContent
 * @property {string} src
 * @property {string} [alt]        // required for informative images (not fabricated)
 * @property {boolean} [decorative]
 * @property {number} [ratio]      // e.g. 16/9
 * @property {"cover"|"contain"|"fill"|"none"|"scale-down"} [objectFit]
 * @property {"lazy"|"eager"} [loading]
 */

/**
 * @typedef {Object} HeroContent          // → <Hero> / part of <PageHero>
 * @property {string} [eyebrow]
 * @property {string} title
 * @property {string} [description]
 * @property {ActionContent} [primaryAction]
 * @property {ActionContent} [secondaryAction]
 * @property {ImageContent} [image]       // page maps to <ImageBlock/>
 * @property {"left"|"center"} [align]
 */

/**
 * @typedef {Object} PageHeroContent      // → <PageHero>
 * @property {Array<{label:string, href?:string}>} [breadcrumbItems]
 * @property {string} [eyebrow]
 * @property {string} title
 * @property {string} [description]
 * @property {ActionContent} [action]
 * @property {"default"|"compact"} [variant]
 */

/**
 * @typedef {Object} ProblemItem
 * @property {string} [title]
 * @property {string} [description]
 * @property {ImageContent} [icon]        // usually a small icon; may be omitted
 */
/**
 * @typedef {Object} ProblemContent       // → <ProblemBlock>
 * @property {string} [eyebrow]
 * @property {string} [title]
 * @property {string} [description]
 * @property {ProblemItem[]} [items]
 * @property {string} [example]
 */

/**
 * @typedef {Object} BenefitItem
 * @property {string} title
 * @property {string} [description]
 */
/**
 * @typedef {Object} BenefitsContent      // → <BenefitsBlock>
 * @property {string} [eyebrow]
 * @property {string} [title]
 * @property {string} [description]
 * @property {BenefitItem[]} [items]
 * @property {2|3} [columns]
 */

/**
 * @typedef {Object} ProcessStep
 * @property {string} title
 * @property {string} [description]
 * @property {string|number} [label]      // optional step label/number
 */
/**
 * @typedef {Object} ProcessContent       // → <ProcessSteps>  (API uses `steps`)
 * @property {string} [eyebrow]
 * @property {string} [title]
 * @property {string} [description]
 * @property {ProcessStep[]} [steps]
 */

/**
 * @typedef {Object} TrustItem
 * @property {string} title
 * @property {string} [description]
 */
/**
 * @typedef {Object} TrustContent         // → <TrustBlock>
 * @property {string} [eyebrow]
 * @property {string} [title]
 * @property {string} [description]
 * @property {TrustItem[]} [items]
 * @property {2|3} [columns]
 */

/**
 * @typedef {Object} FounderContent       // → <FounderBlock>  (OPTIONAL piece)
 * @property {string} [name]
 * @property {string} [role]
 * @property {string} [text]
 * @property {ImageContent} [image]
 * @property {ActionContent} [action]
 */

/**
 * @typedef {Object} TestimonialContent   // → <Testimonial>
 * @property {string} quote
 * @property {string} [author]
 * @property {string} [role]
 * @property {string} [organization]
 * @property {ImageContent} [image]
 */

/**
 * @typedef {Object} FAQItem
 * @property {string} question
 * @property {string} answer
 */
/**
 * @typedef {Object} FAQContent           // → <FAQ>
 * @property {string} [eyebrow]
 * @property {string} [title]
 * @property {string} [description]
 * @property {FAQItem[]} [items]
 * @property {"single"|"multiple"} [type]
 */

/**
 * @typedef {Object} RelatedLinkItem
 * @property {string} label
 * @property {string} [href]
 * @property {string} [description]
 * @property {boolean} [pending]
 */
/**
 * @typedef {Object} RelatedLinksContent  // → <RelatedLinks>
 * @property {string} [title]
 * @property {RelatedLinkItem[]} [items]
 */

/**
 * @typedef {Object} CTAContent           // → <CTASection> (+ <MainCTA>)
 * @property {string} [eyebrow]
 * @property {string} [title]
 * @property {string} [description]
 * @property {ActionContent} [action]     // defaults to the matrix CTA when omitted
 */

/**
 * @typedef {Object} PageContent
 * @property {string} id                  // stable content id (not a route)
 * @property {import("./contentFamilies").ContentFamily} family
 * @property {HeroContent} [hero]
 * @property {ProblemContent} [problems]
 * @property {BenefitsContent} [benefits]
 * @property {ProcessContent} [process]
 * @property {TrustContent} [trust]
 * @property {FounderContent} [founder]
 * @property {TestimonialContent[]} [testimonials]
 * @property {FAQContent} [faq]
 * @property {RelatedLinksContent} [relatedLinks]
 * @property {CTAContent} [cta]
 */

/**
 * definePageContent — light identity helper.
 *
 * Provides editor discoverability and a single, documented entry point for
 * authoring page content. It does NOT mutate, validate heavily, run business
 * logic or add dependencies — it simply returns the object, typed via JSDoc.
 *
 * @param {PageContent} content
 * @returns {PageContent}
 */
export function definePageContent(content) {
  return content;
}
