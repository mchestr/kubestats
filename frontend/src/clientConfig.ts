import type { CreateClientConfig } from "./client/client.gen"

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseUrl: import.meta.env.VITE_API_BASE_URL,
  headers: {
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  },
  onErrorCaptured: () => {
    // Handle 401/403 errors by redirecting to login
    if (window.location.pathname !== "/login") {
      localStorage.removeItem("access_token")
      window.location.href = "/login"
    }
  },
})
