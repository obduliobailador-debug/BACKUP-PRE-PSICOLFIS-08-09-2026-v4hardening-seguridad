import { useCallback, useEffect, useState } from "react";
import { useAdminApi } from "./useAdminApi";

export const AdminReviews = ({ token, onAuthFail }) => {
  const api = useAdminApi(token, onAuthFail);
  const [data, setData] = useState({ items: [], total: 0, pending: 0 });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const reload = async () => {
    setLoading(true);
    try {
      const d = await api.get("/admin/reviews");
      setData(d);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { reload(); /* eslint-disable-next-line */ }, [token]);

  const moderate = async (id, approved) => {
    await api.patch(`/admin/reviews/${id}`, { approved });
    reload();
  };
  const remove = async (id) => {
    if (!window.confirm("¿Eliminar esta reseña permanentemente?")) return;
    await api.del(`/admin/reviews/${id}`);
    reload();
  };

  const filtered = (data.items || []).filter((x) =>
    filter === "all" ? true : filter === "pending" ? !x.approved : !!x.approved
  );

  return (
    <section className="admin-section" data-testid="admin-reviews">
      <div className="admin-section-head">
        <h2>Reseñas</h2>
        <div className="admin-meta">
          <span className="badge">{data.total} en total</span>
          <span className="badge badge-warn">{data.pending} pendientes</span>
        </div>
      </div>
      <div className="admin-filters">
        <button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>Todas</button>
        <button className={filter === "pending" ? "active" : ""} onClick={() => setFilter("pending")}>Pendientes</button>
        <button className={filter === "approved" ? "active" : ""} onClick={() => setFilter("approved")}>Publicadas</button>
      </div>
      {loading ? (
        <div className="admin-loading">Cargando...</div>
      ) : filtered.length === 0 ? (
        <div className="admin-empty">No hay reseñas en este filtro.</div>
      ) : (
        <ul className="admin-list">
          {filtered.map((r) => (
            <li key={r.id} className={`admin-item ${r.approved ? "is-read" : ""}`} data-testid={`review-item-${r.id}`}>
              <div className="admin-item-head">
                <div>
                  <div className="admin-item-title">
                    <strong>{r.author || r.name}</strong>
                    <span className="admin-tag">{"★".repeat(Math.round(r.rating || 5))}</span>
                    {r.role && <span className="admin-tag admin-tag-soft">{r.role}</span>}
                    {r.approved
                      ? <span className="admin-tag admin-tag-ok">PUBLICADA</span>
                      : <span className="admin-tag admin-tag-warn">PENDIENTE</span>}
                  </div>
                  <div className="admin-item-sub">
                    {new Date(r.created_at).toLocaleString("es-ES")}
                  </div>
                </div>
                <div className="admin-item-actions">
                  {r.approved
                    ? <button onClick={() => moderate(r.id, false)}>Despublicar</button>
                    : <button onClick={() => moderate(r.id, true)}>Aprobar</button>}
                  <button className="danger" onClick={() => remove(r.id)}>Eliminar</button>
                </div>
              </div>
              {r.text && <div className="admin-item-body">{r.text}</div>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};



