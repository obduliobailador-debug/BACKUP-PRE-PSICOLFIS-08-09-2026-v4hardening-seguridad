import { useState } from "react";
import axios from "axios";
import { API } from "../../api";

export const AdminLogin = ({ onLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { data } = await axios.post(`${API}/admin/login`, { email, password });
      onLogin(data.token);
    } catch (err) {
      const msg = err?.response?.data?.detail || "No se pudo iniciar sesión";
      setError(typeof msg === "string" ? msg : "Error de validación");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-page" data-testid="admin-login-page">
      <form className="admin-login-card" onSubmit={submit}>
        <h1>Panel PSICOLFIS.NET</h1>
        <p>Acceso restringido</p>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
            data-testid="admin-login-email"
          />
        </label>
        <label>
          Contraseña
          <div className="admin-pwd-wrap">
            <input
              type={showPwd ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              data-testid="admin-login-password"
            />
            <button
              type="button"
              className="admin-pwd-toggle"
              onClick={() => setShowPwd((v) => !v)}
              aria-label={showPwd ? "Ocultar contraseña" : "Mostrar contraseña"}
              data-testid="admin-login-toggle-pwd"
            >
              {showPwd ? "Ocultar" : "Mostrar"}
            </button>
          </div>
        </label>
        {error && <div className="admin-login-error" data-testid="admin-login-error">{error}</div>}
        <button type="submit" disabled={loading} data-testid="admin-login-submit">
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
};

