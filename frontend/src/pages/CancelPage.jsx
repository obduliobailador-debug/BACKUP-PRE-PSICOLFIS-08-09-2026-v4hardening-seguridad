import { usePageSeo } from "../lib/seo";

export const CancelPage = () => {
  usePageSeo({
    title: 'Pago cancelado · PSICOLFIS.NET',
    description: 'Has cancelado el proceso de pago. Puedes volver cuando quieras.',
    canonicalPath: '/cancel',
    noindex: true,
  });
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
