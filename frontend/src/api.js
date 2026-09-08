/**
 * Central API constants used by every page/hook.
 *
 * BACKEND_URL is exposed via CRA's REACT_APP_* env variable so it can differ
 * per environment (local vs preview vs production). All fetches go through
 * `/api/...` so the ingress in K8s routes them to the FastAPI backend.
 */
export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Stripe payment links per agent + level, sourced from env so they can be
// rotated without a redeploy.
export const AGENT_STRIPE_URLS = {
  iris: process.env.REACT_APP_STRIPE_DEMO_IRIS,
  alex: process.env.REACT_APP_STRIPE_DEMO_ALEX,
  umbral: process.env.REACT_APP_STRIPE_DEMO_UMBRAL,
};

export const AGENT_STRIPE_URLS_FULL = {
  iris: process.env.REACT_APP_STRIPE_FULL_IRIS,
  alex: process.env.REACT_APP_STRIPE_FULL_ALEX,
  umbral: process.env.REACT_APP_STRIPE_FULL_UMBRAL,
};

export const ADMIN_TOKEN_KEY = "psicolfis_admin_token";
