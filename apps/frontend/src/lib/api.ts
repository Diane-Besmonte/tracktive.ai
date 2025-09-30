import axios from "axios";
import { getToken, clearToken } from "./storage";

export const API_BASE = import.meta.env.VITE_API_URL;

const api = axios.create({ baseURL: API_BASE });

api.defaults.headers.common["Accept"] = "application/json";
api.defaults.headers.post["Content-Type"] = "application/json";

api.interceptors.request.use((config) => {
    const token = getToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

api.interceptors.response.use(
    (res) => res,
    (err) => {
        const status = err?.response?.status;
        if (status == 401) {
            clearToken();

            if (location.pathname !== "/login") location.replace("/login");
        }
        return Promise.reject(err)
    }
);

export default api;