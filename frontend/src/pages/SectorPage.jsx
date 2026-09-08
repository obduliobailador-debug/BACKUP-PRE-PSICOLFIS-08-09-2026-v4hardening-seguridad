import { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useParams } from "react-router-dom";
import { API } from "../api";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { usePageSeo, setJsonLd } from "../lib/seo";
import { WhatsAppFAB } from "../components/WhatsAppFAB";
import { SECTOR_ICONS } from "../data/sectorIcons";

const SECTOR_BUNDLED_PRODUCTS = {
  inmobiliarias: {
    name: "CRM Inmobiliario Premium",
    tagline: "El software de gestión que nuestros clientes inmobiliarios reciben incluido con su agente IA.",
    url: process.env.REACT_APP_CRM_DEMO_URL_INMOBILIARIAS || "",
    features: [
      "Panel ejecutivo con cartera activa, clientes, valor y comisiones estimadas.",
      "Gestión completa de inmuebles con estados: En venta · Reservado · Alquiler.",
      "Base de clientes segmentada (compradores, vendedores, inquilinos).",
      "Tips diarios, informes, agentes comerciales y cierre de visitas.",
    ],
    screenshots: [
      { src: "/images/crm/dashboard.jpg",   alt: "Panel principal del CRM inmobiliario con métricas de cartera, clientes y comisiones" },
      { src: "/images/crm/properties.jpg",  alt: "Listado de inmuebles del CRM con fotos, precios y estados" },
      { src: "/images/crm/clients.jpg",     alt: "Clientes recientes del CRM segmentados por tipo" },
    ],
    disclaimer: "Demo pública con datos ficticios · El entorno es de prueba y puede estar temporalmente offline.",
  },
};

const SectorBundledProduct = ({ slug, sectorName }) => {
  const product = SECTOR_BUNDLED_PRODUCTS[slug];
  const [imgFailed, setImgFailed] = useState({});
  const [probe, setProbe] = useState({ checked: false, online: true });

  // Lightweight availability check: open a HEAD request via an image beacon.
  // We use the favicon so we don't depend on the CRM allowing CORS.
  useEffect(() => {
    if (!product?.url) return;
    let done = false;
    const img = new window.Image();
    const timer = setTimeout(() => {
      if (!done) { done = true; setProbe({ checked: true, online: false }); }
    }, 6000);
    try {
      const u = new URL(product.url);
      img.onload = () => { if (!done) { done = true; clearTimeout(timer); setProbe({ checked: true, online: true }); } };
      img.onerror = () => { if (!done) { done = true; clearTimeout(timer); setProbe({ checked: true, online: false }); } };
      img.src = `${u.origin}/favicon.ico?t=${Date.now()}`;
    } catch (e) {
      setProbe({ checked: true, online: false });
    }
    return () => { clearTimeout(timer); done = true; };
  }, [product?.url]);

  if (!product || !product.url) return null;

  const handleOpen = () => {
    window.open(product.url, "_blank", "noopener,noreferrer");
  };

  const handleNotify = () => {
    const subject = encodeURIComponent(`CRM ${sectorName || ""} ha sido reportado como offline`);
    const body = encodeURIComponent(
      `Hola Obdulio,\n\nUn visitante ha intentado acceder al CRM de demo y no ha respondido.\n\nURL: ${product.url}\nFecha: ${new Date().toLocaleString("es-ES")}`
    );
    window.location.href = `mailto:obdulio@psicolfis.net?subject=${subject}&body=${body}`;
  };

  return (
    <section className="sector-bundled reveal" data-testid={`sector-bundled-${slug}`}>
      <div className="sector-bundled-head">
        <span className="sectors-eyebrow">Producto incluido</span>
        <h2>{product.name}</h2>
        <p>{product.tagline}</p>
      </div>

      <div className="sector-bundled-grid">
        <div className="sector-bundled-gallery">
          {product.screenshots.map((sh, idx) => (
            <div key={sh.src} className="sector-bundled-shot" data-testid={`crm-shot-${idx}`}>
              {imgFailed[idx] ? (
                <div className="sector-bundled-shot-fallback">
                  <span>{idx === 0 ? "Panel principal" : idx === 1 ? "Inmuebles" : "Clientes"}</span>
                </div>
              ) : (
                <img
                  src={sh.src}
                  alt={sh.alt}
                  loading="lazy"
                  onError={() => setImgFailed((s) => ({ ...s, [idx]: true }))}
                />
              )}
            </div>
          ))}
        </div>

        <div className="sector-bundled-body">
          <ul>
            {product.features.map((f, i) => (
              <li key={i}>
                <span className="sector-check" aria-hidden="true">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                </span>
                {f}
              </li>
            ))}
          </ul>

          {probe.checked && !probe.online ? (
            <div className="sector-bundled-offline" data-testid="crm-offline">
              <strong>La demo en vivo no responde ahora mismo.</strong>
              <p>Estamos en un entorno de prueba y a veces se pone a dormir. Puedes intentar abrirlo igualmente — si sigue caído, escríbenos y te enviamos una demo guiada en 5 minutos.</p>
              <div className="sector-bundled-actions">
                <button className="hero-btn primary" onClick={handleOpen} data-testid="crm-try-anyway">
                  Intentar abrir igualmente →
                </button>
                <button className="hero-btn secondary" onClick={handleNotify} data-testid="crm-notify">
                  Avisarnos del fallo
                </button>
              </div>
            </div>
          ) : (
            <div className="sector-bundled-actions">
              <button
                className="hero-btn primary"
                onClick={handleOpen}
                data-testid="crm-open-live"
              >
                Probar el CRM en vivo →
              </button>
              <span className="sector-bundled-note">
                Se abre en pestaña nueva · No pierdes esta página
              </span>
            </div>
          )}

          <p className="sector-bundled-disclaimer">{product.disclaimer}</p>
        </div>
      </div>
    </section>
  );
};



export const SectorPage = () => {
  const { slug } = useParams();
  useScrollReveal();
  const [state, setState] = useState({ status: "loading", data: null, error: null });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await axios.get(`${API}/sectors/${slug}`);
        if (!cancelled) setState({ status: "ok", data, error: null });
      } catch (e) {
        const msg = e?.response?.data?.detail || "No hemos podido cargar este sector.";
        if (!cancelled) setState({ status: "error", data: null, error: msg });
      }
    })();
    return () => { cancelled = true; };
  }, [slug]);

  usePageSeo({
    title: state.data
      ? `${state.data.name} · IA por sector · PSICOLFIS.NET`
      : "Sector · PSICOLFIS.NET",
    description: state.data?.description || "Agente IA vertical de PSICOLFIS.NET.",
    canonicalPath: `/soluciones/${slug || ""}`,
  });

  // Inject JSON-LD Service schema for rich snippets
  useEffect(() => {
    if (state.status !== "ok" || !state.data) return;
    const baseUrl = process.env.REACT_APP_PUBLIC_BASE_URL || "https://psicolfis.net";
    setJsonLd(`ld-service-${state.data.slug}`, {
      "@context": "https://schema.org",
      "@type": "Service",
      "serviceType": `Agente IA para ${state.data.name}`,
      "name": state.data.headline,
      "description": state.data.description,
      "provider": {
        "@type": "Organization",
        "name": "PSICOLFIS.NET",
        "url": baseUrl,
      },
      "areaServed": { "@type": "Country", "name": "España" },
      "audience": { "@type": "Audience", "audienceType": state.data.ideal_for },
      "url": `${baseUrl}/soluciones/${state.data.slug}`,
      "hasOfferCatalog": {
        "@type": "OfferCatalog",
        "name": `Casos de uso · ${state.data.name}`,
        "itemListElement": (state.data.use_cases || []).map((uc, i) => ({
          "@type": "Offer",
          "position": i + 1,
          "itemOffered": { "@type": "Service", "name": uc },
        })),
      },
    });
    return () => {
      const el = document.getElementById(`ld-service-${state.data.slug}`);
      if (el) el.remove();
    };
  }, [state]);

  // Inject Pickaxe bundle once we have a deployment_id
  useEffect(() => {
    if (state.status !== "ok" || !state.data?.deployment_id) return;
    const SRC = "https://studio.pickaxe.co/api/embed/bundle.js";
    const existing = document.querySelector(`script[src="${SRC}"]`);
    if (existing) {
      try { window?.Pickaxe?.refresh && window.Pickaxe.refresh(); } catch (_) {}
      return;
    }
    const s = document.createElement("script");
    s.src = SRC;
    s.defer = true;
    document.body.appendChild(s);
  }, [state]);

  const whatsappUrlFor = (sectorName) => {
    const text = encodeURIComponent(
      `Hola Obdulio, vengo desde la página de soluciones para ${sectorName} y me gustaría una demo personalizada.`
    );
    return `${API}/whatsapp?text=${text}`;
  };

  const openBudget = (sectorName) => {
    // Navigate home and ask Home to pre-open the budget form via query param.
    window.location.href = `/?demo=${encodeURIComponent(sectorName)}#contacto`;
  };

  if (state.status === "loading") {
    return (
      <div className="sector-page" data-testid="sector-page-loading">
        <div className="soluciones-loading">Cargando…</div>
      </div>
    );
  }
  if (state.status === "error") {
    return (
      <div className="sector-page" data-testid="sector-page-error">
        <div className="soluciones-loading">
          <h2>{state.error}</h2>
          <a href="/soluciones" className="hero-btn primary">Ver todas las soluciones</a>
        </div>
      </div>
    );
  }

  const s = state.data;
  return (
    <div className="sector-page" data-testid={`sector-page-${s.slug}`}>
      <header className="soluciones-header">
        <a href="/" className="soluciones-brand">
          <span>PSICOLFIS.NET</span>
          <small>· {s.name}</small>
        </a>
        <a href="/soluciones" className="soluciones-back">← Todas las soluciones</a>
      </header>

      <main className="sector-main">
        {/* Hero */}
        <section className="sector-hero">
          <div className="sector-hero-icon">{SECTOR_ICONS[s.slug] || null}</div>
          <span className="sectors-eyebrow">{s.name}</span>
          <h1 data-testid="sector-headline">{s.headline}</h1>
          <p>{s.description}</p>
          <div className="sector-hero-cta">
            <button
              className="hero-btn primary"
              onClick={() => openBudget(s.name)}
              data-testid="sector-cta-demo"
            >
              Solicitar demo personalizada
            </button>
            <a
              href={whatsappUrlFor(s.name)}
              target="_blank"
              rel="noopener noreferrer"
              className="hero-btn secondary"
              data-testid="sector-cta-whatsapp"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" style={{marginRight:6,verticalAlign:"middle"}}><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.198-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.247-.694.247-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0 0 20.464 3.488"/></svg>
              WhatsApp directo
            </a>
          </div>
          <p className="sector-ideal-for"><strong>Ideal para:</strong> {s.ideal_for}</p>
        </section>

        {/* Metrics */}
        <section className="sector-metrics">
          {(s.metrics || []).map((m) => (
            <div key={m.label} className="sector-metric reveal reveal-up">
              <div className="sector-metric-value">{m.value}</div>
              <div className="sector-metric-label">{m.label}</div>
            </div>
          ))}
        </section>

        {/* Problem / Solution */}
        <section className="sector-twoblocks">
          <div className="sector-block sector-block-problem reveal reveal-up">
            <h3>El problema</h3>
            <p>{s.problem}</p>
          </div>
          <div className="sector-block sector-block-solution reveal reveal-up">
            <h3>La solución PSICOLFIS</h3>
            <p>{s.solution}</p>
          </div>
        </section>

        {/* Use cases */}
        <section className="sector-usecases reveal">
          <h2>Lo que el agente hace por ti</h2>
          <ul>
            {(s.use_cases || []).map((uc, i) => (
              <li key={i} data-testid={`sector-usecase-${i}`}>
                <span className="sector-check" aria-hidden="true">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                </span>
                {uc}
              </li>
            ))}
          </ul>
        </section>

        {/* Bundled product (e.g. CRM for inmobiliarias) */}
        <SectorBundledProduct slug={s.slug} sectorName={s.name} />

        {/* Live demo */}
        <section className="sector-demo reveal" data-testid="sector-demo-section">
          <div className="sector-demo-head">
            <span className="sectors-eyebrow">Demo en vivo</span>
            <h2>Pruébalo como si fueras tu cliente</h2>
            <p>{s.demo_intro}</p>
          </div>
          {s.deployment_id ? (
            <div className="sector-demo-stage">
              <div
                id={`deployment-${s.deployment_id}`}
                data-testid="sector-pickaxe-mount"
                className="sector-pickaxe"
              />
            </div>
          ) : (
            <div className="sector-demo-placeholder" data-testid="sector-demo-placeholder">
              <h3>Demo próximamente</h3>
              <p>Estamos terminando los últimos ajustes del agente para {s.name.toLowerCase()}. Mientras tanto, agenda una demo personalizada y te lo enseñamos en directo.</p>
              <button className="hero-btn primary" onClick={() => openBudget(s.name)} data-testid="sector-placeholder-cta">
                Solicitar demo personalizada
              </button>
            </div>
          )}
        </section>

        {/* Final CTA */}
        <section className="sector-final-cta reveal">
          <h2>¿Listo para que tu {s.name.toLowerCase()} trabaje sola?</h2>
          <p>En una llamada de 20 minutos te enseñamos cómo encajaría en tu día a día.</p>
          <div className="sector-hero-cta">
            <button
              className="hero-btn primary"
              onClick={() => openBudget(s.name)}
              data-testid="sector-final-cta-demo"
            >
              Solicitar demo personalizada
            </button>
            <a
              href={whatsappUrlFor(s.name)}
              target="_blank"
              rel="noopener noreferrer"
              className="hero-btn secondary"
              data-testid="sector-final-cta-whatsapp"
            >
              Hablar por WhatsApp
            </a>
          </div>
        </section>
      </main>

      <footer className="soluciones-footer">
        <p>
          ¿Otro sector? Escribe a <a href="mailto:obdulio@psicolfis.net">obdulio@psicolfis.net</a>.
        </p>
      </footer>
      <WhatsAppFAB text={`Hola Obdulio, vengo desde la página de ${s.name} y quiero una demo personalizada.`} />
    </div>
  );
};



