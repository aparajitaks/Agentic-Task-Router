/**
 * frontend/src/lib/api-client.ts
 *
 * WHY IT EXISTS:
 * Enterprise applications need a centralized HTTP client for consistent request
 * configurations, auth token injection, global error handling, and timeout policies.
 *
 * WHAT IT DOES:
 * Configures an Axios instance with base URLs and interceptors. It intercepts
 * responses to extract the nested `data` envelope we standardized in the backend.
 *
 * HOW IT CONNECTS TO BACKEND:
 * This points directly to the FastAPI backend running at `http://localhost:8000/api/v1`.
 */

import axios from "axios";

// ── API Configuration ────────────────────────────────────────────────────────
// In a production environment, we'd use a real domain. 
// Locally, we default to localhost:8000.
const getBaseURL = () => {
  if (typeof window !== "undefined") {
    // If we're in the browser, and the API URL is not explicitly set,
    // we try to be smart about whether to use localhost or the current hostname.
    const explicitUrl = process.env.NEXT_PUBLIC_API_URL;
    if (explicitUrl) return explicitUrl;

    const hostname = window.location.hostname;
    // If we are accessing via an IP or another hostname, use that instead of localhost
    if (hostname !== "localhost" && hostname !== "127.0.0.1") {
      return `http://${hostname}:8000/api/v1`;
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
};

export const apiClient = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use((config) => {
  console.log(`🚀 [API Request] ${config.method?.toUpperCase()} ${config.url}`, {
    params: config.params,
    headers: config.headers,
    baseURL: config.baseURL
  });
  return config;
});

// Response interceptor to handle our standard backend envelope: { success: true, data: ... }
apiClient.interceptors.response.use(
  (response) => {
    // If the backend wraps responses in a `data` key alongside `success`, unwrap it
    if (response.data && response.data.success !== undefined && response.data.data !== undefined) {
      return response.data.data;
    }
    return response.data;
  },
  (error) => {
    // Global error handling: log exactly what went wrong for easier debugging
    if (error.response) {
      // The server responded with a status code outside the 2xx range
      console.error("API Error Response:", error.response.status, error.response.data);
    } else if (error.request) {
      // The request was made but no response was received (Network Error)
      console.error("API Network Error (No Response):", error.request);
    } else {
      // Something happened in setting up the request
      console.error("API Request Setup Error:", error.message);
    }
    return Promise.reject(error);
  }
);
