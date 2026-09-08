import { useState, useEffect } from "react";
import axios from "axios";
import { useParams } from "react-router-dom";
import { API, AGENT_STRIPE_URLS_FULL } from "../api";
import { usePageSeo } from "../lib/seo";

export const MiAgentePage = () => {
  const { token } = useParams();
  const [state, setState] = useState({ status: "loading", data: null, error: null });

  useEffect(() => {
    document.title = "Mi Agente · PSICOLFIS.NET";
    let cancelled = false;
    const validate = async () => {
      try {
        const { data } = await axios.get(`${API}/access/validate`, { params: { token } });
        if (!cancelled) setState({ status: "ok", data, error: null });
      } catch (e) {
        const msg = e?.response?.data?.detail || "No hemos podido validar tu enlace de acceso.";
        if (!cancelled) setState({ status: "error", data: null, error: msg });
      }
    };
    if (token) validate();
    else setState({ status: "error", data: null, error: "Falta el token de acceso." });
    return () => { cancelled = true; };
  }, [token]);

  // Una vez validado, inyectamos el script bundle.js de Pickaxe (idempotente).
  useEffect(() => {
    if (state.status !== "ok" || !state.data?.deployment_id) return;
    const SRC = "https://studio.pickaxe.co/api/embed/bundle.js";
    const existing = document.querySelector(`script[src="${SRC}"]`);
    if (existing) {
      // Ya estaba cargado; forzamos un re-render manual del bundle si expone API
      try { window?.Pickaxe?.refresh && window.Pickaxe.refresh(); } catch (_) {}
      return;
    }
    const s = document.createElement("script");
    s.src = SRC;
    s.defer = true;
    document.body.appendChild(s);
  }, [state]);

  return (
    <div className="mi-agente-page" data-testid="mi-agente-page">
      <header className="mi-agente-header">
        <a href="/" className="mi-agente-brand" data-testid="mi-agente-home-link">
          <span className="mi-agente-brand-mark">PSICOLFIS.NET</span>
          <span className="mi-agente-brand-sub">Universo</span>
        </a>
        {state.status === "ok" && state.data && (
          <div className="mi-agente-meta" data-testid="mi-agente-meta">
            <span className="mi-agente-agent-name">{state.data.agent_name}</span>
            <span className="mi-agente-level">
              {state.data.level === "full" ? "Acceso completo" : "Demo limitada"}
            </span>
          </div>
        )}
        <a
          href={`${API}/whatsapp`}
          target="_blank"
          rel="noopener noreferrer"
          className="mi-agente-help"
          data-testid="mi-agente-help"
        >
          ¿Necesitas ayuda?
        </a>
      </header>

      <main className="mi-agente-shell">
        {state.status === "loading" && (
          <div className="mi-agente-loading" data-testid="mi-agente-loading">
            <div className="spinner" />
            <p>Validando tu acceso al Universo PSICOLFIS.NET…</p>
          </div>
        )}

        {state.status === "error" && (
          <div className="mi-agente-error" data-testid="mi-agente-error">
            <h1>No podemos abrir tu agente</h1>
            <p>{state.error}</p>
            <p className="mi-agente-error-hint">
              Si crees que esto es un error o tu enlace ha caducado, escríbenos a{" "}
              <a href="mailto:obdulio@psicolfis.net">obdulio@psicolfis.net</a> y te enviamos un enlace nuevo en minutos.
            </p>
            <a href="/" className="btn-secondary" data-testid="mi-agente-back-home">
              Volver a la página principal
            </a>
          </div>
        )}

        {state.status === "ok" && state.data && (
          <div className="mi-agente-stage" data-testid="mi-agente-stage">
            <div
              id={`deployment-${state.data.deployment_id}`}
              data-testid="mi-agente-pickaxe-mount"
              className="mi-agente-pickaxe"
            />
          </div>
        )}
      </main>
    </div>
  );
};

// ====== /admin — back-office for Obdulio ======
