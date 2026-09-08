import { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { API } from "../api";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { usePageSeo } from "../lib/seo";
import { WhatsAppFAB } from "../components/WhatsAppFAB";
import { SECTOR_ICONS } from "../data/sectorIcons";

export const SolucionesIndexPage = () => {
  useScrollReveal();
  usePageSeo({
    title: "Soluciones por sector · PSICOLFIS.NET",
    description: "Agentes IA verticales para inmobiliarias, clínicas dentales y salones de belleza. Pruébalos en vivo y agenda una demo personalizada.",
    canonicalPath: "/soluciones",
  });

  const [sectors, setSectors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await axios.get(`${API}/sectors`);
        if (!cancelled) setSectors(data.items || []);
      } catch (e) {
        if (!cancelled) setSectors([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="soluciones-page" data-testid="soluciones-page">
      <header className="soluciones-header">
        <a href="/" className="soluciones-brand" data-testid="soluciones-home">
          <span>PSICOLFIS.NET</span>
          <small>Soluciones por sector</small>
        </a>
        <a href="/" className="soluciones-back">← Volver al inicio</a>
      </header>

      <main className="soluciones-main">
        <section className="soluciones-hero">
          <span className="sectors-eyebrow">Vertical · B2B</span>
          <h1>IA que entiende tu sector, no solo tu negocio</h1>
          <p>
            Cada agente está pensado para los retos reales de un vertical: cualificar visitas en una inmobiliaria,
            recuperar pacientes en una clínica dental o multiplicar reservas en un salón de belleza.
            Pruébalos en vivo y, si te encajan, agendamos una demo personalizada.
          </p>
        </section>

        {loading ? (
          <div className="soluciones-loading">Cargando soluciones…</div>
        ) : (
          <div className="soluciones-grid">
            {sectors.map((s) => (
              <a
                key={s.slug}
                href={`/soluciones/${s.slug}`}
                className="soluciones-card reveal reveal-up"
                data-testid={`soluciones-card-${s.slug}`}
              >
                <div className="soluciones-card-icon">{SECTOR_ICONS[s.slug] || null}</div>
                <h2>{s.name}</h2>
                <p>{s.tagline}</p>
                <ul>
                  {(s.metrics || []).map((m) => (
                    <li key={m.label}><strong>{m.value}</strong> · {m.label}</li>
                  ))}
                </ul>
                <span className="soluciones-card-cta">Ver solución →</span>
              </a>
            ))}
            <a
              href="/?demo=Tu%20sector"
              className="soluciones-card soluciones-card-wish"
              data-testid="soluciones-card-wish"
            >
              <div className="soluciones-card-icon" aria-hidden="true">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14"/></svg>
              </div>
              <h2>Estamos esperando tu sector</h2>
              <p>Dinos qué hace tu negocio y creamos un agente IA a medida para ti. Sin plantillas, sin esperas.</p>
              <span className="soluciones-card-cta">Proponer mi sector →</span>
            </a>
          </div>
        )}
      </main>

      <footer className="soluciones-footer">
        <p>
          ¿Tu sector no está aún? Escríbenos y diseñamos un agente vertical para tu caso.{" "}
          <a href="mailto:obdulio@psicolfis.net">obdulio@psicolfis.net</a>
        </p>
      </footer>
      <WhatsAppFAB text="Hola Obdulio, vengo desde la página de soluciones y me gustaría más información." />
    </div>
  );
};


const emptySector = () => ({
  slug: "", name: "", icon: "", tagline: "",
  headline: "", description: "", problem: "", solution: "",
  ideal_for: "", demo_intro: "",
  use_cases: [""],
  metrics: [{ label: "", value: "" }],
  deployment_id: "",
  hidden: false,
});

