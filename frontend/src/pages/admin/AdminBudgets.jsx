import { useCallback, useEffect, useState } from "react";
import { useAdminApi } from "./useAdminApi";

export const AdminBudgets = ({ token, onAuthFail }) => {
  const api = useAdminApi(token, onAuthFail);
  const [data, setData] = useState({ items: [], total: 0, unread: 0 });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [expanded, setExpanded] = useState({});

  const reload = async () => {
    setLoading(true);
    try {
      const d = await api.get("/admin/budget-requests");
      setData(d);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { reload(); /* eslint-disable-next-line */ }, [token]);

  const toggleRead = async (id, current) => {
    await api.patch(`/admin/budget-requests/${id}`, { read: !current });
    reload();
  };

  const removeBudget = async (id) => {
    if (!window.confirm("¿Eliminar esta solicitud permanentemente?")) return;
    await api.del(`/admin/budget-requests/${id}`);
    reload();
  };

  const filtered = (data.items || []).filter((x) =>
    filter === "all" ? true : filter === "unread" ? !x.read : !!x.read
  );

  return (
    <section className="admin-section" data-testid="admin-budgets">
      <div className="admin-section-head">
        <h2>Solicitudes de presupuesto</h2>
        <div className="admin-meta">
          <span className="badge">{data.total} en total</span>
          <span className="badge badge-warn">{data.unread} sin leer</span>
        </div>
      </div>
      <div className="admin-filters">
        <button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>Todas</button>
        <button className={filter === "unread" ? "active" : ""} onClick={() => setFilter("unread")}>Sin leer</button>
        <button className={filter === "read" ? "active" : ""} onClick={() => setFilter("read")}>Leídas</button>
      </div>
      {loading ? (
        <div className="admin-loading">Cargando...</div>
      ) : filtered.length === 0 ? (
        <div className="admin-empty">No hay solicitudes en este filtro.</div>
      ) : (
        <ul className="admin-list">
          {filtered.map((b) => (
            <li key={b.id} className={`admin-item ${b.read ? "is-read" : ""}`} data-testid={`budget-item-${b.id}`}>
              <div className="admin-item-head">
                <div>
                  <div className="admin-item-title">
                    <strong>{b.nombre}</strong>
                    <span className="admin-tag">{b.plan}</span>
                    {b.agente && <span className="admin-tag admin-tag-soft">{b.agente}</span>}
                    {!b.read && <span className="admin-tag admin-tag-warn">NUEVO</span>}
                  </div>
                  <div className="admin-item-sub">
                    <a href={`mailto:${b.email}`}>{b.email}</a>
                    {b.telefono && <> · <a href={`tel:${b.telefono}`}>{b.telefono}</a></>}
                    {" · "}
                    <span>{new Date(b.created_at).toLocaleString("es-ES")}</span>
                  </div>
                </div>
                <div className="admin-item-actions">
                  <button onClick={() => setExpanded((s) => ({ ...s, [b.id]: !s[b.id] }))}>
                    {expanded[b.id] ? "Ocultar" : "Ver"}
                  </button>
                  <button onClick={() => toggleRead(b.id, b.read)}>
                    {b.read ? "Marcar no leída" : "Marcar leída"}
                  </button>
                  <a className="btn-link" href={`mailto:${b.email}?subject=Re:%20Tu%20solicitud%20PSICOLFIS.NET`}>
                    Responder
                  </a>
                  <button className="danger" onClick={() => removeBudget(b.id)}>
                    Eliminar
                  </button>
                </div>
              </div>
              {expanded[b.id] && b.mensaje && (
                <div className="admin-item-body">{b.mensaje}</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

