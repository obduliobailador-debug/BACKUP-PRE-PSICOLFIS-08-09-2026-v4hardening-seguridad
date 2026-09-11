import { useEffect, useState } from "react";
import axios from "axios";
import { API, AGENT_STRIPE_URLS, AGENT_STRIPE_URLS_FULL } from "../api";
import { useScrollReveal } from "../hooks/useScrollReveal";
import { useModalA11y } from "../hooks/useModalA11y";
import { usePageSeo } from "../lib/seo";

import { CookieBanner } from "./home/CookieBanner";
import { FaqSection } from "./home/FaqSection";
import { Footer } from "./home/Footer";
import { HeroSection } from "./home/HeroSection";
import { Navbar } from "./home/Navbar";
import { PricingSection } from "./home/PricingSection";
import { ProcessSection } from "./home/ProcessSection";
import { PromoModal } from "./home/PromoModal";
import { ReviewsSection } from "./home/ReviewsSection";
import { SectorsSection } from "./home/SectorsSection";
import { SuperAgentsSection } from "./home/SuperAgentsSection";
import { TransformationSection } from "./home/TransformationSection";
import { VideoSection } from "./home/VideoSection";
import { WhySection } from "./home/WhySection";

/**
 * Landing page orchestrator. Owns the shared state (promo countdown,
 * budget/review form modals, purchases, reviews) and composes the visual
 * sections declared under `./home/`.
 */
export const Home = () => {
  useScrollReveal();
  usePageSeo({
    title: 'PSICOLFIS.NET · Agentes de IA personalizados para tu negocio',
    description: 'Agentes de IA creados a medida para autónomos y pequeños negocios. Automatiza atención, contenido y ventas con IRIS, ALEX y UMBRAL. Resultados en 5-10 días.',
    canonicalPath: '/',
  });
  const [showModal, setShowModal] = useState(true);
  const [timeLeft, setTimeLeft] = useState(15);
  const [loading] = useState({});

  useEffect(() => {
    if (timeLeft > 0 && showModal) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0) {
      setShowModal(false);
    }
  }, [timeLeft, showModal]);

  const formatTime = (seconds) => `00:${seconds.toString().padStart(2, '0')}`;

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

  // ----- Budget form state -----
  const [showBudgetForm, setShowBudgetForm] = useState(false);
  const [budgetForm, setBudgetForm] = useState({
    nombre: '', email: '', telefono: '', plan: '',
    agente: '', mensaje: '', captcha_answer: '', website: ''
  });
  const [captcha, setCaptcha] = useState({ question: '', token: '' });
  const [captchaLoading, setCaptchaLoading] = useState(false);
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const budgetModalRef = useModalA11y({ isOpen: showBudgetForm, onClose: () => setShowBudgetForm(false) });
  const reviewModalRef = useModalA11y({ isOpen: showReviewForm, onClose: () => setShowReviewForm(false) });

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

  // Auto-open budget form when landing with ?demo=<sector>
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
      <PromoModal
        show={showModal}
        onClose={() => setShowModal(false)}
        timeLeft={timeLeft}
        formatTime={formatTime}
        handlePurchase={handlePurchase}
        loading={loading}
      />

      <div className="main-page">
        <Navbar openBudgetForm={openBudgetForm} />
        <HeroSection />
        <TransformationSection />
        <VideoSection />
        <WhySection />
        <SuperAgentsSection />
        <SectorsSection />
        <ProcessSection />
        <PricingSection openBudgetForm={openBudgetForm} />

        {/* Budget request modal */}
        {showBudgetForm && (
          <div className="budget-modal-overlay" onClick={() => setShowBudgetForm(false)}>
            <div className="budget-modal" onClick={(e) => e.stopPropagation()} ref={budgetModalRef} role="dialog" aria-modal="true" aria-labelledby="budget-modal-title" tabIndex={-1}>
              <button className="budget-modal-close" onClick={() => setShowBudgetForm(false)} aria-label="Cerrar">✕</button>
              {!formSubmitted ? (
                <>
                  <h2 id="budget-modal-title">📋 Solicitar Presupuesto</h2>
                  <p className="budget-plan-selected">Plan seleccionado: <strong>{budgetForm.plan}</strong></p>
                  <form onSubmit={handleBudgetSubmit}>
                    <div className="form-group">
                      <label htmlFor="budget-nombre">Nombre completo *</label>
                      <input
                        id="budget-nombre"
                        type="text"
                        required
                        value={budgetForm.nombre}
                        onChange={(e) => setBudgetForm({...budgetForm, nombre: e.target.value})}
                        placeholder="Tu nombre completo"
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="budget-email">Email *</label>
                      <input
                        id="budget-email"
                        type="email"
                        required
                        value={budgetForm.email}
                        onChange={(e) => setBudgetForm({...budgetForm, email: e.target.value})}
                        placeholder="tu@email.com"
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="budget-telefono">Teléfono móvil (opcional)</label>
                      <input
                        id="budget-telefono"
                        type="tel"
                        value={budgetForm.telefono}
                        onChange={(e) => setBudgetForm({...budgetForm, telefono: e.target.value})}
                        placeholder="+34 600 000 000"
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="budget-agente">¿Te interesa algún agente en particular? (opcional)</label>
                      <select
                        id="budget-agente"
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
                      <div className="captcha-label-row">
                        <label htmlFor="budget-captcha">Verificación de seguridad *</label>
                        <button
                          type="button"
                          className="captcha-refresh"
                          onClick={fetchCaptcha}
                          title="Cambiar pregunta"
                          aria-label="Cambiar pregunta"
                        >
                          ↻
                        </button>
                      </div>
                      <div className="captcha-row">
                        <span className="captcha-question" id="budget-captcha-question" data-testid="captcha-question">
                          {captchaLoading ? 'Cargando…' : (captcha.question || 'No disponible')}
                        </span>
                        <input
                          id="budget-captcha"
                          aria-describedby="budget-captcha-question"
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
                      <p className="budget-error" role="alert" data-testid="budget-error">{formError}</p>
                    )}
                  </form>
                  <p className="budget-notice">Una vez hecha la reserva, nos pondremos en contacto con usted para concretar la personalización. Mínimo plazo de entrega: 5 días laborables.</p>
                </>
              ) : (
                <div className="budget-success">
                  <div className="success-icon">✅</div>
                  <h2 id="budget-modal-title">¡Solicitud Enviada!</h2>
                  <p>Nos pondremos en contacto contigo en breve.</p>
                </div>
              )}
            </div>
          </div>
        )}

        <ReviewsSection
          reviews={reviews}
          reviewsStats={reviewsStats}
          openReviewForm={openReviewForm}
        />

        {/* Review modal */}
        {showReviewForm && (
          <div className="budget-modal-overlay" onClick={() => setShowReviewForm(false)}>
            <div className="budget-modal" onClick={(e) => e.stopPropagation()} ref={reviewModalRef} role="dialog" aria-modal="true" aria-labelledby="review-modal-title" tabIndex={-1}>
              <button className="budget-modal-close" onClick={() => setShowReviewForm(false)} aria-label="Cerrar">✕</button>
              {!reviewSubmitted ? (
                <>
                  <h2 id="review-modal-title">✍️ Deja tu reseña</h2>
                  <p className="budget-plan-selected">Tu opinión nos ayuda a seguir mejorando</p>
                  <form onSubmit={handleReviewSubmit}>
                    <div className="form-group">
                      <label htmlFor="review-author">Tu nombre *</label>
                      <input
                        id="review-author"
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
                      <label htmlFor="review-role">¿A qué te dedicas? (opcional)</label>
                      <input
                        id="review-role"
                        type="text"
                        maxLength={80}
                        value={reviewForm.role}
                        onChange={(e) => setReviewForm({...reviewForm, role: e.target.value})}
                        placeholder="Ej: Fisioterapeuta, Dueño de cafetería..."
                        data-testid="review-role"
                      />
                    </div>
                    <div className="form-group">
                      <label id="review-rating-label">Valoración *</label>
                      <div className="rating-input" role="group" aria-labelledby="review-rating-label" data-testid="review-rating">
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
                      <label htmlFor="review-text">Tu reseña * (mín. 20 caracteres)</label>
                      <textarea
                        id="review-text"
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
                      <div className="captcha-label-row">
                        <label htmlFor="review-captcha">Verificación de seguridad *</label>
                        <button type="button" className="captcha-refresh" onClick={fetchReviewCaptcha} aria-label="Cambiar pregunta">↻</button>
                      </div>
                      <div className="captcha-row">
                        <span className="captcha-question" id="review-captcha-question">{reviewCaptcha.question || 'Cargando…'}</span>
                        <input
                          id="review-captcha"
                          aria-describedby="review-captcha-question"
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
                      <p className="budget-error" role="alert">{reviewError}</p>
                    )}
                  </form>
                </>
              ) : (
                <div className="budget-success">
                  <div className="success-icon">🌟</div>
                  <h2 id="review-modal-title">¡Gracias por tu reseña!</h2>
                  <p>Ya está publicada en la web.</p>
                </div>
              )}
            </div>
          </div>
        )}

        <FaqSection openBudgetForm={openBudgetForm} />
        <Footer />
        <CookieBanner />
      </div>
    </div>
  );
};
