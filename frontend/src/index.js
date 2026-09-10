import React from "react";
import ReactDOM from "react-dom/client";
// Self-hosted variable fonts (bundled locally, no external/CDN requests).
// Only the weight (wght) axis, normal style — no italics.
import "@fontsource-variable/inter/wght.css";
import "@fontsource-variable/manrope/wght.css";
import "@/index.css";
import App from "@/App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
