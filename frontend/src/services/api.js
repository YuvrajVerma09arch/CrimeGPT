import axios from "axios";

// VITE_API_URL semantics: unset -> local dev backend; empty string -> same
// origin (production behind nginx, which proxies /api/ to the backend).
export const BASE_URL =
  (import.meta.env.VITE_API_URL ?? "http://localhost:8000") + "/api/v1";

export const ACCESS_TOKEN_KEY = "crimegpt_access_token";
export const REFRESH_TOKEN_KEY = "crimegpt_refresh_token";

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const lang = localStorage.getItem("language");
  if (lang) config.headers["Accept-Language"] = lang;
  return config;
});

// Single in-flight refresh shared by all 401-ed requests
let refreshPromise = null;

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) throw new Error("No refresh token");
  const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
    refresh_token: refreshToken,
  });
  localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
  return data.access_token;
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const isAuthUrl =
      original?.url?.includes("/auth/login") ||
      original?.url?.includes("/auth/refresh");

    if (status === 401 && original && !original._retry && !isAuthUrl) {
      original._retry = true;
      try {
        refreshPromise = refreshPromise || refreshAccessToken();
        const token = await refreshPromise;
        refreshPromise = null;
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      } catch (refreshError) {
        refreshPromise = null;
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        if (window.location.pathname !== "/login") {
          window.location.assign("/login");
        }
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export function saveBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export default api;
