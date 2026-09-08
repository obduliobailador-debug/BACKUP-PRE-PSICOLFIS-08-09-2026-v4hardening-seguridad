/** #soluciones — teaser for the /soluciones B2B verticals landing. */
export const SectorsSection = () => (
  <>
        <section id="soluciones" className="sectors-section">
          <div className="section-container">
            <div className="sectors-head reveal">
              <span className="sectors-eyebrow">Nuevo · Soluciones por sector</span>
              <h2 className="section-title">
                IA que <span className="text-blue">habla el idioma</span> de tu negocio
              </h2>
              <p className="section-subtitle">
                Más allá de los agentes genéricos, diseñamos sistemas verticales para sectores específicos.
                Pruébalos en vivo y agenda una demo si te encajan.
              </p>
            </div>

            <div className="sectors-grid">
              <a className="sector-card reveal reveal-up" href="/soluciones/inmobiliarias" data-testid="home-sector-inmobiliarias">
                <div className="sector-icon" aria-hidden="true">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                </div>
                <h3>Inmobiliarias</h3>
                <p>Cualifica leads y agenda visitas mientras atiendes a tus clientes actuales.</p>
                <span className="sector-link">Ver solución →</span>
              </a>

              <a className="sector-card reveal reveal-up" href="/soluciones/clinicas-dentales" data-testid="home-sector-dental">
                <div className="sector-icon" aria-hidden="true">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5.5c1-1 2.5-2 4.5-2C19 3.5 21 5 21 8.5c0 4-3 7.5-4 11.5-.5 2-1.5 2-2 0-.5-2-1-4-2-4s-1.5 2-2 4c-.5 2-1.5 2-2 0-1-4-4-7.5-4-11.5C5 5 7 3.5 9.5 3.5c2 0 3.5 1 4.5 2"/></svg>
                </div>
                <h3>Clínicas dentales</h3>
                <p>Reduce cancelaciones, recupera pacientes inactivos y libera la recepción.</p>
                <span className="sector-link">Ver solución →</span>
              </a>

              <a className="sector-card reveal reveal-up" href="/soluciones/salones-belleza" data-testid="home-sector-beauty">
                <div className="sector-icon" aria-hidden="true">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/></svg>
                </div>
                <h3>Salones de belleza</h3>
                <p>Reservas 24/7 por WhatsApp, upsell automático y clientas que vuelven solas.</p>
                <span className="sector-link">Ver solución →</span>
              </a>

              <a className="sector-card sector-card-wish reveal reveal-up" href="/?demo=Tu%20sector" data-testid="home-sector-wish">
                <div className="sector-icon" aria-hidden="true">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14"/></svg>
                </div>
                <h3>Tu sector aquí</h3>
                <p>¿No ves el tuyo? Dinos a qué te dedicas y diseñamos un agente IA a medida.</p>
                <span className="sector-link">Proponer mi sector →</span>
              </a>
            </div>

            <div className="sectors-cta reveal">
              <a href="/soluciones" className="hero-btn primary" data-testid="home-sectors-all">
                Ver todas las soluciones por sector →
              </a>
            </div>
          </div>
        </section>
  </>
);
