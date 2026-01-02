import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosError } from 'axios';

// Tworzymy instancję axios
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api', // Używamy zmiennej środowiskowej
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: Automatyczne dodawanie tokena do każdego zapytania
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Pobieramy token z localStorage (nazwa klucza musi być spójna z auth.ts)
    const token = localStorage.getItem('accessToken');

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Interceptor: Obsługa błędów (np. 401 - wylogowanie)
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
      // Opcjonalnie: Tu można dodać logikę wylogowania
      console.warn('Błąd 401: Brak dostępu lub token wygasł.');
    }
    return Promise.reject(error);
  }
);

export default apiClient;