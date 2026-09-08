import { useEffect } from "react";

/**
 * Inject Google Analytics 4 once, when REACT_APP_GA4_ID is provided.
 * No-op if the id is missing (safe default for preview / local dev).
 */
export const useGA4 = () => {
  useEffect(() => {
    const GA_ID = process.env.REACT_APP_GA4_ID;
    if (!GA_ID) return;
    if (window.__ga4_loaded) return;
    window.__ga4_loaded = true;
    const s = document.createElement('script');
    s.async = true;
    s.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    function gtag(){ window.dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('config', GA_ID, { anonymize_ip: true });
  }, []);
};
