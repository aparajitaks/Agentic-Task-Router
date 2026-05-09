/**
 * frontend/src/lib/api-client.ts
 *
 * WHY IT EXISTS:
 * A centralized Axios instance that automatically injects auth headers on
 * every request. This is the correct place to manage auth — not inside
 * individual components.
 *
 * AUTH STRATEGY:
 * We use a custom `x-clerk-id` header in development. The interceptor reads
 * the current user ID from the Zustand auth store and attaches it to every
 * outgoing request automatically.
 *
 * PRODUCTION MIGRATION PATH:
 * When real Clerk JWT tokens are integrated, replace the x-clerk-id injection
 * below with: `config.headers.Authorization = `Bearer ${await getToken()}`
 */

import axios from "axios";

// ── API Base URL ─────────────────────────────────────────────────────────────
// Reads from NEXT_PUBLIC_API_URL. If not set, detects the current hostname
// so that requests work whether you're on localhost or a network IP.
const getBaseURL = (): string => {
  if (typeof window !== "undefined") {
    const explicitUrl = process.env.NEXT_PUBLIC_API_URL;
    if (explicitUrl) return explicitUrl;

    const { hostname } = window.location;
    if (hostname !== "localhost" && hostname !== "127.0.0.1") {
      return `http://${hostname}:8000/api/v1`;
    }
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
};

// ── Axios Instance ───────────────────────────────────────────────────────────
export const apiClient = axios.create({
  baseURL: getBaseURL(),
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request Interceptor: Auto-inject auth header ─────────────────────────────
// WHY THIS IS THE CORRECT PATTERN:
// Components should NEVER manually construct auth headers. The interceptor
// acts as a single source of truth for identity propagation.
apiClient.interceptors.request.use((config) => {
  // Lazily import to avoid circular dependency and SSR issues.
  // The store is only read client-side at request time.
  if (typeof window !== "undefined") {
    try {
      // Read current user from the Zustand auth store.
      // This avoids requiring a React component context (hooks) at this level.
      const authStorage = localStorage.getItem("auth-storage");
      if (authStorage) {
        const { state } = JSON.parse(authStorage);
        const clerkId = state?.user?.id;
        if (clerkId) {
          config.headers["x-clerk-id"] = clerkId;
        }
      }
    } catch {
      // If localStorage is unavailable or parsing fails, fail silently.
      // The backend dev-bypass will handle missing headers in development.
    }
  }

  console.debug(
    `🚀 [API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`,
    { headers: { "x-clerk-id": config.headers["x-clerk-id"] ?? "(missing)" } }
  );

  return config;
});

// ── Response Interceptor: Unwrap standard envelope + log errors ──────────────
// Backend wraps all responses as: { success: true, data: { ... } }
// This interceptor transparently unwraps `data` so callers just get the payload.
apiClient.interceptors.response.use(
  (response) => {
    if (
      response.data &&
      response.data.success !== undefined &&
      response.data.data !== undefined
    ) {
      return response.data.data;
    }
    return response.data;
  },
  (error) => {
    if (error.response) {
      // Server responded with a 4xx/5xx.
      // Extract the user-readable message from our standard envelope.
      const backendMessage =
        error.response.data?.error?.message ||
        error.response.data?.detail ||
        error.response.data?.message ||
        `HTTP ${error.response.status}`;

      console.error(
        `❌ [API Error] ${error.response.status} on ${error.config?.url}: ${backendMessage}`
      );

      // Attach a clean message to the error so catch blocks can use it
      error.userMessage = backendMessage;
    } else if (error.request) {
      // Request was sent but no response received.
      // After our middleware fix, this should only happen if the container is
      // actually down or there's a real network issue.
      console.error(
        `🔌 [Network Error] No response received for ${error.config?.url}. ` +
        `Backend may be down or CORS is blocking the preflight.`
      );
      error.userMessage = "Cannot reach the backend. Is the server running?";
    } else {
      console.error("⚠️ [Request Error]", error.message);
      error.userMessage = error.message;
    }
    return Promise.reject(error);
  }
);
