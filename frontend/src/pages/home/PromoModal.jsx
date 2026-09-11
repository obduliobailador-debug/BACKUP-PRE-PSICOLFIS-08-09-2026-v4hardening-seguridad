import { agents } from "../../data/agents";
import { useModalA11y } from "../../hooks/useModalA11y";

/**
 * Countdown pop-up shown on first visit with the 3 agents' cards.
 * All state (`showModal`, `timeLeft`, `loading`) is owned by Home.jsx.
 */
export const PromoModal = ({ show, onClose, timeLeft, formatTime, handlePurchase, loading }) => {
  const modalRef = useModalA11y({ isOpen: show, onClose });
  if (!show) return null;
  return (
    <div className="modal-overlay" data-testid="promo-modal">
      <div className="modal-content" ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="promo-modal-title" tabIndex={-1}>
        <button className="modal-close" onClick={onClose} aria-label="Cerrar">
          ✕
        </button>
        <div className="banner-header">
          <div className="clock-icon">⏰</div>
          <span className="banner-text">Tu tiempo es tu fortaleza</span>
          <div className="clock-icon">⏰</div>
        </div>

        <div className="modal-body">
          <div className="promo-content">
            <div className="promo-icon">🤖</div>
            <h2 className="promo-title" id="promo-modal-title">CONOCE NUESTROS AGENTES</h2>
            <div className="promo-icon">🤖</div>
          </div>
          <p className="promo-subtitle">Inteligencia artificial que piensa como tú</p>
          <p className="promo-description">
            Elige tu agente y empieza a multiplicar tu productividad hoy mismo.
          </p>

          <div className="countdown-timer">
            <div className="timer-circle">
              <span className="timer-number">{formatTime(timeLeft)}</span>
            </div>
          </div>

          <h2 className="agents-main-title">TU SABIDURÍA. NUESTRA IA.</h2>
          <div className="agents-grid">
            {agents.map((agent) => (
              <div key={agent.id} className="agent-card" data-testid={`agent-card-${agent.id}`}>
                <div className="agent-video-container">
                  <video className="agent-video" autoPlay muted loop playsInline>
                    <source src={agent.video} type="video/mp4" />
                  </video>
                  <div className="agent-overlay">
                    <h2 className="agent-name">{agent.name}</h2>
                  </div>
                </div>
                <p className="agent-description">{agent.description}</p>
                <div className="agent-price">{agent.price}</div>
                <div className="agent-offer-note" data-testid={`agent-offer-note-${agent.id}`}>
                  Elige el plan que prefieras
                </div>
                <div className="agent-actions">
                  <button
                    className="buy-button buy-demo"
                    onClick={() => handlePurchase(agent.id, "demo")}
                    disabled={loading[agent.id]}
                    data-testid={`buy-button-${agent.id}`}
                  >
                    {loading[agent.id] ? 'Procesando...' : 'Demo limitada'}
                  </button>
                  <button
                    className="buy-button buy-full"
                    onClick={() => handlePurchase(agent.id, "full")}
                    disabled={loading[agent.id]}
                    data-testid={`buy-full-button-${agent.id}`}
                  >
                    Acceso total
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button className="special-offers-btn" onClick={onClose}>
            🚀 Explorar la web →
          </button>
        </div>
      </div>
    </div>
  );
};
