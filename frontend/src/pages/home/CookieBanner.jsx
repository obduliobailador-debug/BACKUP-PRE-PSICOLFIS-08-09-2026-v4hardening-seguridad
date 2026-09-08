import { useEffect, useState } from "react";

/**
 * GDPR cookie banner. Reads/writes `cookiesAccepted` in localStorage so it
 * stays hidden after the first choice.
 */
export const CookieBanner = () => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const cookiesAccepted = localStorage.getItem('cookiesAccepted');
    if (!cookiesAccepted) setVisible(true);
  }, []);

  const accept = () => {
    localStorage.setItem('cookiesAccepted', 'true');
    setVisible(false);
  };

  const reject = () => {
    localStorage.setItem('cookiesAccepted', 'false');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="cookie-banner">
      <div className="cookie-content">
        <div className="cookie-text">
          <h4>🍪 Uso de Cookies</h4>
          <p>
            Utilizamos cookies para mejorar tu experiencia de navegación y analizar el uso de nuestro sitio web.
            Al continuar navegando, aceptas nuestra política de cookies.
          </p>
        </div>
        <div className="cookie-buttons">
          <button className="cookie-btn accept" onClick={accept}>
            ✅ Aceptar todas
          </button>
          <button className="cookie-btn reject" onClick={reject}>
            ❌ Rechazar
          </button>
          <a href="/legal#cookies" className="cookie-link">
            Más información
          </a>
        </div>
      </div>
    </div>
  );
};
