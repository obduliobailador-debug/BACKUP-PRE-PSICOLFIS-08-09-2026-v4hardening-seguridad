/**
 * SVG icons for each sector, keyed by slug. Extends the catalogue on the
 * public /soluciones page. Falls back to the "default" icon for sectors
 * created via the admin CMS that don't have a slug we recognize yet.
 */
export const SECTOR_ICONS = {
  inmobiliarias: (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
  ),
  "clinicas-dentales": (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5.5c1-1 2.5-2 4.5-2C19 3.5 21 5 21 8.5c0 4-3 7.5-4 11.5-.5 2-1.5 2-2 0-.5-2-1-4-2-4s-1.5 2-2 4c-.5 2-1.5 2-2 0-1-4-4-7.5-4-11.5C5 5 7 3.5 9.5 3.5c2 0 3.5 1 4.5 2"/></svg>
  ),
  "salones-belleza": (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/></svg>
  ),
};
