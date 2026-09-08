/** #como-funciona — 3-step process explainer. */
export const ProcessSection = () => (
  <>
        <section id="como-funciona" className="process-section">
          <div className="section-container">
            <h2 className="section-title">
              Tu IA Personalizada en <span className="text-blue">4 Pasos Sencillos</span>
            </h2>
            <p className="section-subtitle">Desde la primera sesión hasta la optimización continua, te acompañamos en todo el proceso.</p>
            
            <div className="steps-row">
              <div className="step-card-clean reveal reveal-up">
                <div className="step-icon">🔍</div>
                <div className="step-number-blue">01</div>
                <h3>Exploramos tu Negocio</h3>
                <p>Entrevista ligera para entender tu propuesta, tu voz y tus objetivos. Aquí definimos el mapa de tu IA personalizada.</p>
              </div>
              
              <div className="step-card-clean reveal reveal-up" style={{transitionDelay: '100ms'}}>
                <div className="step-icon">⚙️</div>
                <div className="step-number-blue">02</div>
                <h3>Diseñamos tu Agente</h3>
                <p>Configuramos el comportamiento, tono y criterios. Tu IA aprende a pensar contigo (no en tu lugar).</p>
              </div>
              
              <div className="step-card-clean reveal reveal-up" style={{transitionDelay: '200ms'}}>
                <div className="step-icon">🎯</div>
                <div className="step-number-blue">03</div>
                <h3>Integración Digital</h3>
                <p>Lo integramos en tu web, email, atención a clientes o creación de contenidos. Donde más impacto te genere.</p>
              </div>
              
              <div className="step-card-clean reveal reveal-up" style={{transitionDelay: '300ms'}}>
                <div className="step-icon">📈</div>
                <div className="step-number-blue">04</div>
                <h3>Optimización Continua</h3>
                <p>Medimos resultados, afinamos respuestas y ampliamos usos. Evolución continua con foco en ROI.</p>
              </div>
            </div>

            <div className="examples-box-clean">
              <h4>Ejemplos de Uso</h4>
              <ul>
                <li>✓ Responder dudas de clientes con tu tono y criterios</li>
                <li>✓ Redactar ofertas, emails y publicaciones listas</li>
                <li>✓ Crear guiones de vídeo coherentes con tu marca</li>
                <li>✓ Filtrar leads y preparar reuniones con info clave</li>
              </ul>
            </div>
          </div>
        </section>
  </>
);
