import type { CreateClientConfig } from './client/client.gen';

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});
