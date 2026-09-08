import { useCallback, useEffect, useState } from "react";
import { useAdminApi } from "./useAdminApi";

const AGENT_OPTIONS = [
  { value: "iris", label: "IRIS" },
  { value: "alex", label: "ALEX" },
  { value: "umbral", label: "UMBRAL" },
];

export const AdminAccessLinks = ({ token, onAuthFail }) => {
  const api = useAdminApi(token, onAuthFail);

  // Form state
  const [form, setForm] = useState({
    customer_name: "",
    customer_email: "",
    agent_id: "iris",
    level: "demo",
    days_valid: "",
    send_email: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null); // {type, msg}
  const [lastLink, setLastLink] = useState(null);
  const [copied, setCopied] = useState("");

  // History state
  const [history, setHistory] = useState({ items: [], total: 0 });
  const [loadingHistory, setLoadingHistory] = useState(true);

  const reload = async () => {
    setLoadingHistory(true);
    try {
      const d = await api.get("/admin/access-links");
      setHistory(d || { items: [], total: 0 });
    } finally {
      setLoadingHistory(false);
    }
  };
  useEffect(() => { reload(); /* eslint-disable-next-line */ }, [token]);

  const update = (k) => (e) => {
    const v = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, [k]: v }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setFeedback(null);
    setLastLink(null);
    if (!form.customer_email || !form.agent_id || !form.level) {
      setFeedback({ type: "error", msg: "Email, agente y nivel son obligatorios." });
      return;
    }
    setSubmitting(true);
    try {
      const body = {
        customer_email: form.customer_email.trim(),
        customer_name: form.customer_name.trim(),
        agent_id: form.agent_id,
        level: form.level,
        send_email: !!form.send_email,
      };
      if (form.days_valid) {
        const n = parseInt(form.days_valid, 10);
        if (Number.isFinite(n) && n > 0) body.days_valid = n;
      }
      const data = await api.post("/admin/access-links", body);
      setLastLink(data.link);
      const emailMsg = data.link.email_status === "sent"
        ? "Email enviado al cliente."
        : data.link.email_status === "failed"
          ? "Atención: el email no se envió. Copia el enlace y mándalo manualmente."
          : "Enlace generado (sin enviar email).";
      setFeedback({
        type: data.link.email_status === "failed" ? "warn" : "ok",
        msg: emailMsg,
      });
      // Reset only customer fields, keep agent + level for chained generation
      setForm((f) => ({ ...f, customer_email: "", customer_name: "" }));
      reload();
    } catch (err) {
      const msg = err?.response?.data?.detail || "No se pudo generar el enlace.";
      setFeedback({ type: "error", msg: typeof msg === "string" ? msg : "Error" });
    } finally {
      setSubmitting(false);
    }
  };

  const copy = async (id, text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(id);
      setTimeout(() => setCopied(""), 1500);
    } catch (e) {
      setFeedback({ type: "warn", msg: "No se pudo copiar. Selecciona el enlace y copia manualmente." });
    }
  };

  const resend = async (id) => {
    try {
      const data = await api.post(`/admin/access-links/${id}/resend`, {});
      const ok = data?.success !== false && data?.email_status === "sent";
      setFeedback({
        type: ok ? "ok" : "warn",
        msg: data?.message || (ok ? "Email reenviado correctamente." : "No se pudo enviar el email. Revisa la configuración SMTP."),
      });
      reload();
    } catch (err) {
      const msg = err?.response?.data?.detail || "No se pudo reenviar el email.";
      setFeedback({ type: "error", msg });
    }
  };

  const revoke = async (id) => {
    if (!window.confirm("¿Revocar este acceso? El cliente dejará de poder usar el enlace.")) return;
    try {
      await api.post(`/admin/access-links/${id}/revoke`, {});
      setFeedback({ type: "ok", msg: "Acceso revocado." });
      reload();
    } catch (err) {
      const msg = err?.response?.data?.detail || "No se pudo revocar.";
      setFeedback({ type: "error", msg });
    }
  };

  const removeFromHistory = async (id) => {
    if (!window.confirm("¿Eliminar el enlace del historial? (No revoca el acceso. Si quieres bloquear, usa Revocar primero.)")) return;
    try {
      await api.del(`/admin/access-links/${id}`);
      setFeedback({ type: "ok", msg: "Eliminado del historial." });
      reload();
    } catch (err) {
      const msg = err?.response?.data?.detail || "No se pudo eliminar.";
      setFeedback({ type: "error", msg });
    }
  };

  return (
    <section className="admin-section" data-testid="admin-access-links">
      <div className="admin-section-head">
        <h2>Regalar acceso a un agente</h2>
        <div className="admin-meta">
          <span className="badge">{history.total} en historial</span>
        </div>
      </div>

      <form className="admin-gift-form" onSubmit={submit} data-testid="admin-gift-form">
        <div className="admin-gift-grid">
          <label>
            Nombre del cliente
            <input
              type="text"
              value={form.customer_name}
              onChange={update("customer_name")}
              placeholder="Ej: María Ruiz"
              data-testid="gift-customer-name"
            />
          </label>
          <label>
            Email del cliente *
            <input
              type="email"
              value={form.customer_email}
              onChange={update("customer_email")}
              placeholder="cliente@email.com"
              required
              data-testid="gift-customer-email"
            />
          </label>
          <label>
            Agente *
            <select value={form.agent_id} onChange={update("agent_id")} data-testid="gift-agent">
              {AGENT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
          <label>
            Nivel *
            <select value={form.level} onChange={update("level")} data-testid="gift-level">
              <option value="demo">Demo (limitado)</option>
              <option value="full">Completo</option>
            </select>
          </label>
          <label>
            Validez en días (opcional)
            <input
              type="number"
              min="1"
              max="3650"
              value={form.days_valid}
              onChange={update("days_valid")}
              placeholder="365 por defecto"
              data-testid="gift-days"
            />
          </label>
          <label className="admin-gift-checkbox">
            <input
              type="checkbox"
              checked={form.send_email}
              onChange={update("send_email")}
              data-testid="gift-send-email"
            />
            <span>Enviar email automáticamente al cliente</span>
          </label>
        </div>
        <div className="admin-gift-actions">
          <button type="submit" disabled={submitting} data-testid="gift-submit">
            {submitting ? "Generando..." : "Generar enlace"}
          </button>
        </div>
      </form>

      {feedback && (
        <div className={`admin-gift-feedback ${feedback.type}`} data-testid="gift-feedback">
          {feedback.msg}
        </div>
      )}

      {lastLink && (
        <div className="admin-gift-last" data-testid="gift-last-link">
          <div className="admin-gift-last-head">
            Enlace generado para <strong>{lastLink.customer_email}</strong>
            <span className="admin-tag">{lastLink.agent_name}</span>
            <span className={`admin-tag ${lastLink.level === "full" ? "admin-tag-ok" : "admin-tag-soft"}`}>
              {lastLink.level === "full" ? "Completo" : "Demo"}
            </span>
          </div>
          <div className="admin-gift-url-row">
            <input
              type="text"
              readOnly
              value={lastLink.url}
              onFocus={(e) => e.target.select()}
              data-testid="gift-last-url"
            />
            <button
              type="button"
              onClick={() => copy(lastLink.id, lastLink.url)}
              data-testid="gift-last-copy"
            >
              {copied === lastLink.id ? "Copiado!" : "Copiar"}
            </button>
          </div>
        </div>
      )}

      <h3 className="admin-gift-history-title">Historial (últimos 50)</h3>
      {loadingHistory ? (
        <div className="admin-loading">Cargando...</div>
      ) : (history.items || []).length === 0 ? (
        <div className="admin-empty">Aún no has generado enlaces manualmente.</div>
      ) : (
        <ul className="admin-list">
          {history.items.map((it) => (
            <li
              key={it.id}
              className={`admin-item ${it.revoked ? "is-revoked" : ""}`}
              data-testid={`gift-item-${it.id}`}
            >
              <div className="admin-item-head">
                <div>
                  <div className="admin-item-title">
                    <strong>{it.customer_name || it.customer_email}</strong>
                    <span className="admin-tag">{it.agent_name}</span>
                    <span className={`admin-tag ${it.level === "full" ? "admin-tag-ok" : "admin-tag-soft"}`}>
                      {it.level === "full" ? "Completo" : "Demo"}
                    </span>
                    {it.revoked
                      ? <span className="admin-tag admin-tag-warn">REVOCADO</span>
                      : it.email_status === "sent"
                        ? <span className="admin-tag admin-tag-ok">Email enviado</span>
                        : it.email_status === "failed"
                          ? <span className="admin-tag admin-tag-warn">Email fallido</span>
                          : <span className="admin-tag admin-tag-soft">Sin email</span>}
                  </div>
                  <div className="admin-item-sub">
                    <a href={`mailto:${it.customer_email}`}>{it.customer_email}</a>
                    {" · "}
                    <span>{new Date(it.created_at).toLocaleString("es-ES")}</span>
                    {it.last_sent_at && (
                      <> · enviado {new Date(it.last_sent_at).toLocaleString("es-ES")}</>
                    )}
                  </div>
                </div>
                <div className="admin-item-actions">
                  <button
                    onClick={() => copy(it.id, it.url)}
                    disabled={it.revoked}
                    data-testid={`gift-copy-${it.id}`}
                  >
                    {copied === it.id ? "Copiado!" : "Copiar enlace"}
                  </button>
                  {!it.revoked && (
                    <button onClick={() => resend(it.id)} data-testid={`gift-resend-${it.id}`}>
                      Reenviar email
                    </button>
                  )}
                  {!it.revoked && (
                    <button
                      className="danger"
                      onClick={() => revoke(it.id)}
                      data-testid={`gift-revoke-${it.id}`}
                    >
                      Revocar
                    </button>
                  )}
                  <button
                    className="danger"
                    onClick={() => removeFromHistory(it.id)}
                    data-testid={`gift-delete-${it.id}`}
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};



