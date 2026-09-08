import { useState, useEffect } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";
import { API } from "../api";
import { usePageSeo } from "../lib/seo";

export const SuccessPage = () => {
  usePageSeo({
    title: 'Pago confirmado · PSICOLFIS.NET',
    description: 'Gracias por tu compra. Tu agente de IA estará listo en breve.',
    canonicalPath: '/success',
    noindex: true,
  });
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

