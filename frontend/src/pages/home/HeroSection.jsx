/** Marketing hero at the top of the home page. Static markup only. */
export const HeroSection = () => (
  <>
        <section className="hero-section">
          <div className="hero-content">
            <div className="hero-logo-box">
              <img
                src="/images/legacy/psicolfisnet-con-nombre.png"
                alt="Logo PSICOLFIS.NET - Agentes de IA personalizados"
                className="hero-logo"
                width="360"
                height="150"
                fetchPriority="high"
              />
            </div>
            
            <h1 className="hero-title">
              IA con Propósito<br/>
              <span className="hero-highlight">Agentes que Multiplican</span><br/>
              tu Impacto
            </h1>
            
            <p className="hero-subtitle">
              Inteligencias artificiales que piensan como tú, trabajan contigo y liberan<br/>
              tu tiempo.
            </p>
            
            <p className="hero-description">
              No vendemos tecnología: creamos sistemas que te representan y generan<br/>
              resultados reales.
            </p>

            <div className="hero-watermark">PSICOLFIS.NET</div>

            <div className="hero-buttons">
              <button className="hero-btn primary" onClick={() => document.getElementById('agentes').scrollIntoView({behavior: 'smooth'})}>
                <span aria-hidden="true">🤖</span> Descubre los Super Agentes <span aria-hidden="true">→</span>
              </button>
              <button className="hero-btn secondary" onClick={() => document.getElementById('precios').scrollIntoView({behavior: 'smooth'})}>
                <span aria-hidden="true">💰</span> Ver Precios <span aria-hidden="true">→</span>
              </button>
            </div>

            <p className="hero-footer">
              ✨ Autónomos y pequeños negocios • Implementación práctica • Resultados medibles
            </p>

            <button className="scroll-down" onClick={() => window.scrollTo({top: window.innerHeight, behavior: 'smooth'})}>
              Descubre más <span aria-hidden="true">↓</span>
            </button>
          </div>
        </section>
  </>
);
