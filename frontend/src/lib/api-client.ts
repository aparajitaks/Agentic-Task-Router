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

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
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
    // Global error handling can be done here (e.g., token refresh logic, toasts)
    return Promise.reject(error);
  }
);
