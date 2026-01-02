import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import authService from '@/services/auth.service';

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'));
  const username = ref<string | null>(localStorage.getItem('username'));

  const isLoggedIn = computed(() => !!accessToken.value);

  const login = async (credentials: { username: string; password: string }) => {
    try {
      // ZMIANA: używamy authService zamiast api
      const response = await authService.login(credentials);

      // Zakładam, że backend zwraca { access: "...", refresh: "..." }
      const { access, refresh } = response.data;

      accessToken.value = access;
      username.value = credentials.username;

      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);
      localStorage.setItem('username', credentials.username);

      return true;
    } catch (error) {
      console.error("Błąd logowania w Store:", error);
      throw error;
    }
  };

  const logout = () => {
    accessToken.value = null;
    username.value = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('username');
  };

  return { accessToken, username, isLoggedIn, login, logout };
});