import apiClient from './api';

export default {
  // Logowanie
  login(credentials: { username: string; password: string }) {
    return apiClient.post('/auth/login/', credentials);
  },

  // Rejestracja
  register(data: { username: string; email: string; password: string; first_name?: string }) {
    return apiClient.post('/auth/register/', data);
  },

  // Pobranie profilu (opcjonalnie, przyda się później)
  getProfile() {
    return apiClient.get('/auth/me/');
  },

  // Odświeżanie tokena
  refreshToken(refreshToken: string) {
    return apiClient.post('/auth/token/refresh/', { refresh: refreshToken });
  }
};