/**
 * #precios — pricing table. Every CTA opens the budget modal owned by
 * Home.jsx via the `openBudgetForm(plan)` callback.
 */
export const PricingSection = ({ openBudgetForm }) => (
  <>
        <section id="precios" className="pricing-section">
          <div className="section-container">
            <h2 className="section-title">
              Elige tu <span className="text-blue">Plan Perfecto</span>
            </h2>
            <p className="section-subtitle">Comienza hoy y multiplica tu productividad con nuestros Super Agentes de IA</p>
            
            <div className="pricing-notice-clean pricing-notice-animated">
              <h3><span aria-hidden="true">📋</span> Solicita tu Presupuesto Personalizado</h3>
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
                <button className="plan-button-dark" onClick={() => openBudgetForm('Starter Pack - 99,00€')}><span aria-hidden="true">📧</span> Solicitar Presupuesto</button>
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
                <button className="plan-button-blue" onClick={() => openBudgetForm('Professional Pack - 249,00€')}><span aria-hidden="true">📧</span> Solicitar Presupuesto</button>
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
                <button className="plan-button-dark" onClick={() => openBudgetForm('Enterprise Pack - 2.300€')}><span aria-hidden="true">📧</span> Solicitar Presupuesto</button>
              </div>
            </div>

            <p className="pricing-footer-clean">
              📧 Contacto directo • 💬 Presupuesto personalizado • ✨ Sin compromiso • 🤝 Asesoramiento previo incluido
            </p>
          </div>
        </section>
  </>
);
