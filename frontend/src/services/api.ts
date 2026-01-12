import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosError } from 'axios';
import router from "@/router";
import { useAuthStore } from '@/stores/auth';

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

// Flaga zapobiegająca wielokrotnemu odświeżaniu tokena
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Interceptor: Obsługa błędów (np. 401 - odświeżanie tokena lub wylogowanie)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Jeśli otrzymamy błąd 401 (Unauthorized) z backendu
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Jeśli token jest właśnie odświeżany, dodaj żądanie do kolejki
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refreshToken');

      if (!refreshToken) {
        // Brak refresh tokena - wyloguj użytkownika
        isRefreshing = false;
        const authStore = useAuthStore();
        authStore.logout();
        await router.push({ path: '/auth', query: { redirect: router.currentRoute.value.fullPath } });
        return Promise.reject(error);
      }

      try {
        // Próba odświeżenia tokena
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/auth/token/refresh/`,
          { refresh: refreshToken }
        );

        const { access } = response.data;

        // Zapisz nowy access token
        localStorage.setItem('accessToken', access);
        const authStore = useAuthStore();
        authStore.accessToken = access;

        // Zaktualizuj nagłówek Authorization w oryginalnym żądaniu
        originalRequest.headers.Authorization = `Bearer ${access}`;

        // Przetwórz kolejkę oczekujących żądań
        processQueue(null, access);
        isRefreshing = false;

        // Ponów oryginalne żądanie
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Odświeżenie tokena nie powiodło się - wyloguj użytkownika
        processQueue(refreshError, null);
        isRefreshing = false;

        const authStore = useAuthStore();
        authStore.logout();
        await router.push({ path: '/auth', query: { redirect: router.currentRoute.value.fullPath } });

        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
export default apiClient;