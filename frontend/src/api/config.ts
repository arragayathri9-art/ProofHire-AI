const rawBaseUrl =
  (import.meta.env.VITE_API_BASE_URL as string) ||
  (import.meta.env.PROD
    ? 'https://proofhire-ai.onrender.com'
    : 'http://localhost:8000');

export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '');

export default API_BASE_URL;

