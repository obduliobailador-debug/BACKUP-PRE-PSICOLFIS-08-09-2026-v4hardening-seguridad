import { useEffect, useRef, useState } from "react";
import { Menu, X } from "lucide-react";

const LINKS = [
  { href: "#caracteristicas", label: "Características" },
  { href: "#agentes", label: "Super Agentes" },
  { href: "/soluciones", label: "Soluciones", testid: "nav-soluciones" },
  { href: "#como-funciona", label: "Cómo Funciona" },
  { href: "#precios", label: "Precios" },
  { href: "#resenas", label: "Reseñas" },
  { href: "#faq", label: "FAQ" },
];

/**
 * Top navigation with in-page anchors + primary CTAs.
 * On <=768px it collapses into an accessible hamburger dropdown panel
 * (aria-expanded/aria-controls, Escape to close, focus return).
 * `openBudgetForm` opens the shared budget modal owned by Home.jsx.
 */
export const Navbar = ({ openBudgetForm }) => {
  const [open, setOpen] = useState(false);
  const toggleRef = useRef(null);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 769px)");
    const onChange = (e) => {
      if (e.matches) setOpen(false);
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") {
        setOpen(false);
        if (toggleRef.current) toggleRef.current.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <nav className="navbar" aria-label="Principal">
      <div className="navbar-container">
        <button
          ref={toggleRef}
          type="button"
          className="nav-toggle"
          aria-label={open ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={open}
          aria-controls="primary-navigation"
          onClick={() => setOpen((v) => !v)}
          data-testid="nav-toggle-btn"
        >
          {open ? <X size={24} aria-hidden="true" /> : <Menu size={24} aria-hidden="true" />}
        </button>

        <ul
          id="primary-navigation"
          className={`nav-menu ${open ? "open" : ""}`}
          data-testid="primary-navigation"
        >
          {LINKS.map((l) => (
            <li key={l.href}>
              <a
                href={l.href}
                onClick={() => setOpen(false)}
                {...(l.testid ? { "data-testid": l.testid } : {})}
              >
                {l.label}
              </a>
            </li>
          ))}
        </ul>

        <div className="nav-actions">
          <button
            className="cta-button"
            onClick={() => (window.location.href = "/agentes")}
            data-testid="nav-empezar-btn"
          >
            Empezar Ahora
          </button>
          <button
            className="contact-cta-button"
            onClick={() => openBudgetForm("Consulta general")}
            data-testid="nav-contact-btn"
          >
            Ponte en contacto
          </button>
        </div>
      </div>
    </nav>
  );
};
