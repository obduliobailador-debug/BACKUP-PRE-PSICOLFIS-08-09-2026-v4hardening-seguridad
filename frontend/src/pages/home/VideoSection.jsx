/** Full-width video showcase. Auto-plays, muted, loop. */
export const VideoSection = () => (
  <>
        <section className="video-section">
          <div className="section-container">
            <h2 className="section-title">
              ¿Por qué Necesitas un <span className="text-blue">Super Agente</span>?
            </h2>
            <p className="section-subtitle">Mira cómo nuestros agentes transforman negocios en solo 12 segundos</p>
            
            <div className="video-container">
              {/* YouTube como principal */}
              <iframe
                className="promo-video-youtube"
                src="https://www.youtube.com/embed/v4cSwxZd64U?rel=0"
                title="Agentes de IA - PSICOLFIS"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
              ></iframe>
              {/* Video local como respaldo (oculto) */}
              <video 
                className="promo-video-backup"
                controls
                playsInline
                preload="none"
                poster="/images/legacy/psicolfisnet-con-nombre.png"
                style={{display: 'none'}}
              >
                <source src="/videos/agentes_ia.mp4" type="video/mp4" />
              </video>
            </div>

            <p className="video-cta-text">Descubre cómo multiplicar tu productividad</p>

            <div className="benefits-grid">
              <div className="benefit-card reveal reveal-up">
                <div className="benefit-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <h4>Ahorra 10+ horas/semana</h4>
                <p>Recupera tiempo valioso automatizando tareas repetitivas</p>
              </div>
              <div className="benefit-card reveal reveal-up" style={{transitionDelay: '120ms'}}>
                <div className="benefit-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="1" x2="12" y2="23"></line>
                    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                  </svg>
                </div>
                <h4>Aumenta tus ingresos</h4>
                <p>Responde más rápido y cierra más ventas</p>
              </div>
              <div className="benefit-card reveal reveal-up" style={{transitionDelay: '240ms'}}>
                <div className="benefit-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                  </svg>
                </div>
                <h4>Escala tu negocio</h4>
                <p>Crece sin necesidad de contratar más personal</p>
              </div>
            </div>
          </div>
        </section>
  </>
);
