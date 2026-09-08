/** #caracteristicas — "transformation" showcase. Purely presentational. */
export const TransformationSection = () => (
  <>
        <section id="caracteristicas" className="transformation-section">
          <div className="section-container">
            <h2 className="section-title reveal">
              La Transformación es <span className="text-blue">Real</span>
            </h2>
            <p className="section-subtitle reveal">Tu conocimiento convertido en una herramienta que trabaja por ti, 24/7</p>
            
            <div className="transformation-image-large reveal">
              <img
                src="/images/legacy/antes-y-despues.jpeg"
                alt="Comparativa antes y después: de tareas manuales a automatización con agentes de IA"
                loading="lazy"
                width="1200"
                height="600"
              />
            </div>
            
            <div className="transformation-comparison">
              <div className="comparison-card before reveal reveal-left">
                <h3>❌ Antes (Sin IA)</h3>
                <ul>
                  <li>• Tareas repetitivas consumen tu día</li>
                  <li>• Respuestas manuales a cada cliente</li>
                  <li>• Creación de contenido lenta</li>
                  <li>• Sin tiempo para estrategia</li>
                  <li>• Sobrecarga de trabajo constante</li>
                </ul>
              </div>
              
              <div className="comparison-card after reveal reveal-right">
                <h3>✅ Después (Con IA)</h3>
                <ul>
                  <li>✓ Automatización inteligente 24/7</li>
                  <li>✓ Respuestas instantáneas con tu tono</li>
                  <li>✓ Contenido generado en minutos</li>
                  <li>✓ Tiempo libre para crecer tu negocio</li>
                  <li>✓ Productividad multiplicada x10</li>
                </ul>
              </div>
            </div>
          </div>
        </section>
  </>
);
