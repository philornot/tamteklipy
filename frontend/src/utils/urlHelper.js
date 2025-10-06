/**
 * Helper do budowania URL dla API i plików
 * W produkcji używa relatywnych URL, w dev — localhost:8000
 */

export const getBaseUrl = () => {
  return import.meta.env.PROD ? "" : "http://localhost:8000";
};

export const getApiUrl = (path) => {
  const base = getBaseUrl();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
};

// Konkretne helpery dla plików
export const getThumbnailUrl = (clipId) => {
  return getApiUrl(`/api/files/thumbnails/${clipId}`);
};

export const getStreamUrl = (clipId) => {
  return getApiUrl(`/api/files/stream/${clipId}`);
};

export const getDownloadUrl = (clipId) => {
  return getApiUrl(`/api/files/download/${clipId}`);
};

export const getAwardIconUrl = (iconPath) => {
  // iconPath już zawiera /api/admin/award-types/{id}/icon
  return getApiUrl(iconPath);
};

export default {
  getApiUrl,
  getThumbnailUrl,
  getStreamUrl,
  getDownloadUrl,
  getAwardIconUrl
};