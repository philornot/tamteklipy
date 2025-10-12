/**
 * Helper do budowania URL dla API i plików
 * W produkcji używa relatywnych URL, w dev — localhost:8000
 */

const getBaseUrl = () => {
  return import.meta.env.PROD ? "" : "http://localhost:8000";
};

const getApiUrl = (path) => {
  const base = getBaseUrl();
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${cleanPath}`;
};

// Helper do dodawania tokenu do URL
const addTokenToUrl = (url) => {
  const token = localStorage.getItem("access_token");
  if (!token) return url;

  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}token=${token}`;
};

// Konkretne helpery dla plików
const getThumbnailUrl = (clipId) => {
  const url = getApiUrl(`/api/files/thumbnails/${clipId}`);
  return addTokenToUrl(url);
};

const getStreamUrl = (clipId) => {
  const url = getApiUrl(`/api/files/stream/${clipId}`);
  return addTokenToUrl(url);
};

const getDownloadUrl = (clipId) => {
  const url = getApiUrl(`/api/files/download/${clipId}`);
  return addTokenToUrl(url);
};

const getAwardIconUrl = (iconPath) => {
  const url = getApiUrl(iconPath);
  return addTokenToUrl(url);
};

// Named export dla api.js
export { getBaseUrl as default };

// Export wszystkich funkcji
export {
  getBaseUrl,
  getApiUrl,
  getThumbnailUrl,
  getStreamUrl,
  getDownloadUrl,
  getAwardIconUrl,
  addTokenToUrl,
};
