import { useState, useEffect } from "react";
import { AGENT_STRIPE_URLS, AGENT_STRIPE_URLS_FULL } from "../api";
import { agents } from "../data/agents";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { usePageSeo } from "../lib/seo";
import { WhatsAppFAB } from "../components/WhatsAppFAB";

export const AgentesPage = () => {
  usePageSeo({
    title: 'Agentes de IA: IRIS, ALEX y UMBRAL · PSICOLFIS.NET',
    description: 'Conoce a IRIS, ALEX y UMBRAL: tres agentes de IA personalizados para vida digital, trabajo y bienestar. Desde 50€ en demostración real con disponibilidad limitada.',
    canonicalPath: '/agentes',
  });
  const [loading, setLoading] = useState({});
  const [legalOpen, setLegalOpen] = useState(false);

  const agentesData = [
    {
      id: "iris",
      name: "IRIS",
      description: "Tu compañera inteligente para pensar mejor tu vida digital, personal y profesional. Es lúcida, empática y actual. Combina calidez humana con pensamiento claro y criterio propio. No actúa como gurú ni como coach motivacional. Camina al lado de la usuaria con serenidad, ayudándole a pensar mejor, ordenar ideas y ampliar perspectivas. IRIS inspira sin imponer, acompaña sin crear dependencia y aporta claridad sin simplificar en exceso.",
      video: "/videos/iris_sonriendo.mp4",
      price: "50€"
    },
    {
      id: "alex",
      name: "ALEX",
      description: "ALEX te ayuda a pensar mejor para avanzar mejor. Trabajo, dinero, decisiones, deporte, motor y tecnología explicados con claridad, enfoque práctico y criterio realista. Un apoyo claro para quien quiere mejorar sin perder el tiempo.",
      video: "/videos/alex_sonriendo.mp4",
      price: "50€"
    },
    {
      id: "umbral",
      name: "UMBRAL",
      description: "Un espacio de conversación para personas LGTBIQ+ que viven sus relaciones, su identidad y sus decisiones con libertad, con la calma necesaria, con conciencia y sin etiquetas impuestas. Y también UMBRAL es una importante ayuda a la hora de encontrar compras de interés.",
      video: "/videos/umbral_sonriendo.mp4",
      price: "50€"
    }
  ];

  const handleBuyAgent = (agentId, level = "demo") => {
    const map = level === "full" ? AGENT_STRIPE_URLS_FULL : AGENT_STRIPE_URLS;
    const url = map[agentId];
    if (url) {
      window.location.href = url;
    } else {
      alert("Enlace de pago no disponible para este agente.");
    }
  };

  return (
    <div className="agentes-page-v2">
      {/* Partículas decorativas */}
      <div className="particles">
        <div className="particle p1"></div>
        <div className="particle p2"></div>
        <div className="particle p3"></div>
        <div className="particle p4"></div>
        <div className="particle p5"></div>
        <div className="particle p6"></div>
        <div className="particle p7"></div>
        <div className="particle p8"></div>
      </div>

      <div className="agentes-container-v2">
        {/* Header Section */}
        <div className="agentes-hero-section">
          <div className="hero-card-v2">
            <h1 className="hero-title-v2">Agentes de IA para tu Bienestar</h1>
            <p className="hero-subtitle-v2">
              Herramientas inteligentes diseñadas para acompañarte en tu desarrollo personal
            </p>
          </div>
        </div>

        {/* Section Title */}
        <div className="section-header-v2">
          <h2 className="section-title-v2">Nuestros Agentes</h2>
          <p className="section-subtitle-v2">✨ Descubre tu compañero de IA perfecto ✨</p>
        </div>

        {/* Agents Grid */}
        <div className="agentes-grid-v2">
          {agentesData.map((agent) => (
            <div key={agent.id} className="agente-card-v2" data-testid={`agente-card-${agent.id}`}>
              <div className="agente-avatar-container">
                <div className="avatar-glow"></div>
                <video
                  src={agent.video}
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="agente-avatar-video"
                />
              </div>
              <div className="agente-content-v2">
                <h3 className="agente-name-v2">{agent.name}</h3>
                <p className="agente-description-v2">{agent.description}</p>
                <div className="agente-footer-v2">
                  <div className="agente-price-wrap-v2">
                    <span className="agente-price-v2">{agent.price}</span>
                    <span className="agente-offer-note-v2">Elige el plan que prefieras</span>
                  </div>
                  <div className="agente-actions-v2">
                    <button
                      className="agente-buy-btn-v2 agente-buy-demo"
                      onClick={() => handleBuyAgent(agent.id, "demo")}
                      disabled={loading[agent.id]}
                      data-testid={`agente-buy-${agent.id}`}
                    >
                      {loading[agent.id] ? "Procesando..." : "Demo limitada"}
                    </button>
                    <button
                      className="agente-buy-btn-v2 agente-buy-full"
                      onClick={() => handleBuyAgent(agent.id, "full")}
                      disabled={loading[agent.id]}
                      data-testid={`agente-buy-full-${agent.id}`}
                    >
                      Acceso total
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Botón volver al inicio */}
        <div className="back-home-section">
          <a href="/" className="back-home-btn">
            ← Volver a la página principal
          </a>
        </div>

        {/* Footer Legal Desplegable */}
        <div className="legal-accordion">
          <button 
            className={`legal-accordion-header ${legalOpen ? 'open' : ''}`}
            onClick={() => setLegalOpen(!legalOpen)}
          >
            <span className="legal-icon">▶ ⚖️</span>
            <span>Aviso Legal y Condiciones de Uso</span>
            <span className={`legal-arrow ${legalOpen ? 'open' : ''}`}>▼</span>
          </button>

          {legalOpen && (
            <div className="legal-accordion-content">
              <div className="legal-warning-box">
                <p><strong>AVISO:</strong> Cualquier persona que acceda, utilice o contrate los AGENTES, por el solo hecho de hacerlo, acepta las siguientes Cláusulas.</p>
              </div>

              <p className="legal-update-date">Última actualización: {new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })}</p>

              <div className="legal-clauses-grid">
                <div className="legal-clause">
                  <h4>1. Naturaleza del servicio (IA, no humano)</h4>
                  <p>Los AGENTES son sistemas automatizados de inteligencia artificial. Sus respuestas pueden ser inexactas, incompletas, descontextualizadas o erróneas.</p>
                </div>

                <div className="legal-clause">
                  <h4>2. No es asesoramiento profesional</h4>
                  <p>Las respuestas de los AGENTES son información/orientación general y no sustituyen asesoramiento profesional (médico, legal, financiero, psicológico, u otros). El USUARIO debe consultar a un profesional cualificado cuando corresponda.</p>
                </div>

                <div className="legal-clause">
                  <h4>3. Decisiones y responsabilidad del USUARIO</h4>
                  <p>Cualquier decisión, acción, omisión o actitud que el USUARIO adopte basándose en respuestas de los AGENTES se realiza bajo su exclusiva responsabilidad. El USUARIO se compromete a verificar la información antes de actuar, especialmente en temas sensibles.</p>
                </div>

                <div className="legal-clause">
                  <h4>4. Emergencias</h4>
                  <p>Los AGENTES no son un servicio de emergencias. Ante riesgo para la vida o integridad, contacte con el <strong>112</strong> u otros servicios/profesionales competentes.</p>
                </div>

                <div className="legal-clause">
                  <h4>5. Enlaces y terceros</h4>
                  <p>Los AGENTES pueden incluir referencias o enlaces a contenidos de terceros. No se garantiza su disponibilidad, exactitud o idoneidad. El uso de dichos recursos es responsabilidad del USUARIO.</p>
                </div>

                <div className="legal-clause">
                  <h4>6. Uso indebido</h4>
                  <p>Queda prohibido usar los AGENTES para fines ilícitos, dañinos, fraudulentos o que vulneren derechos de terceros. Se podrá limitar o suspender el acceso ante usos abusivos.</p>
                </div>

                <div className="legal-clause">
                  <h4>7. Limitación de responsabilidad</h4>
                  <p>En la medida máxima permitida por la normativa aplicable, la responsabilidad total derivada del uso o imposibilidad de uso de los AGENTES quedará limitada al importe efectivamente pagado por el USUARIO por el servicio en los últimos 30 días.</p>
                  <p>Para aclarar, consultar o reclamar cualquier cuestión relacionada con el servicio, el USUARIO deberá contactar en: <a href="mailto:obdulio@psicolfis.net">obdulio@psicolfis.net</a></p>
                </div>

                <div className="legal-clause">
                  <h4>8. Protección de datos y privacidad</h4>
                  <p>El USUARIO debe evitar introducir datos personales innecesarios, especialmente datos sensibles. El tratamiento de datos se rige por la Política de Privacidad publicada en el sitio.</p>
                </div>

                <div className="legal-clause">
                  <h4>9. Modificaciones</h4>
                  <p>Estas cláusulas pueden actualizarse. La versión vigente será la publicada en esta página. El uso continuado del servicio implica aceptación de la versión publicada.</p>
                </div>

                <div className="legal-clause">
                  <h4>10. Ley aplicable y jurisdicción</h4>
                  <p>Se aplica la legislación española. Salvo norma imperativa en contrario, las partes se someten a los juzgados y tribunales de <strong>ZAMORA (ESPAÑA)</strong>.</p>
                </div>
              </div>

              <p className="legal-final-date">Última actualización: {new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

