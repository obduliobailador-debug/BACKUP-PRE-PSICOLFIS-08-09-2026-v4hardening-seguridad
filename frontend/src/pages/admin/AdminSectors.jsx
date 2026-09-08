import { useCallback, useEffect, useState } from "react";
import { useAdminApi } from "./useAdminApi";

const emptySector = () => ({
  slug: "",
  name: "",
  icon: "",
  tagline: "",
  headline: "",
  description: "",
  problem: "",
  solution: "",
  ideal_for: "",
  demo_intro: "",
  use_cases: [""],
  metrics: [{ label: "", value: "" }],
  deployment_id: "",
  hidden: false,
});

export const AdminSectors = ({ token, onAuthFail }) => {
  const api = useAdminApi(token, onAuthFail);
  const [data, setData] = useState({ items: [], active: 0, hidden: 0, trash: 0 });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("active");
  const [editor, setEditor] = useState(null); // {mode:'new'|'edit', original:{}, form:{}}
  const [feedback, setFeedback] = useState(null);

  const reload = async () => {
    setLoading(true);
    try {
      const d = await api.get("/admin/sectors");
      setData(d);
    } finally { setLoading(false); }
  };
  useEffect(() => { reload(); /* eslint-disable-next-line */ }, [token]);

  const filtered = (data.items || []).filter((s) => {
    if (filter === "active") return !s.hidden && !s.deleted_at;
    if (filter === "hidden") return s.hidden && !s.deleted_at;
    if (filter === "trash")  return !!s.deleted_at;
    return true;
  });

  const openNew = () => setEditor({ mode: "new", original: null, form: emptySector() });
  const openEdit = (s) => setEditor({ mode: "edit", original: s, form: {
    slug: s.slug, name: s.name, icon: s.icon || "", tagline: s.tagline || "",
    headline: s.headline || "", description: s.description || "",
    problem: s.problem || "", solution: s.solution || "",
    ideal_for: s.ideal_for || "", demo_intro: s.demo_intro || "",
    use_cases: (s.use_cases && s.use_cases.length ? s.use_cases : [""]),
    metrics: (s.metrics && s.metrics.length ? s.metrics : [{ label: "", value: "" }]),
    deployment_id: s.deployment_id || "",
    hidden: !!s.hidden,
  }});
  const closeEditor = () => setEditor(null);

  const save = async () => {
    if (!editor) return;
    const f = editor.form;
    const body = {
      ...f,
      use_cases: (f.use_cases || []).filter((x) => x && x.trim()),
      metrics: (f.metrics || []).filter((m) => m.label && m.value),
    };
    try {
      if (editor.mode === "new") {
        await api.post("/admin/sectors", body);
        setFeedback({ type: "ok", msg: "Sector creado correctamente." });
      } else {
        await api.patch(`/admin/sectors/${editor.original.slug}`, body);
        setFeedback({ type: "ok", msg: "Sector actualizado." });
      }
      closeEditor();
      reload();
    } catch (err) {
      const msg = err?.response?.data?.detail || "No se pudo guardar el sector.";
      setFeedback({ type: "error", msg });
    }
  };

  const toggleVisibility = async (s) => {
    try {
      await api.post(`/admin/sectors/${s.slug}/visibility`, { hidden: !s.hidden });
      reload();
    } catch (err) {
      setFeedback({ type: "error", msg: err?.response?.data?.detail || "Error al cambiar visibilidad." });
    }
  };
  const trashSector = async (s) => {
    if (!window.confirm(`¿Mover "${s.name}" a la papelera? Podrás restaurarlo durante 30 días.`)) return;
    try { await api.del(`/admin/sectors/${s.slug}`); reload(); }
    catch (err) { setFeedback({ type: "error", msg: err?.response?.data?.detail || "Error." }); }
  };
  const restore = async (s) => {
    try { await api.post(`/admin/sectors/${s.slug}/restore`, {}); reload(); }
    catch (err) { setFeedback({ type: "error", msg: err?.response?.data?.detail || "Error." }); }
  };
  const hardDelete = async (s) => {
    if (!window.confirm(`Eliminar "${s.name}" PERMANENTEMENTE. Esta acción no se puede deshacer.`)) return;
    try { await api.del(`/admin/sectors/${s.slug}/permanent`); reload(); }
    catch (err) { setFeedback({ type: "error", msg: err?.response?.data?.detail || "Error." }); }
  };

  return (
    <section className="admin-section" data-testid="admin-sectors">
      <div className="admin-section-head">
        <h2>Sectores</h2>
        <div className="admin-meta">
          <span className="badge">{data.active} activos</span>
          <span className="badge badge-warn">{data.hidden} ocultos</span>
          <span className="badge">{data.trash} en papelera</span>
        </div>
      </div>
      <div className="admin-filters">
        <button className={filter === "active" ? "active" : ""} onClick={() => setFilter("active")}>Activos</button>
        <button className={filter === "hidden" ? "active" : ""} onClick={() => setFilter("hidden")}>Ocultos</button>
        <button className={filter === "trash" ? "active" : ""} onClick={() => setFilter("trash")}>Papelera</button>
        <button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>Todos</button>
        <button className="admin-primary" onClick={openNew} data-testid="admin-sector-new">+ Nuevo sector</button>
      </div>

      {feedback && (
        <div className={`admin-gift-feedback ${feedback.type}`} data-testid="sector-feedback">{feedback.msg}</div>
      )}

      {loading ? (
        <div className="admin-loading">Cargando...</div>
      ) : filtered.length === 0 ? (
        <div className="admin-empty">No hay sectores en este filtro.</div>
      ) : (
        <ul className="admin-list">
          {filtered.map((s) => (
            <li key={s.slug} className={`admin-item ${s.hidden ? "is-hidden-sector" : ""} ${s.deleted_at ? "is-trashed" : ""}`} data-testid={`sector-item-${s.slug}`}>
              <div className="admin-item-head">
                <div>
                  <div className="admin-item-title">
                    <strong>{s.name}</strong>
                    <span className="admin-tag admin-tag-soft">/{s.slug}</span>
                    {s.deployment_id
                      ? <span className="admin-tag admin-tag-ok">Demo configurada</span>
                      : <span className="admin-tag admin-tag-warn">Sin Pickaxe</span>}
                    {s.hidden && <span className="admin-tag admin-tag-warn">OCULTO</span>}
                    {s.deleted_at && <span className="admin-tag admin-tag-warn">EN PAPELERA</span>}
                  </div>
                  <div className="admin-item-sub">{s.tagline}</div>
                </div>
                <div className="admin-item-actions">
                  {!s.deleted_at && (
                    <>
                      <button onClick={() => openEdit(s)} data-testid={`sector-edit-${s.slug}`}>Editar</button>
                      <button onClick={() => toggleVisibility(s)} data-testid={`sector-toggle-${s.slug}`}>
                        {s.hidden ? "Mostrar" : "Ocultar"}
                      </button>
                      <button className="danger" onClick={() => trashSector(s)} data-testid={`sector-trash-${s.slug}`}>
                        A papelera
                      </button>
                    </>
                  )}
                  {s.deleted_at && (
                    <>
                      <button onClick={() => restore(s)} data-testid={`sector-restore-${s.slug}`}>Restaurar</button>
                      <button className="danger" onClick={() => hardDelete(s)} data-testid={`sector-hard-${s.slug}`}>
                        Eliminar definitivamente
                      </button>
                    </>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {editor && (
        <SectorEditorModal
          mode={editor.mode}
          form={editor.form}
          setForm={(f) => setEditor({ ...editor, form: f })}
          onClose={closeEditor}
          onSave={save}
        />
      )}
    </section>
  );
};

const SectorEditorModal = ({ mode, form, setForm, onClose, onSave }) => {
  const upd = (k) => (e) => setForm({ ...form, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const updList = (k, i, v) => {
    const arr = [...(form[k] || [])]; arr[i] = v; setForm({ ...form, [k]: arr });
  };
  const addToList = (k, empty) => setForm({ ...form, [k]: [...(form[k] || []), empty] });
  const removeFromList = (k, i) => {
    const arr = [...(form[k] || [])]; arr.splice(i, 1); setForm({ ...form, [k]: arr });
  };

  return (
    <div className="budget-modal-overlay" onClick={onClose}>
      <div className="budget-modal admin-sector-modal" onClick={(e) => e.stopPropagation()} data-testid="sector-editor-modal">
        <button className="budget-modal-close" onClick={onClose} aria-label="Cerrar">✕</button>
        <h2>{mode === "new" ? "Nuevo sector" : `Editar · ${form.name}`}</h2>

        <div className="admin-gift-grid">
          <label>Slug (URL) * <input type="text" value={form.slug} onChange={upd("slug")} placeholder="ej: gimnasios" data-testid="sector-form-slug" /></label>
          <label>Nombre * <input type="text" value={form.name} onChange={upd("name")} placeholder="ej: Gimnasios y centros fitness" data-testid="sector-form-name" /></label>
          <label>Icono (id) <input type="text" value={form.icon} onChange={upd("icon")} placeholder="ej: dumbbell" /></label>
          <label>Deployment ID Pickaxe <input type="text" value={form.deployment_id} onChange={upd("deployment_id")} placeholder="UUID de Pickaxe" data-testid="sector-form-deployment" /></label>
        </div>

        <label className="admin-modal-full">Tagline <input type="text" value={form.tagline} onChange={upd("tagline")} placeholder="Frase corta para tarjeta" /></label>
        <label className="admin-modal-full">Headline <input type="text" value={form.headline} onChange={upd("headline")} placeholder="Título grande del hero" /></label>
        <label className="admin-modal-full">Descripción <textarea rows={3} value={form.description} onChange={upd("description")} /></label>
        <label className="admin-modal-full">Problema <textarea rows={3} value={form.problem} onChange={upd("problem")} /></label>
        <label className="admin-modal-full">Solución <textarea rows={3} value={form.solution} onChange={upd("solution")} /></label>
        <label className="admin-modal-full">Ideal para <input type="text" value={form.ideal_for} onChange={upd("ideal_for")} /></label>
        <label className="admin-modal-full">Intro de demo <input type="text" value={form.demo_intro} onChange={upd("demo_intro")} /></label>

        <div className="admin-modal-sub">
          <h4>Casos de uso</h4>
          {(form.use_cases || []).map((uc, i) => (
            <div key={i} className="admin-list-row">
              <input type="text" value={uc} onChange={(e) => updList("use_cases", i, e.target.value)} placeholder={`Caso de uso #${i+1}`} />
              <button type="button" className="danger" onClick={() => removeFromList("use_cases", i)}>×</button>
            </div>
          ))}
          <button type="button" onClick={() => addToList("use_cases", "")}>+ Añadir caso de uso</button>
        </div>

        <div className="admin-modal-sub">
          <h4>Métricas</h4>
          {(form.metrics || []).map((m, i) => (
            <div key={i} className="admin-list-row">
              <input type="text" value={m.label} onChange={(e) => updList("metrics", i, { ...m, label: e.target.value })} placeholder="Etiqueta (ej: Reservas fuera de horario)" />
              <input type="text" value={m.value} onChange={(e) => updList("metrics", i, { ...m, value: e.target.value })} placeholder="Valor (ej: +35%)" />
              <button type="button" className="danger" onClick={() => removeFromList("metrics", i)}>×</button>
            </div>
          ))}
          <button type="button" onClick={() => addToList("metrics", { label: "", value: "" })}>+ Añadir métrica</button>
        </div>

        <label className="admin-modal-full admin-gift-checkbox">
          <input type="checkbox" checked={!!form.hidden} onChange={upd("hidden")} />
          <span>Ocultar sector (no aparecerá en /soluciones ni en el Home)</span>
        </label>

        <div className="admin-modal-footer">
          <button onClick={onClose}>Cancelar</button>
          <button className="admin-primary" onClick={onSave} data-testid="sector-form-save">
            {mode === "new" ? "Crear sector" : "Guardar cambios"}
          </button>
        </div>
      </div>
    </div>
  );
};


