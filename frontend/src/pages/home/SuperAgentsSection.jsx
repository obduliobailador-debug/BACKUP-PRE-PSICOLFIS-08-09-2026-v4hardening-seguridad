/** #agentes — banner linking to /agentes. Static markup only. */
export const SuperAgentsSection = () => (
  <>
        <section id="agentes" className="super-agents-section">
          <div className="section-container">
            <h2 className="section-title">
              Los 5 <span className="text-blue">Super Agentes</span>
            </h2>
            <p className="section-subtitle">Demostración de agentes que interactúan entre ellos y trabajan de forma coordinada para multiplicar tu productividad.</p>
            
            <div className="agents-interaction">
              <h3 className="interaction-title">🔄 Cómo Interactúan los Agentes</h3>
              
              <div className="agents-flow">
                <div className="agent-box">
                  <div className="agent-icon">💬</div>
                  <h4>Atención al Cliente</h4>
                </div>
                
                <div className="flow-arrow">→</div>
                
                <div className="agent-box">
                  <div className="agent-icon">📊</div>
                  <h4>Asistente de Ventas</h4>
                </div>
                
                <div className="flow-arrow">↔</div>
                
                <div className="agent-box highlighted">
                  <div className="agent-icon">🎯</div>
                  <h4>Coordinador Central</h4>
                </div>
              </div>
              
              <p className="interaction-description">
                Los agentes trabajan en equipo: el Coordinador Central orquesta todas las interacciones, mientras que Atención al Cliente envía leads calificados directamente al Asistente de Ventas.
              </p>
            </div>
          </div>
        </section>
  </>
);
