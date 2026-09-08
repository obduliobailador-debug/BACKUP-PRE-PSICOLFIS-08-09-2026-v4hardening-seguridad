import "@/App.css";
import { useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { useGA4 } from "./hooks/useGA4";
import { AgentesPage } from "./pages/AgentesPage";
import { CancelPage } from "./pages/CancelPage";
import { Home } from "./pages/Home";
import { LegalPage } from "./pages/LegalPage";
import { MiAgentePage } from "./pages/MiAgentePage";
import { SectorPage } from "./pages/SectorPage";
import { SolucionesIndexPage } from "./pages/SolucionesIndexPage";
import { SuccessPage } from "./pages/SuccessPage";
import { AdminPage } from "./pages/admin/AdminPage";

/**
 * Thin router entrypoint. Each route lazily reads its own hooks (SEO, GA4,
 * scroll reveals) inside its page component, keeping this file free of
 * business logic.
 */
function App() {
  useGA4();
  useEffect(() => {
    // Runtime-set CSS variables for legacy background images. Doing this via
    // JS (instead of CSS url()) avoids webpack's css-loader trying to resolve
    // absolute paths as JS modules during compilation.
    const root = document.documentElement.style;
    root.setProperty('--bg-dorado', "url('/images/legacy/fondo-psicolfis-dorado.jpg')");
    root.setProperty('--bg-sectors', "url('/images/legacy/fondo-web-sectores.jpg')");
  }, []);
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/agentes" element={<AgentesPage />} />
        <Route path="/soluciones" element={<SolucionesIndexPage />} />
        <Route path="/soluciones/:slug" element={<SectorPage />} />
        <Route path="/success" element={<SuccessPage />} />
        <Route path="/cancel" element={<CancelPage />} />
        <Route path="/legal" element={<LegalPage />} />
        <Route path="/mi-agente/:token" element={<MiAgentePage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
