/**
 * #resenas — reviews carousel. Data (`reviews`, `reviewsStats`) is fetched
 * in Home.jsx from /api/reviews. `openReviewForm` opens the shared review
 * modal owned by Home.jsx.
 */
export const ReviewsSection = ({ reviews, reviewsStats, openReviewForm }) => (
  <>
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
  </>
);
