import axios from "axios";

// Sprawdź czy jest produkcja (po zbudowaniu import.meta.env.PROD będzie true)
const API_BASE_URL = import.meta.env.PROD
  ? "https://www.tamteklipy.pl"  // Produkcja - twarda wartość
  : "http://localhost:8000";      // Development

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - dodaj JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const reqUrl = error.config?.url || "";
      const isLoginRequest = reqUrl.includes("/auth/login");
      const onLoginPage = typeof window !== "undefined" && window.location?.pathname?.startsWith("/login");

      // Wyczyść tokeny (zawsze przy 401)
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");

      // Nie przeładowuj, jeśli:
      // - błąd dotyczy samego logowania (chcemy pokazać komunikat na /login)
      // - już jesteśmy na stronie logowania (unikaj zbędnego reloadu)
      if (!isLoginRequest && !onLoginPage) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
