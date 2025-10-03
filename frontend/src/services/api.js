import axios from "axios";

// Base URL z env variable lub fallback
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
