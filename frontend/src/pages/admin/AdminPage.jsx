import { useEffect, useState } from "react";
import axios from "axios";
import { API, ADMIN_TOKEN_KEY } from "../../api";
import { usePageSeo } from "../../lib/seo";
import { AdminLogin } from "./AdminLogin";
import { AdminBudgets } from "./AdminBudgets";
import { AdminReviews } from "./AdminReviews";
import { AdminAccessLinks } from "./AdminAccessLinks";
import { AdminSectors } from "./AdminSectors";


export const AdminPage = () => {
  const [token, setToken] = useState(() => localStorage.getItem(ADMIN_TOKEN_KEY) || "");
  const [tab, setTab] = useState("budgets");

  useEffect(() => {
    document.title = "Panel · PSICOLFIS.NET";
  }, []);

  const handleLogout = () => {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    setToken("");
  };

  if (!token) {
    return <AdminLogin onLogin={(t) => { localStorage.setItem(ADMIN_TOKEN_KEY, t); setToken(t); }} />;
  }

  return (
    <div className="admin-shell" data-testid="admin-shell">
      <header className="admin-header">
        <a href="/" className="admin-brand">PSICOLFIS.NET <span>· Panel</span></a>
        <nav className="admin-tabs">
          <button
            className={`admin-tab ${tab === "budgets" ? "active" : ""}`}
            onClick={() => setTab("budgets")}
            data-testid="admin-tab-budgets"
          >
            Presupuestos
          </button>
          <button
            className={`admin-tab ${tab === "reviews" ? "active" : ""}`}
            onClick={() => setTab("reviews")}
            data-testid="admin-tab-reviews"
          >
            Reseñas
          </button>
          <button
            className={`admin-tab ${tab === "gift" ? "active" : ""}`}
            onClick={() => setTab("gift")}
            data-testid="admin-tab-gift"
          >
            Regalar acceso
          </button>
          <button
            className={`admin-tab ${tab === "sectors" ? "active" : ""}`}
            onClick={() => setTab("sectors")}
            data-testid="admin-tab-sectors"
          >
            Sectores
          </button>
        </nav>
        <button className="admin-logout" onClick={handleLogout} data-testid="admin-logout">
          Cerrar sesión
        </button>
      </header>
      <main className="admin-main">
        {tab === "budgets" && <AdminBudgets token={token} onAuthFail={handleLogout} />}
        {tab === "reviews" && <AdminReviews token={token} onAuthFail={handleLogout} />}
        {tab === "gift" && <AdminAccessLinks token={token} onAuthFail={handleLogout} />}
        {tab === "sectors" && <AdminSectors token={token} onAuthFail={handleLogout} />}
      </main>
    </div>
  );
};

