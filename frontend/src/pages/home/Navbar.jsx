/**
 * Top navigation with in-page anchors + primary CTAs.
 * `openBudgetForm` opens the shared budget modal owned by Home.jsx.
 */
export const Navbar = ({ openBudgetForm }) => (
  <>
        {/* Navbar */}
        <nav className="navbar">
          <div className="navbar-container">
            <ul className="nav-menu">
              <li><a href="#caracteristicas">Características</a></li>
              <li><a href="#agentes">Super Agentes</a></li>
              <li><a href="/soluciones" data-testid="nav-soluciones">Soluciones</a></li>
              <li><a href="#como-funciona">Cómo Funciona</a></li>
              <li><a href="#precios">Precios</a></li>
              <li><a href="#resenas">Reseñas</a></li>
              <li><a href="#faq">FAQ</a></li>
            </ul>
            <div className="nav-actions">
              <button
                className="cta-button"
                onClick={() => window.location.href = '/agentes'}
                data-testid="nav-empezar-btn"
              >
                Empezar Ahora
              </button>
              <button
                className="contact-cta-button"
                onClick={() => openBudgetForm('Consulta general')}
                data-testid="nav-contact-btn"
              >
                Ponte en contacto
              </button>
            </div>
          </div>
        </nav>
  </>
);
