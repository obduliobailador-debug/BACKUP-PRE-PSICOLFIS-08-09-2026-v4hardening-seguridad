import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useSearchParams } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Enlaces directos de pago de Stripe por agente
const AGENT_STRIPE_URLS = {
  iris: "https://buy.stripe.com/cNicMY9Jf5NffL30aH7ok00",
  alex: "https://buy.stripe.com/aFabIU2gN8ZraqJg9F7ok01",
  umbral: "https://buy.stripe.com/14A5kwbRnejL56paPl7ok02"
};

const agents = [
  {
    id: "iris",
    name: "IRIS",
    description: "Tu compañera inteligente para la vida digital, personal y profesional.",
    video: "/videos/iris_sonriendo.mp4",
    price: "50€"
  },
  {
    id: "alex",
    name: "ALEX",
    description: "Tu compañero inteligente para trabajo, finanzas y decisiones.",
    video: "/videos/alex_sonriendo.mp4",
    price: "50€"
  },
  {
    id: "umbral",
    name: "UMBRAL",
    description: "Tu compañero inteligente para identidad, relaciones y decisiones.",
    video: "/videos/umbral_sonriendo.mp4",
    price: "50€"
  }
];

const faqData = [
  {
    question: "¿Qué es un agente de IA personalizado?",
    answer: "Es un asistente diseñado para pensar y responder con tu tono, tus criterios y tus objetivos. No es genérico: se entrena con tu forma de trabajar y representa tu negocio."
  },
  {
    question: "¿Necesito conocimientos técnicos?",
    answer: "No. Nosotros configuramos e integramos todo; tú lo usas como una herramienta diaria con nuestro soporte completo."
  },
  {
    question: "¿Cuánto tarda la implementación?",
    answer: "Un piloto suele estar listo en 5-10 días hábiles según complejidad e integraciones necesarias."
  },
  {
    question: "¿Qué tareas puede cubrir un agente?",
    answer: "Respuestas a clientes, redacción de contenidos, guiones de vídeo, filtrado de leads, soporte interno, emails, documentación, y muchísimo más."
  },
  {
    question: "¿Cómo se entrena con mi tono?",
    answer: "Analizamos ejemplos de tu comunicación (textos, vídeos) y definimos una guía de estilo que el agente respeta en cada interacción."
  },
  {
    question: "¿Mis datos están seguros?",
    answer: "Sí. Trabajamos con buenas prácticas de privacidad, solo usamos los datos estrictamente necesarios y bajo acuerdos de confidencialidad."
  },
  {
    question: "¿Cumple con RGPD?",
    answer: "Sí, diseñamos el uso para alinearlo con RGPD/LOPDGDD. Te orientamos en cláusulas y avisos básicos necesarios."
  },
  {
    question: "¿Qué diferencia hay con un chatbot genérico?",
    answer: "Un chatbot genérico responde sin contexto. Un agente personalizado entiende tu negocio, tu tono y tus objetivos específicos."
  },
  {
    question: "¿Puedo integrarlo en mi web actual?",
    answer: "Sí. Podemos añadirlo como widget, iframe o vía API según tu plataforma y necesidades."
  },
  {
    question: "¿Qué mantenimiento requiere?",
    answer: "Actualizaciones periódicas, revisión de respuestas y afinación según nuevos productos, campañas o cambios en tu negocio."
  },
  {
    question: "¿Cómo medimos resultados?",
    answer: "Definimos KPIs (tiempo ahorrado, calidad de respuesta, conversión) y revisamos mejoras en ciclos mensuales con reportes claros."
  },
  {
    question: "¿Ofrecen formación para mi equipo?",
    answer: "Sí. Incluimos una sesión de uso y buenas prácticas, con opciones de formación ampliada si la necesitas."
  }
];

const Home = () => {
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

  const handlePurchase = (agentId) => {
    const url = AGENT_STRIPE_URLS[agentId];
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
                    <button
                      className="buy-button"
                      onClick={() => handlePurchase(agent.id)}
                      disabled={loading[agent.id]}
                      data-testid={`buy-button-${agent.id}`}
                    >
                      {loading[agent.id] ? 'Procesando...' : 'LO QUIERO...'}
                    </button>
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
              <li><a href="#como-funciona">Cómo Funciona</a></li>
              <li><a href="#precios">Precios</a></li>
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
              <img src="https://customer-assets.emergentagent.com/job_dynamic-psicolfis/artifacts/xu2c0617_PSICOLFISNET_CON%20NOMBRE.png" alt="PSICOLFIS" className="hero-logo" />
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
            <h2 className="section-title">
              La Transformación es <span className="text-blue">Real</span>
            </h2>
            <p className="section-subtitle">Tu conocimiento convertido en una herramienta que trabaja por ti, 24/7</p>
            
            <div className="transformation-image-large">
              <img src="https://customer-assets.emergentagent.com/job_dynamic-psicolfis/artifacts/jd1bv0v9_Imagen%20de%20antes%20y%20despues.jpeg" alt="Transformación" />
            </div>
            
            <div className="transformation-comparison">
              <div className="comparison-card before">
                <h3>❌ Antes (Sin IA)</h3>
                <ul>
                  <li>• Tareas repetitivas consumen tu día</li>
                  <li>• Respuestas manuales a cada cliente</li>
                  <li>• Creación de contenido lenta</li>
                  <li>• Sin tiempo para estrategia</li>
                  <li>• Sobrecarga de trabajo constante</li>
                </ul>
              </div>
              
              <div className="comparison-card after">
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
                poster="https://customer-assets.emergentagent.com/job_dynamic-psicolfis/artifacts/xu2c0617_PSICOLFISNET_CON%20NOMBRE.png"
                style={{display: 'none'}}
              >
                <source src="/videos/agentes_ia.mp4" type="video/mp4" />
              </video>
            </div>

            <p className="video-cta-text">Descubre cómo multiplicar tu productividad</p>

            <div className="benefits-grid">
              <div className="benefit-card">
                <div className="benefit-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <h4>Ahorra 10+ horas/semana</h4>
                <p>Recupera tiempo valioso automatizando tareas repetitivas</p>
              </div>
              <div className="benefit-card">
                <div className="benefit-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="1" x2="12" y2="23"></line>
                    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                  </svg>
                </div>
                <h4>Aumenta tus ingresos</h4>
                <p>Responde más rápido y cierra más ventas</p>
              </div>
              <div className="benefit-card">
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
              <div className="feature-card-clean">
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                  </svg>
                </div>
                <h3>IA con Alma</h3>
                <p>Cada agente respeta tu voz, tus valores y tu forma de decidir. No son robots genéricos, son extensiones de tu negocio.</p>
              </div>
              
              <div className="feature-card-clean">
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
              
              <div className="feature-card-clean">
                <div className="feature-icon-svg">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                  </svg>
                </div>
                <h3>Resultados Medibles</h3>
                <p>Productividad, presencia e ingresos. Nos enfocamos en lo que realmente mueve la aguja de tu negocio.</p>
              </div>
              
              <div className="feature-card-clean">
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

        {/* Process Section */}
        <section id="como-funciona" className="process-section">
          <div className="section-container">
            <h2 className="section-title">
              Tu IA Personalizada en <span className="text-blue">4 Pasos Sencillos</span>
            </h2>
            <p className="section-subtitle">Desde la primera sesión hasta la optimización continua, te acompañamos en todo el proceso.</p>
            
            <div className="steps-row">
              <div className="step-card-clean">
                <div className="step-icon">🔍</div>
                <div className="step-number-blue">01</div>
                <h3>Exploramos tu Negocio</h3>
                <p>Entrevista ligera para entender tu propuesta, tu voz y tus objetivos. Aquí definimos el mapa de tu IA personalizada.</p>
              </div>
              
              <div className="step-card-clean">
                <div className="step-icon">⚙️</div>
                <div className="step-number-blue">02</div>
                <h3>Diseñamos tu Agente</h3>
                <p>Configuramos el comportamiento, tono y criterios. Tu IA aprende a pensar contigo (no en tu lugar).</p>
              </div>
              
              <div className="step-card-clean">
                <div className="step-icon">🎯</div>
                <div className="step-number-blue">03</div>
                <h3>Integración Digital</h3>
                <p>Lo integramos en tu web, email, atención a clientes o creación de contenidos. Donde más impacto te genere.</p>
              </div>
              
              <div className="step-card-clean">
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
              <div className="pricing-card-white">
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
              
              <div className="pricing-card-white featured">
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
              
              <div className="pricing-card-white">
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
              <button
                type="button"
                className="contact-button"
                onClick={() => openBudgetForm('Consulta general')}
                data-testid="faq-contact-btn"
              >
                Contactar ahora
              </button>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="footer-section">
          <div className="footer-container">
            <div className="footer-content">
              <div className="footer-brand">
                <img src="https://customer-assets.emergentagent.com/job_dynamic-psicolfis/artifacts/xu2c0617_PSICOLFISNET_CON%20NOMBRE.png" alt="PSICOLFIS" className="footer-logo" />
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
              <p>&copy; 2024 PSICOLFIS.NET - Todos los derechos reservados</p>
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

const SuccessPage = () => {
  const [searchParams] = useSearchParams();
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const [statusMessage, setStatusMessage] = useState('Verificando pago...');
  const sessionId = searchParams.get('session_id');

  const pollPaymentStatus = async (sessionId, attempts) => {
    const maxAttempts = 5;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setPaymentStatus('timeout');
      setStatusMessage('No se pudo verificar el pago. Por favor, revisa tu email para confirmación.');
      return;
    }

    try {
      const response = await axios.get(`${API}/checkout/status/${sessionId}`);

      if (response.data.payment_status === 'paid') {
        setPaymentStatus('success');
        setStatusMessage('¡Pago exitoso! Gracias por tu compra.');
        return;
      } else if (response.data.status === 'expired') {
        setPaymentStatus('error');
        setStatusMessage('La sesión de pago expiró. Por favor, intenta nuevamente.');
        return;
      }

      setStatusMessage('Procesando pago...');
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      console.error('Error checking payment:', error);
      setPaymentStatus('error');
      setStatusMessage('Error al verificar el pago. Por favor, intenta nuevamente.');
    }
  };

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus(sessionId, 0);
    }
  }, [sessionId, pollPaymentStatus]);

  return (
    <div className="status-page">
      <div className="status-card">
        <div className={`status-icon ${paymentStatus}`}>
          {paymentStatus === 'checking' && '⏳'}
          {paymentStatus === 'success' && '✅'}
          {paymentStatus === 'error' && '❌'}
          {paymentStatus === 'timeout' && '⏰'}
        </div>
        <h1>{statusMessage}</h1>
        {paymentStatus === 'success' && (
          <p>Recibirás un correo con los detalles de acceso a tu agente.</p>
        )}
        <a href="/" className="back-link">Volver al inicio</a>
      </div>
    </div>
  );
};

const CancelPage = () => {
  return (
    <div className="status-page">
      <div className="status-card">
        <div className="status-icon error">❌</div>
        <h1>Pago cancelado</h1>
        <p>Has cancelado el proceso de pago.</p>
        <a href="/" className="back-link">Volver al inicio</a>
      </div>
    </div>
  );
};

// Página de Agentes (clon exacto de config-recovery-1)
const AgentesPage = () => {
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

  const handleBuyAgent = (agentId) => {
    const url = AGENT_STRIPE_URLS[agentId];
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
                  <span className="agente-price-v2">{agent.price}</span>
                  <button
                    className="agente-buy-btn-v2"
                    onClick={() => handleBuyAgent(agent.id)}
                    disabled={loading[agent.id]}
                    data-testid={`agente-buy-${agent.id}`}
                  >
                    {loading[agent.id] ? "Procesando..." : "Lo Quiero"}
                  </button>
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

const LegalPage = () => {
  return (
    <div className="legal-page">
      <div className="legal-container">
        <div className="legal-header">
          <a href="/" className="back-link">← Volver al inicio</a>
          <h1>Aviso Legal y Política de Privacidad</h1>
        </div>

        <div className="legal-content">
          <section id="aviso-legal">
            <h2>Aviso Legal</h2>
            
            <h3>1. Datos Identificativos</h3>
            <p>
              En cumplimiento del artículo 10 de la Ley 34/2002, de 11 de julio, de Servicios de la Sociedad de la Información y de Comercio Electrónico, se informa que:
            </p>
            <ul>
              <li><strong>Denominación social:</strong> PSICOLFIS.NET</li>
              <li><strong>Domicilio:</strong> España</li>
              <li><strong>Correo electrónico:</strong> obdulio@psicolfis.net</li>
              <li><strong>Sitio web:</strong> psicolfis.net</li>
            </ul>

            <h3>2. Objeto</h3>
            <p>
              El presente aviso legal regula el uso del sitio web psicolfis.net, propiedad de PSICOLFIS.NET, que pone a disposición de los usuarios de Internet sus servicios de consultoría en inteligencia artificial y desarrollo de agentes personalizados.
            </p>

            <h3>3. Condiciones de Uso</h3>
            <p>
              El acceso y uso de este sitio web implica la aceptación plena de las presentes condiciones generales. Si no está de acuerdo con estas condiciones, no debe usar este sitio web.
            </p>

            <h3>4. Responsabilidad</h3>
            <p>
              PSICOLFIS.NET no se hace responsable de los daños y perjuicios que pudieran derivarse del uso incorrecto de este sitio web. El usuario es el único responsable del uso que haga de los contenidos y servicios ofrecidos.
            </p>
          </section>

          <section id="privacidad">
            <h2>Política de Privacidad</h2>
            
            <h3>1. Responsable del Tratamiento</h3>
            <p>
              <strong>PSICOLFIS.NET</strong> es el responsable del tratamiento de los datos personales del Usuario y le informa que estos datos serán tratados de conformidad con lo dispuesto en el Reglamento (UE) 2016/679 de 27 de abril de 2016 (GDPR) relativo a la protección de las personas físicas en lo que respecta al tratamiento de datos personales y a la libre circulación de estos datos.
            </p>

            <h3>2. Finalidad del Tratamiento</h3>
            <p>Los datos personales se tratarán para las siguientes finalidades:</p>
            <ul>
              <li>Gestión de consultas y solicitudes de información</li>
              <li>Prestación de servicios de consultoría en IA</li>
              <li>Procesamiento de pagos y facturación</li>
              <li>Comunicaciones comerciales (con consentimiento previo)</li>
            </ul>

            <h3>3. Legitimación</h3>
            <p>
              La base legal para el tratamiento de sus datos es el consentimiento del interesado, la ejecución de un contrato o la aplicación de medidas precontractuales.
            </p>

            <h3>4. Conservación de Datos</h3>
            <p>
              Los datos se conservarán durante el tiempo necesario para cumplir con la finalidad para la que se recabaron y para determinar las posibles responsabilidades que se pudieran derivar de dicha finalidad y del tratamiento de los datos.
            </p>

            <h3>5. Derechos del Usuario</h3>
            <p>El Usuario tiene derecho a:</p>
            <ul>
              <li>Solicitar el acceso a los datos personales</li>
              <li>Solicitar su rectificación o supresión</li>
              <li>Solicitar la limitación de su tratamiento</li>
              <li>Oponerse al tratamiento</li>
              <li>Solicitar la portabilidad de los datos</li>
            </ul>
            <p>
              Para ejercer estos derechos, puede contactar con nosotros en: <strong>obdulio@psicolfis.net</strong>
            </p>
          </section>

          <section id="cookies">
            <h2>Política de Cookies</h2>
            
            <h3>¿Qué son las cookies?</h3>
            <p>
              Las cookies son pequeños archivos de texto que se almacenan en su dispositivo cuando visita un sitio web. Nos ayudan a mejorar su experiencia de navegación y a analizar el uso del sitio.
            </p>

            <h3>Tipos de cookies que utilizamos:</h3>
            <ul>
              <li><strong>Cookies técnicas:</strong> Necesarias para el funcionamiento del sitio web</li>
              <li><strong>Cookies analíticas:</strong> Para analizar el comportamiento de los usuarios</li>
              <li><strong>Cookies de personalización:</strong> Para recordar sus preferencias</li>
            </ul>

            <h3>Gestión de cookies</h3>
            <p>
              Puede configurar su navegador para rechazar las cookies o para que le avise cuando se envíen cookies. Sin embargo, si rechaza las cookies, es posible que no pueda utilizar todas las funciones de nuestro sitio web.
            </p>
          </section>

          <div className="legal-contact">
            <h3>Contacto</h3>
            <p>
              Para cualquier consulta relacionada con este aviso legal o política de privacidad, puede contactarnos en:
            </p>
            <p><strong>Email:</strong> obdulio@psicolfis.net</p>
            <p><strong>Última actualización:</strong> Diciembre 2024</p>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/agentes" element={<AgentesPage />} />
          <Route path="/success" element={<SuccessPage />} />
          <Route path="/cancel" element={<CancelPage />} />
          <Route path="/legal" element={<LegalPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
