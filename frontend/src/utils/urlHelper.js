/**
 * Helper do budowania URL dla API i plików
 * W produkcji używa relatywnych URL, w dev — localhost:8000
 */

const getBaseUrl = () => {
  return import.meta.env.PROD ? "" : "http://localhost:8000";
};

const getApiUrl = (path) => {
  const base = getBaseUrl();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
};

// Konkretne helpery dla plików
const getThumbnailUrl = (clipId) => {
  return getApiUrl(`/api/files/thumbnails/${clipId}`);
};

const getStreamUrl = (clipId) => {
  return getApiUrl(`/api/files/stream/${clipId}`);
};

const getDownloadUrl = (clipId) => {
  return getApiUrl(`/api/files/download/${clipId}`);
};

const getAwardIconUrl = (iconPath) => {
  // iconPath już zawiera pełną ścieżkę np. /api/admin/award-types/{id}/icon
  return getApiUrl(iconPath);
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
  getAwardIconUrl
};