// Base URL of the HealStation API.
// Empty (the default) means same origin: the Vite dev server proxies /api to
// the backend, and in production the backend serves this app itself.
// Set VITE_API_BASE_URL at build time only when the API lives elsewhere.
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

export const apiUrl = (path) => `${API_BASE_URL}${path}`;

// Opens an external link without giving the new page access to this one.
export const openExternal = (url) => window.open(url, '_blank', 'noopener,noreferrer');
