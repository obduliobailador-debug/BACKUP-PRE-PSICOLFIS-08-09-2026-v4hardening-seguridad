/**
 * SEO helpers: per-route <title>, description, canonical, robots and JSON-LD.
 *
 * We mutate the document head directly instead of adding a heavy dep like
 * react-helmet because the site only has a handful of routes.
 */
import { useEffect } from "react";

export const setMetaTag = (selector, attr, value) => {
  let tag = document.head.querySelector(selector);
  if (!tag) {
    tag = document.createElement('meta');
    const [name, val] = selector.replace(/^meta\[|\]$/g, '').split('=');
    tag.setAttribute(name, val.replace(/['"]/g, ''));
    document.head.appendChild(tag);
  }
  tag.setAttribute(attr, value);
};

// Inject / replace a JSON-LD script with a stable id (so we can swap it per route)
export const setJsonLd = (id, data) => {
  let el = document.getElementById(id);
  if (!el) {
    el = document.createElement('script');
    el.type = 'application/ld+json';
    el.id = id;
    document.head.appendChild(el);
  }
  el.textContent = JSON.stringify(data);
};

export const usePageSeo = ({ title, description, canonicalPath, noindex = false }) => {
  useEffect(() => {
    if (title) document.title = title;
    if (description) {
      setMetaTag('meta[name="description"]', 'content', description);
      setMetaTag('meta[property="og:description"]', 'content', description);
      setMetaTag('meta[name="twitter:description"]', 'content', description);
    }
    if (title) {
      setMetaTag('meta[property="og:title"]', 'content', title);
      setMetaTag('meta[name="twitter:title"]', 'content', title);
    }
    if (canonicalPath) {
      const baseUrl = process.env.REACT_APP_PUBLIC_BASE_URL || 'https://psicolfis.net';
      let link = document.head.querySelector('link[rel="canonical"]');
      if (!link) {
        link = document.createElement('link');
        link.setAttribute('rel', 'canonical');
        document.head.appendChild(link);
      }
      link.setAttribute('href', `${baseUrl}${canonicalPath}`);
      setMetaTag('meta[property="og:url"]', 'content', `${baseUrl}${canonicalPath}`);
    }
    setMetaTag(
      'meta[name="robots"]',
      'content',
      noindex ? 'noindex, nofollow' : 'index, follow, max-image-preview:large, max-snippet:-1'
    );
  }, [title, description, canonicalPath, noindex]);
};
