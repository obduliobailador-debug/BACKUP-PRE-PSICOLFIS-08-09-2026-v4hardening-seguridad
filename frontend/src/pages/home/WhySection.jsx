/** #why — value-prop section. Static markup only. */
export const WhySection = () => (
  <>
        <section className="why-section">
          <div className="section-container">
            <h2 className="section-title">
              Por Qué <span className="text-blue">Elegirnos</span>
            </h2>
            <p className="section-subtitle">No somos solo otra herramienta de IA. Somos tu socio estratégico en la transformación digital.</p>
            
            <div className="features-grid-four">
              <div className="feature-card-clean reveal reveal-up">
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                  </svg>
                </div>
                <h3>IA con Alma</h3>
                <p>Cada agente respeta tu voz, tus valores y tu forma de decidir. No son robots genéricos, son extensiones de tu negocio.</p>
              </div>
              
              <div className="feature-card-clean reveal reveal-up" style={{transitionDelay: '100ms'}}>
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </div>
                <h3>Acompañamiento Real</h3>
                <p>Implementación más guía práctica. No te dejamos solo con la herramienta, te acompañamos en cada paso.</p>
              </div>
              
              <div className="feature-card-clean reveal reveal-up" style={{transitionDelay: '200ms'}}>
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                  </svg>
                </div>
                <h3>Resultados Medibles</h3>
                <p>Productividad, presencia e ingresos. Nos enfocamos en lo que realmente mueve la aguja de tu negocio.</p>
              </div>
              
              <div className="feature-card-clean reveal reveal-up" style={{transitionDelay: '300ms'}}>
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <circle cx="12" cy="12" r="6"></circle>
                    <circle cx="12" cy="12" r="2"></circle>
                  </svg>
                </div>
                <h3>Experiencia Transversal</h3>
                <p>Marketing, coaching, asesoría y tecnología. Un enfoque integrado que entiende todos los aspectos de tu negocio.</p>
              </div>
            </div>

            <div className="feature-highlight-clean">
              <h3>Tu Conocimiento, Convertido en una Herramienta que Trabaja por Ti (24/7)</h3>
              <p>Creamos asistentes inteligentes diseñados a tu medida. Cada proyecto captura tu tono, tus valores y tu forma de tomar decisiones. El resultado: una extensión de tu mente y tu negocio que reduce tareas repetitivas, mejora tu comunicación y te devuelve horas al día.</p>
            </div>
          </div>
        </section>
  </>
);
