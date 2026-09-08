/** Site-wide footer with brand + link columns. */
export const Footer = () => (
  <>
        <footer className="footer-section">
          <div className="footer-container">
            <div className="footer-content">
              <div className="footer-brand">
                <img
                  src="/images/legacy/psicolfisnet-con-nombre.png"
                  alt="Logo PSICOLFIS.NET"
                  className="footer-logo"
                  loading="lazy"
                  width="200"
                  height="80"
                />
                <p className="footer-description">
                  IA con propósito. Agentes que multiplican tu impacto.
                </p>
              </div>
              
              <div className="footer-links">
                <div className="footer-column">
                  <h4>Servicios</h4>
                  <ul>
                    <li><a href="#agentes">Super Agentes</a></li>
                    <li><a href="#caracteristicas">Características</a></li>
                    <li><a href="#como-funciona">Cómo Funciona</a></li>
                    <li><a href="#precios">Precios</a></li>
                  </ul>
                </div>
                
                <div className="footer-column">
                  <h4>Soporte</h4>
                  <ul>
                    <li><a href="#faq">FAQ</a></li>
                    <li><a href="mailto:obdulio@psicolfis.net">Contacto</a></li>
                    <li><a href="/legal">Aviso Legal</a></li>
                    <li><a href="/legal#privacidad">Política de Privacidad</a></li>
                  </ul>
                </div>
                
                <div className="footer-column">
                  <h4>Contacto</h4>
                  <ul>
                    <li>📧 obdulio@psicolfis.net</li>
                    <li>🌐 psicolfis.net</li>
                    <li>💼 Consultoría IA</li>
                  </ul>
                </div>
              </div>
            </div>
            
            <div className="footer-bottom">
              <p>&copy; {new Date().getFullYear()} PSICOLFIS.NET - Todos los derechos reservados</p>
              <div className="footer-legal">
                <a href="/legal">Aviso Legal</a>
                <span>•</span>
                <a href="/legal#privacidad">Privacidad</a>
                <span>•</span>
                <a href="/legal#cookies">Cookies</a>
              </div>
            </div>
          </div>
        </footer>
  </>
);
