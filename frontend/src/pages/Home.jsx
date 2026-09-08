import { useState, useEffect } from "react";
import axios from "axios";
import { API, AGENT_STRIPE_URLS, AGENT_STRIPE_URLS_FULL } from "../api";
import { agents } from "../data/agents";
import { faqData } from "../data/faq";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { usePageSeo, setJsonLd } from "../lib/seo";
import { WhatsAppFAB } from "../components/WhatsAppFAB";

export const Home = () => {
  useScrollReveal();
  usePageSeo({
    title: 'PSICOLFIS.NET · Agentes de IA personalizados para tu negocio',
    description: 'Agentes de IA creados a medida para autónomos y pequeños negocios. Automatiza atención, contenido y ventas con IRIS, ALEX y UMBRAL. Resultados en 5-10 días.',
    canonicalPath: '/',
  });
  const [showModal, setShowModal] = useState(true); // Popup activado
  const [timeLeft, setTimeLeft] = useState(15);
  const [loading, setLoading] = useState({});
  const [expandedFaq, setExpandedFaq] = useState(null);
  const [showCookieBanner, setShowCookieBanner] = useState(true);

  useEffect(() => {
    if (timeLeft > 0 && showModal) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0) {
      setShowModal(false);
    }
  }, [timeLeft, showModal]);

  useEffect(() => {
    const cookiesAccepted = localStorage.getItem('cookiesAccepted');
    if (cookiesAccepted === 'true') {
      setShowCookieBanner(false);
    }
  }, []);

  const formatTime = (seconds) => {
    return `00:${seconds.toString().padStart(2, '0')}`;
  };

  const acceptCookies = () => {
    localStorage.setItem('cookiesAccepted', 'true');
    setShowCookieBanner(false);
  };

  const rejectCookies = () => {
    localStorage.setItem('cookiesAccepted', 'false');
    setShowCookieBanner(false);
  };

  // ----- Reviews state -----
  const [reviews, setReviews] = useState([]);
  const [reviewsStats, setReviewsStats] = useState({ count: 0, average: 0 });
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewForm, setReviewForm] = useState({
    author: '', role: '', rating: 5, text: '', captcha_answer: '', website: ''
  });
  const [reviewCaptcha, setReviewCaptcha] = useState({ question: '', token: '' });
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewSubmitted, setReviewSubmitted] = useState(false);
  const [reviewError, setReviewError] = useState('');

  // Fetch reviews on mount
  useEffect(() => {
    axios.get(`${API}/reviews`)
      .then(({ data }) => {
        setReviews(data.reviews || []);
        setReviewsStats({ count: data.count || 0, average: data.average || 0 });
      })
      .catch((err) => console.error('No se pudieron cargar las reseñas:', err));
  }, []);

  // Inject AggregateRating JSON-LD dynamically when we have reviews
  useEffect(() => {
    const id = 'jsonld-aggregate-rating';
    let tag = document.getElementById(id);
    if (reviewsStats.count > 0) {
      const data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "PSICOLFIS.NET",
        "url": "https://psicolfis.net/",
        "aggregateRating": {
          "@type": "AggregateRating",
          "ratingValue": String(reviewsStats.average),
          "reviewCount": String(reviewsStats.count),
          "bestRating": "5",
          "worstRating": "1"
        },
        "review": reviews.slice(0, 5).map(r => ({
          "@type": "Review",
          "author": { "@type": "Person", "name": r.author },
          "reviewRating": {
            "@type": "Rating",
            "ratingValue": String(r.rating),
            "bestRating": "5"
          },
          "reviewBody": r.text,
          "datePublished": (r.created_at || '').split('T')[0]
        }))
      };
      if (!tag) {
        tag = document.createElement('script');
        tag.id = id;
        tag.type = 'application/ld+json';
        document.head.appendChild(tag);
      }
      tag.textContent = JSON.stringify(data);
    } else if (tag) {
      tag.remove();
    }
  }, [reviews, reviewsStats]);

  const fetchReviewCaptcha = async () => {
    try {
      const { data } = await axios.get(`${API}/captcha`);
      setReviewCaptcha({ question: data.question, token: data.token });
    } catch (err) {
      console.error('No se pudo cargar captcha de reseña', err);
    }
  };

  const openReviewForm = () => {
    setReviewForm({ author: '', role: '', rating: 5, text: '', captcha_answer: '', website: '' });
    setReviewError('');
    setReviewSubmitted(false);
    setShowReviewForm(true);
    fetchReviewCaptcha();
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    setReviewSubmitting(true);
    setReviewError('');
    try {
      const { data } = await axios.post(`${API}/reviews`, {
        ...reviewForm,
        captcha_token: reviewCaptcha.token,
      });
      setReviewSubmitted(true);
      // Prepend the new review locally
      setReviews(prev => [data.review, ...prev]);
      setReviewsStats(prev => {
        const newCount = prev.count + 1;
        const newAvg = ((prev.average * prev.count) + reviewForm.rating) / newCount;
        return { count: newCount, average: Math.round(newAvg * 100) / 100 };
      });
      setTimeout(() => {
        setShowReviewForm(false);
        setReviewSubmitted(false);
      }, 3000);
    } catch (err) {
      setReviewError(err?.response?.data?.detail || 'No se pudo enviar tu reseña. Inténtalo de nuevo.');
      setReviewForm(prev => ({ ...prev, captcha_answer: '' }));
      fetchReviewCaptcha();
    } finally {
      setReviewSubmitting(false);
    }
  };

  // Estado para el formulario de presupuesto
  const [showBudgetForm, setShowBudgetForm] = useState(false);
  const [budgetForm, setBudgetForm] = useState({
    nombre: '',
    email: '',
    telefono: '',
    plan: '',
    agente: '',
    mensaje: '',
    captcha_answer: '',
    website: '' // honeypot (invisible)
  });
  const [captcha, setCaptcha] = useState({ question: '', token: '' });
  const [captchaLoading, setCaptchaLoading] = useState(false);
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const resetBudgetForm = () => {
    setBudgetForm({
      nombre: '', email: '', telefono: '', plan: '',
      agente: '', mensaje: '', captcha_answer: '', website: ''
    });
  };

  const fetchCaptcha = async () => {
    setCaptchaLoading(true);
    try {
      const { data } = await axios.get(`${API}/captcha`);
      setCaptcha({ question: data.question, token: data.token });
    } catch (err) {
      console.error('No se pudo cargar el captcha:', err);
      setCaptcha({ question: '', token: '' });
    } finally {
      setCaptchaLoading(false);
    }
  };

  const handleBudgetSubmit = async (e) => {
    e.preventDefault();
    setFormSubmitting(true);
    setFormError('');
    try {
      await axios.post(`${API}/contact/budget`, {
        ...budgetForm,
        captcha_token: captcha.token,
      });
      setFormSubmitted(true);
      setTimeout(() => {
        setShowBudgetForm(false);
        setFormSubmitted(false);
        resetBudgetForm();
      }, 3500);
    } catch (error) {
      console.error('Error enviando solicitud:', error);
      setFormError(
        error?.response?.data?.detail ||
        'No se pudo enviar la solicitud. Inténtalo de nuevo en unos minutos.'
      );
      // Always refresh captcha after a failed submit so the user has a fresh challenge
      setBudgetForm(prev => ({ ...prev, captcha_answer: '' }));
      fetchCaptcha();
    } finally {
      setFormSubmitting(false);
    }
  };

  const openBudgetForm = (planName) => {
    setBudgetForm(prev => ({
      ...prev,
      plan: planName,
      captcha_answer: '',
      website: ''
    }));
    setFormError('');
    setShowBudgetForm(true);
    fetchCaptcha();
  };

  // If user lands on Home with ?demo=<sector>, auto-open the budget form
  // pre-filled so they can request a personalized demo for that sector.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const demo = params.get('demo');
    if (demo) {
      const planLabel = `Demo personalizada · ${demo}`;
      setBudgetForm(prev => ({
        ...prev,
        plan: planLabel,
        agente: '',
        mensaje: prev.mensaje || `Me gustaría una demo personalizada del agente IA para ${demo}.`,
        captcha_answer: '',
        website: ''
      }));
      setFormError('');
      setShowBudgetForm(true);
      fetchCaptcha();
      // Clean the query param so reloading the page doesn't reopen the form
      const url = new URL(window.location.href);
      url.searchParams.delete('demo');
      window.history.replaceState({}, '', url.toString());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handlePurchase = (agentId, level = "demo") => {
    const map = level === "full" ? AGENT_STRIPE_URLS_FULL : AGENT_STRIPE_URLS;
    const url = map[agentId];
    if (url) {
      window.location.href = url;
    } else {
      alert('Enlace de pago no disponible para este agente.');
    }
  };

  return (
    <div className="app-container">
      {/* Modal/Popup Banner */}
      {showModal && (
        <div className="modal-overlay" data-testid="promo-modal">
          <div className="modal-content">
            <button className="modal-close" onClick={() => setShowModal(false)} aria-label="Cerrar">
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
                <h1 className="promo-title">CONOCE NUESTROS AGENTES</h1>
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
                      <video 
                        className="agent-video"
                        autoPlay
                        muted
                        loop
                        playsInline
                      >
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

              <button className="special-offers-btn" onClick={() => setShowModal(false)}>
                🚀 Explorar la web →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Page Content - Always rendered below modal */}
      <div className="main-page">
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

        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-content">
            <div className="hero-logo-box">
              <img
                src="/images/legacy/psicolfisnet-con-nombre.png"
                alt="Logo PSICOLFIS.NET - Agentes de IA personalizados"
                className="hero-logo"
                width="360"
                height="150"
                fetchPriority="high"
              />
            </div>
            
            <h1 className="hero-title">
              IA con Propósito<br/>
              <span className="hero-highlight">Agentes que Multiplican</span><br/>
              tu Impacto
            </h1>
            
            <p className="hero-subtitle">
              Inteligencias artificiales que piensan como tú, trabajan contigo y liberan<br/>
              tu tiempo.
            </p>
            
            <p className="hero-description">
              No vendemos tecnología: creamos sistemas que te representan y generan<br/>
              resultados reales.
            </p>

            <div className="hero-watermark">PSICOLFIS.NET</div>

            <div className="hero-buttons">
              <button className="hero-btn primary" onClick={() => document.getElementById('agentes').scrollIntoView({behavior: 'smooth'})}>
                🤖 Descubre los Super Agentes →
              </button>
              <button className="hero-btn secondary" onClick={() => document.getElementById('precios').scrollIntoView({behavior: 'smooth'})}>
                💰 Ver Precios →
              </button>
            </div>

            <p className="hero-footer">
              ✨ Autónomos y pequeños negocios • Implementación práctica • Resultados medibles
            </p>

            <button className="scroll-down" onClick={() => window.scrollTo({top: window.innerHeight, behavior: 'smooth'})}>
              Descubre más ↓
            </button>
          </div>
        </section>

        {/* Transformation Section */}
        <section id="caracteristicas" className="transformation-section">
          <div className="section-container">
            <h2 className="section-title reveal">
              La Transformación es <span className="text-blue">Real</span>
            </h2>
            <p className="section-subtitle reveal">Tu conocimiento convertido en una herramienta que trabaja por ti, 24/7</p>
            
            <div className="transformation-image-large reveal">
              <img
                src="/images/legacy/antes-y-despues.jpeg"
                alt="Comparativa antes y después: de tareas manuales a automatización con agentes de IA"
                loading="lazy"
                width="1200"
                height="600"
              />
            </div>
            
            <div className="transformation-comparison">
              <div className="comparison-card before reveal reveal-left">
                <h3>❌ Antes (Sin IA)</h3>
                <ul>
                  <li>• Tareas repetitivas consumen tu día</li>
                  <li>• Respuestas manuales a cada cliente</li>
                  <li>• Creación de contenido lenta</li>
                  <li>• Sin tiempo para estrategia</li>
                  <li>• Sobrecarga de trabajo constante</li>
                </ul>
              </div>
              
              <div className="comparison-card after reveal reveal-right">
                <h3>✅ Después (Con IA)</h3>
                <ul>
                  <li>✓ Automatización inteligente 24/7</li>
                  <li>✓ Respuestas instantáneas con tu tono</li>
                  <li>✓ Contenido generado en minutos</li>
                  <li>✓ Tiempo libre para crecer tu negocio</li>
                  <li>✓ Productividad multiplicada x10</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Video Section */}
        <section className="video-section">
          <div className="section-container">
            <h2 className="section-title">
              ¿Por qué Necesitas un <span className="text-blue">Super Agente</span>?
            </h2>
            <p className="section-subtitle">Mira cómo nuestros agentes transforman negocios en solo 12 segundos</p>
            
            <div className="video-container">
              {/* YouTube como principal */}
              <iframe
                className="promo-video-youtube"
                src="https://www.youtube.com/embed/v4cSwxZd64U?rel=0"
                title="Agentes de IA - PSICOLFIS"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
              ></iframe>
              {/* Video local como respaldo (oculto) */}
              <video 
                className="promo-video-backup"
                controls
                playsInline
                preload="none"
                poster="/images/legacy/psicolfisnet-con-nombre.png"
                style={{display: 'none'}}
              >
                <source src="/videos/agentes_ia.mp4" type="video/mp4" />
              </video>
            </div>

            <p className="video-cta-text">Descubre cómo multiplicar tu productividad</p>

            <div className="benefits-grid">
              <div className="benefit-card reveal reveal-up">
                <div className="benefit-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <h4>Ahorra 10+ horas/semana</h4>
                <p>Recupera tiempo valioso automatizando tareas repetitivas</p>
              </div>
              <div className="benefit-card reveal reveal-up" style={{transitionDelay: '120ms'}}>
                <div className="benefit-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="1" x2="12" y2="23"></line>
                    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                  </svg>
                </div>
                <h4>Aumenta tus ingresos</h4>
                <p>Responde más rápido y cierra más ventas</p>
              </div>
              <div className="benefit-card reveal reveal-up" style={{transitionDelay: '240ms'}}>
                <div className="benefit-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                  </svg>
                </div>
                <h4>Escala tu negocio</h4>
                <p>Crece sin necesidad de contratar más personal</p>
              </div>
            </div>
          </div>
        </section>

        {/* Why Choose Us Section */}
        <section className="why-section">
          <div className="section-container">
            <h2 className="section-title">
              Por Qué <span className="text-blue">Elegirnos</span>
            </h2>
            <p className="section-subtitle">No somos solo otra herramienta de IA. Somos tu socio estratégico en la transformación digital.</p>
            
            <div className="features-grid-four">
              <div className="feature-card-clean reveal reveal-up">
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                  </svg>
                </div>
                <h3>IA con Alma</h3>
                <p>Cada agente respeta tu voz, tus valores y tu forma de decidir. No son robots genéricos, son extensiones de tu negocio.</p>
              </div>
              
              <div className="feature-card-clean reveal reveal-up" style={{transitionDelay: '100ms'}}>
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </div>
                <h3>Acompañamiento Real</h3>
                <p>Implementación más guía práctica. No te dejamos solo con la herramienta, te acompañamos en cada paso.</p>
              </div>
              
              <div className="feature-card-clean reveal reveal-up" style={{transitionDelay: '200ms'}}>
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                  </svg>
                </div>
                <h3>Resultados Medibles</h3>
                <p>Productividad, presencia e ingresos. Nos enfocamos en lo que realmente mueve la aguja de tu negocio.</p>
              </div>
              
              <div className="feature-card-clean reveal reveal-up" style={{transitionDelay: '300ms'}}>
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <circle cx="12" cy="12" r="6"></circle>
                    <circle cx="12" cy="12" r="2"></circle>
                  </svg>
                </div>
                <h3>Experiencia Transversal</h3>
                <p>Marketing, coaching, asesoría y tecnología. Un enfoque integrado que entiende todos los aspectos de tu negocio.</p>
              </div>
            </div>

            <div className="feature-highlight-clean">
              <h3>Tu Conocimiento, Convertido en una Herramienta que Trabaja por Ti (24/7)</h3>
              <p>Creamos asistentes inteligentes diseñados a tu medida. Cada proyecto captura tu tono, tus valores y tu forma de tomar decisiones. El resultado: una extensión de tu mente y tu negocio que reduce tareas repetitivas, mejora tu comunicación y te devuelve horas al día.</p>
            </div>
          </div>
        </section>

        {/* Super Agents Section */}
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

        {/* Soluciones por sector — featured section */}
        <section id="soluciones" className="sectors-section">
          <div className="section-container">
            <div className="sectors-head reveal">
              <span className="sectors-eyebrow">Nuevo · Soluciones por sector</span>
              <h2 className="section-title">
                IA que <span className="text-blue">habla el idioma</span> de tu negocio
              </h2>
              <p className="section-subtitle">
                Más allá de los agentes genéricos, diseñamos sistemas verticales para sectores específicos.
                Pruébalos en vivo y agenda una demo si te encajan.
              </p>
            </div>

            <div className="sectors-grid">
              <a className="sector-card reveal reveal-up" href="/soluciones/inmobiliarias" data-testid="home-sector-inmobiliarias">
                <div className="sector-icon" aria-hidden="true">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                </div>
                <h3>Inmobiliarias</h3>
                <p>Cualifica leads y agenda visitas mientras atiendes a tus clientes actuales.</p>
                <span className="sector-link">Ver solución →</span>
              </a>

              <a className="sector-card reveal reveal-up" href="/soluciones/clinicas-dentales" data-testid="home-sector-dental">
                <div className="sector-icon" aria-hidden="true">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5.5c1-1 2.5-2 4.5-2C19 3.5 21 5 21 8.5c0 4-3 7.5-4 11.5-.5 2-1.5 2-2 0-.5-2-1-4-2-4s-1.5 2-2 4c-.5 2-1.5 2-2 0-1-4-4-7.5-4-11.5C5 5 7 3.5 9.5 3.5c2 0 3.5 1 4.5 2"/></svg>
                </div>
                <h3>Clínicas dentales</h3>
                <p>Reduce cancelaciones, recupera pacientes inactivos y libera la recepción.</p>
                <span className="sector-link">Ver solución →</span>
              </a>

              <a className="sector-card reveal reveal-up" href="/soluciones/salones-belleza" data-testid="home-sector-beauty">
                <div className="sector-icon" aria-hidden="true">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/></svg>
                </div>
                <h3>Salones de belleza</h3>
                <p>Reservas 24/7 por WhatsApp, upsell automático y clientas que vuelven solas.</p>
                <span className="sector-link">Ver solución →</span>
              </a>

              <a className="sector-card sector-card-wish reveal reveal-up" href="/?demo=Tu%20sector" data-testid="home-sector-wish">
                <div className="sector-icon" aria-hidden="true">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14"/></svg>
                </div>
                <h3>Tu sector aquí</h3>
                <p>¿No ves el tuyo? Dinos a qué te dedicas y diseñamos un agente IA a medida.</p>
                <span className="sector-link">Proponer mi sector →</span>
              </a>
            </div>

            <div className="sectors-cta reveal">
              <a href="/soluciones" className="hero-btn primary" data-testid="home-sectors-all">
                Ver todas las soluciones por sector →
              </a>
            </div>
          </div>
        </section>

        {/* Process Section */}
        <section id="como-funciona" className="process-section">
          <div className="section-container">
            <h2 className="section-title">
              Tu IA Personalizada en <span className="text-blue">4 Pasos Sencillos</span>
            </h2>
            <p className="section-subtitle">Desde la primera sesión hasta la optimización continua, te acompañamos en todo el proceso.</p>
            
            <div className="steps-row">
              <div className="step-card-clean reveal reveal-up">
                <div className="step-icon">🔍</div>
                <div className="step-number-blue">01</div>
                <h3>Exploramos tu Negocio</h3>
                <p>Entrevista ligera para entender tu propuesta, tu voz y tus objetivos. Aquí definimos el mapa de tu IA personalizada.</p>
              </div>
              
              <div className="step-card-clean reveal reveal-up" style={{transitionDelay: '100ms'}}>
                <div className="step-icon">⚙️</div>
                <div className="step-number-blue">02</div>
                <h3>Diseñamos tu Agente</h3>
                <p>Configuramos el comportamiento, tono y criterios. Tu IA aprende a pensar contigo (no en tu lugar).</p>
              </div>
              
              <div className="step-card-clean reveal reveal-up" style={{transitionDelay: '200ms'}}>
                <div className="step-icon">🎯</div>
                <div className="step-number-blue">03</div>
                <h3>Integración Digital</h3>
                <p>Lo integramos en tu web, email, atención a clientes o creación de contenidos. Donde más impacto te genere.</p>
              </div>
              
              <div className="step-card-clean reveal reveal-up" style={{transitionDelay: '300ms'}}>
                <div className="step-icon">📈</div>
                <div className="step-number-blue">04</div>
                <h3>Optimización Continua</h3>
                <p>Medimos resultados, afinamos respuestas y ampliamos usos. Evolución continua con foco en ROI.</p>
              </div>
            </div>

            <div className="examples-box-clean">
              <h4>Ejemplos de Uso</h4>
              <ul>
                <li>✓ Responder dudas de clientes con tu tono y criterios</li>
                <li>✓ Redactar ofertas, emails y publicaciones listas</li>
                <li>✓ Crear guiones de vídeo coherentes con tu marca</li>
                <li>✓ Filtrar leads y preparar reuniones con info clave</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="precios" className="pricing-section">
          <div className="section-container">
            <h2 className="section-title">
              Elige tu <span className="text-blue">Plan Perfecto</span>
            </h2>
            <p className="section-subtitle">Comienza hoy y multiplica tu productividad con nuestros Super Agentes de IA</p>
            
            <div className="pricing-notice-clean pricing-notice-animated">
              <h3>📋 Solicita tu Presupuesto Personalizado</h3>
              <p>Estos precios son orientativos. Contacta con nosotros para recibir un presupuesto detallado adaptado a tus necesidades específicas.</p>
              <p className="pricing-notice-extra">Una vez hecha la reserva, nos pondremos en contacto con usted para concretar la personalización. <strong>Mínimo plazo de entrega: 5 días laborables.</strong></p>
            </div>

            <div className="pricing-grid-clean">
              <div className="pricing-card-white reveal reveal-up">
                <h3>Starter Pack</h3>
                <p className="plan-subtitle">Perfecto para empezar y probar los agentes</p>
                <div className="price-large">99,00€</div>
                <p className="credits-blue">100 créditos</p>
                <ul className="features-list-clean">
                  <li>✓ 100 créditos de uso</li>
                  <li>✓ 1 Súper Agente personalizado</li>
                  <li>✓ Soporte por email y WhatsApp</li>
                  <li>✓ Documentación completa</li>
                  <li>✓ Demostraciones incluidas</li>
                </ul>
                <button className="plan-button-dark" onClick={() => openBudgetForm('Starter Pack - 99,00€')}>📧 Solicitar Presupuesto</button>
              </div>
              
              <div className="pricing-card-white featured reveal reveal-up" style={{transitionDelay: '120ms'}}>
                <div className="popular-badge-blue">MÁS POPULAR</div>
                <h3>Professional Pack</h3>
                <p className="plan-subtitle">Ideal para profesionales y pequeños negocios</p>
                <div className="price-large">249,00€</div>
                <p className="credits-blue">350 créditos</p>
                <ul className="features-list-clean">
                  <li>✓ 350 créditos de uso</li>
                  <li>✓ Acceso a los 3 Super Agentes</li>
                  <li>✓ Soporte prioritario</li>
                  <li>✓ Integración personalizada</li>
                  <li>✓ Guía por WhatsApp o app de pantalla compartida</li>
                  <li>✓ Actualización gratuita el PRIMER mes</li>
                </ul>
                <button className="plan-button-blue" onClick={() => openBudgetForm('Professional Pack - 249,00€')}>📧 Solicitar Presupuesto</button>
              </div>
              
              <div className="pricing-card-white reveal reveal-up" style={{transitionDelay: '240ms'}}>
                <h3>Enterprise Pack</h3>
                <p className="plan-subtitle">Para equipos que necesitan escalar</p>
                <div className="price-large">2.300€</div>
                <p className="credits-blue">Implantación completa</p>
                <ul className="features-list-clean">
                  <li>✓ <strong>Implantación:</strong> 5 agentes + flujos + pruebas + formación</li>
                  <li>✓ <strong>Opcional - Servicio mensual:</strong> 599€/mes (operación + mejora, según volumen)</li>
                  <li>✓ <strong>Opcional - Extra WhatsApp/voz:</strong> +400€ setup (voz corporativa personalizada, con consentimiento y contrato)</li>
                  <li>✓ <strong>Caso de servicio mensual:</strong> Mínimo 3 meses de servicio para asegurar completo el chequeo</li>
                </ul>
                <button className="plan-button-dark" onClick={() => openBudgetForm('Enterprise Pack - 2.300€')}>📧 Solicitar Presupuesto</button>
              </div>
            </div>

            <p className="pricing-footer-clean">
              📧 Contacto directo • 💬 Presupuesto personalizado • ✨ Sin compromiso • 🤝 Asesoramiento previo incluido
            </p>
          </div>
        </section>

        {/* Modal Formulario de Presupuesto */}
        {showBudgetForm && (
          <div className="budget-modal-overlay" onClick={() => setShowBudgetForm(false)}>
            <div className="budget-modal" onClick={(e) => e.stopPropagation()}>
              <button className="budget-modal-close" onClick={() => setShowBudgetForm(false)}>✕</button>
              {!formSubmitted ? (
                <>
                  <h2>📋 Solicitar Presupuesto</h2>
                  <p className="budget-plan-selected">Plan seleccionado: <strong>{budgetForm.plan}</strong></p>
                  <form onSubmit={handleBudgetSubmit}>
                    <div className="form-group">
                      <label>Nombre completo *</label>
                      <input 
                        type="text" 
                        required 
                        value={budgetForm.nombre}
                        onChange={(e) => setBudgetForm({...budgetForm, nombre: e.target.value})}
                        placeholder="Tu nombre completo"
                      />
                    </div>
                    <div className="form-group">
                      <label>Email *</label>
                      <input 
                        type="email" 
                        required 
                        value={budgetForm.email}
                        onChange={(e) => setBudgetForm({...budgetForm, email: e.target.value})}
                        placeholder="tu@email.com"
                      />
                    </div>
                    <div className="form-group">
                      <label>Teléfono móvil (opcional)</label>
                      <input 
                        type="tel" 
                        value={budgetForm.telefono}
                        onChange={(e) => setBudgetForm({...budgetForm, telefono: e.target.value})}
                        placeholder="+34 600 000 000"
                      />
                    </div>

                    <div className="form-group">
                      <label>¿Te interesa algún agente en particular? (opcional)</label>
                      <select
                        value={budgetForm.agente}
                        onChange={(e) => setBudgetForm({...budgetForm, agente: e.target.value})}
                        data-testid="budget-agent-select"
                      >
                        <option value="">Sin preferencia</option>
                        <option value="IRIS">IRIS — vida digital, personal y profesional</option>
                        <option value="ALEX">ALEX — trabajo, finanzas y decisiones</option>
                        <option value="UMBRAL">UMBRAL — identidad, relaciones y decisiones</option>
                        <option value="Varios / No lo tengo claro">Varios / No lo tengo claro</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label htmlFor="budget-message">¿En qué proyecto podemos ayudarte? (opcional)</label>
                      <textarea
                        id="budget-message"
                        rows={5}
                        value={budgetForm.mensaje}
                        onChange={(e) => setBudgetForm({...budgetForm, mensaje: e.target.value})}
                        placeholder="Cuéntanos brevemente qué te gustaría conseguir: tipo de negocio, procesos a automatizar, retos actuales, plazos, etc."
                        data-testid="budget-message-textarea"
                      />
                    </div>

                    {/* Honeypot: hidden from real users, tempting for bots */}
                    <div
                      className="hp-field"
                      aria-hidden="true"
                      style={{ position: 'absolute', left: '-10000px', top: 'auto', width: '1px', height: '1px', overflow: 'hidden' }}
                    >
                      <label>Tu sitio web</label>
                      <input
                        type="text"
                        tabIndex={-1}
                        autoComplete="off"
                        value={budgetForm.website}
                        onChange={(e) => setBudgetForm({...budgetForm, website: e.target.value})}
                      />
                    </div>

                    <div className="form-group captcha-group" data-testid="captcha-group">
                      <label>
                        Verificación de seguridad *
                        <button
                          type="button"
                          className="captcha-refresh"
                          onClick={fetchCaptcha}
                          title="Cambiar pregunta"
                          aria-label="Cambiar pregunta"
                        >
                          ↻
                        </button>
                      </label>
                      <div className="captcha-row">
                        <span className="captcha-question" data-testid="captcha-question">
                          {captchaLoading ? 'Cargando…' : (captcha.question || 'No disponible')}
                        </span>
                        <input
                          type="text"
                          inputMode="numeric"
                          required
                          value={budgetForm.captcha_answer}
                          onChange={(e) => setBudgetForm({...budgetForm, captcha_answer: e.target.value})}
                          placeholder="Tu respuesta"
                          data-testid="captcha-input"
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="budget-submit-btn"
                      disabled={formSubmitting || !captcha.token}
                      data-testid="budget-submit-btn"
                    >
                      {formSubmitting ? 'Enviando...' : 'Enviar Solicitud →'}
                    </button>
                    {formError && (
                      <p className="budget-error" data-testid="budget-error">{formError}</p>
                    )}
                  </form>
                  <p className="budget-notice">Una vez hecha la reserva, nos pondremos en contacto con usted para concretar la personalización. Mínimo plazo de entrega: 5 días laborables.</p>
                </>
              ) : (
                <div className="budget-success">
                  <div className="success-icon">✅</div>
                  <h2>¡Solicitud Enviada!</h2>
                  <p>Nos pondremos en contacto contigo en breve.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Reviews / Testimonials Section */}
        <section id="resenas" className="reviews-section">
          <div className="section-container">
            <h2 className="section-title reveal">
              Lo que dicen <span className="text-blue">nuestros clientes</span>
            </h2>
            <p className="section-subtitle reveal">
              Opiniones reales de profesionales y pequeños negocios que ya trabajan con sus agentes
            </p>

            {reviewsStats.count > 0 && (
              <div className="reviews-summary reveal" data-testid="reviews-summary">
                <div className="reviews-stars-big" aria-label={`Valoración media ${reviewsStats.average} de 5`}>
                  {[1,2,3,4,5].map(n => (
                    <span key={n} className={`star ${n <= Math.round(reviewsStats.average) ? 'on' : ''}`}>★</span>
                  ))}
                </div>
                <div className="reviews-summary-text">
                  <strong>{reviewsStats.average}</strong> / 5 · basado en {reviewsStats.count} reseñas
                </div>
              </div>
            )}

            {reviews.length > 0 ? (
              <div className="reviews-grid">
                {reviews.slice(0, 6).map((r) => (
                  <article key={r.id} className="review-card reveal reveal-up" data-testid={`review-${r.id}`}>
                    <div className="review-stars" aria-label={`${r.rating} estrellas`}>
                      {[1,2,3,4,5].map(n => (
                        <span key={n} className={`star ${n <= r.rating ? 'on' : ''}`}>★</span>
                      ))}
                    </div>
                    <p className="review-text">"{r.text}"</p>
                    <div className="review-author">
                      <strong>{r.author}</strong>
                      {r.role ? <span className="review-role"> · {r.role}</span> : null}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="reviews-empty reveal">Aún no hay reseñas. ¿Quieres ser el primero?</p>
            )}

            <div className="reviews-cta reveal">
              <button
                type="button"
                className="leave-review-btn"
                onClick={openReviewForm}
                data-testid="leave-review-btn"
              >
                ✍️ Dejar mi reseña
              </button>
            </div>
          </div>
        </section>

        {/* Modal Formulario Reseña */}
        {showReviewForm && (
          <div className="budget-modal-overlay" onClick={() => setShowReviewForm(false)}>
            <div className="budget-modal" onClick={(e) => e.stopPropagation()}>
              <button className="budget-modal-close" onClick={() => setShowReviewForm(false)}>✕</button>
              {!reviewSubmitted ? (
                <>
                  <h2>✍️ Deja tu reseña</h2>
                  <p className="budget-plan-selected">Tu opinión nos ayuda a seguir mejorando</p>
                  <form onSubmit={handleReviewSubmit}>
                    <div className="form-group">
                      <label>Tu nombre *</label>
                      <input
                        type="text"
                        required
                        maxLength={80}
                        value={reviewForm.author}
                        onChange={(e) => setReviewForm({...reviewForm, author: e.target.value})}
                        placeholder="Tu nombre"
                        data-testid="review-author"
                      />
                    </div>
                    <div className="form-group">
                      <label>¿A qué te dedicas? (opcional)</label>
                      <input
                        type="text"
                        maxLength={80}
                        value={reviewForm.role}
                        onChange={(e) => setReviewForm({...reviewForm, role: e.target.value})}
                        placeholder="Ej: Fisioterapeuta, Dueño de cafetería..."
                        data-testid="review-role"
                      />
                    </div>
                    <div className="form-group">
                      <label>Valoración *</label>
                      <div className="rating-input" data-testid="review-rating">
                        {[1,2,3,4,5].map(n => (
                          <button
                            type="button"
                            key={n}
                            className={`rating-star ${n <= reviewForm.rating ? 'on' : ''}`}
                            onClick={() => setReviewForm({...reviewForm, rating: n})}
                            aria-label={`${n} estrellas`}
                          >
                            ★
                          </button>
                        ))}
                        <span className="rating-value">{reviewForm.rating}/5</span>
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Tu reseña * (mín. 20 caracteres)</label>
                      <textarea
                        required
                        rows={5}
                        maxLength={1000}
                        value={reviewForm.text}
                        onChange={(e) => setReviewForm({...reviewForm, text: e.target.value})}
                        placeholder="Cuéntanos brevemente tu experiencia..."
                        data-testid="review-text"
                      />
                    </div>

                    {/* Honeypot */}
                    <div className="hp-field" aria-hidden="true" style={{position:'absolute',left:'-10000px',width:'1px',height:'1px',overflow:'hidden'}}>
                      <label>Web</label>
                      <input type="text" tabIndex={-1} autoComplete="off"
                        value={reviewForm.website}
                        onChange={(e) => setReviewForm({...reviewForm, website: e.target.value})} />
                    </div>

                    <div className="form-group captcha-group">
                      <label>
                        Verificación de seguridad *
                        <button type="button" className="captcha-refresh" onClick={fetchReviewCaptcha} aria-label="Cambiar pregunta">↻</button>
                      </label>
                      <div className="captcha-row">
                        <span className="captcha-question">{reviewCaptcha.question || 'Cargando…'}</span>
                        <input
                          type="text"
                          inputMode="numeric"
                          required
                          value={reviewForm.captcha_answer}
                          onChange={(e) => setReviewForm({...reviewForm, captcha_answer: e.target.value})}
                          placeholder="Respuesta"
                          data-testid="review-captcha"
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="budget-submit-btn"
                      disabled={reviewSubmitting || !reviewCaptcha.token}
                      data-testid="review-submit"
                    >
                      {reviewSubmitting ? 'Enviando...' : 'Enviar reseña →'}
                    </button>
                    {reviewError && (
                      <p className="budget-error">{reviewError}</p>
                    )}
                  </form>
                </>
              ) : (
                <div className="budget-success">
                  <div className="success-icon">🌟</div>
                  <h2>¡Gracias por tu reseña!</h2>
                  <p>Ya está publicada en la web.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* FAQ Section */}
        <section id="faq" className="faq-section">
          <div className="section-container">
            <h2 className="section-title">Preguntas Frecuentes</h2>
            <p className="section-subtitle">Todo lo que necesitas saber sobre nuestros agentes de IA</p>
            
            <div className="faq-list">
              {faqData.map((faq, index) => (
                <div key={index} className="faq-item">
                  <button 
                    className={`faq-question ${expandedFaq === index ? 'active' : ''}`}
                    onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                  >
                    {faq.question}
                    <span className="faq-icon">{expandedFaq === index ? '−' : '+'}</span>
                  </button>
                  {expandedFaq === index && (
                    <div className="faq-answer">
                      {faq.answer}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="faq-contact">
              <h3>¿Aún tienes dudas?</h3>
              <p>Estamos aquí para ayudarte. Contáctanos y resolveremos todas tus preguntas.</p>
              <div className="faq-contact-actions">
                <button
                  type="button"
                  className="contact-button"
                  onClick={() => openBudgetForm('Consulta general')}
                  data-testid="faq-contact-btn"
                >
                  Contactar ahora
                </button>
                <a
                  href={`${API}/whatsapp`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="whatsapp-button"
                  data-testid="faq-whatsapp-btn"
                  aria-label="Contactar por WhatsApp"
                >
                  <svg className="wa-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.967-.94 1.164-.173.198-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.67-.51-.173-.007-.371-.009-.57-.009-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.625.712.227 1.36.195 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/>
                  </svg>
                  <span className="wa-label">
                    <span className="wa-text">WhatsApp</span>
                    <span className="wa-note">Solo WhatsApp</span>
                  </span>
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
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

        {/* Cookie Banner */}
        {showCookieBanner && (
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
                <button className="cookie-btn accept" onClick={acceptCookies}>
                  ✅ Aceptar todas
                </button>
                <button className="cookie-btn reject" onClick={rejectCookies}>
                  ❌ Rechazar
                </button>
                <a href="/legal#cookies" className="cookie-link">
                  Más información
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

