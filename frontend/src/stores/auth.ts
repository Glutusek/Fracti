import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import authService from '@/services/auth.service';

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'));
  const username = ref<string | null>(localStorage.getItem('username'));
  const email = ref<string | null>(localStorage.getItem('email'));
  const firstName = ref<string | null>(localStorage.getItem('firstName'));
  const lastName = ref<string | null>(localStorage.getItem('lastName'));

  const isLoggedIn = computed(() => !!accessToken.value);

  const login = async (credentials: { username: string; password: string }) => {
    try {
      const response = await authService.login(credentials);

      const { access, refresh } = response.data;

      accessToken.value = access;
      username.value = credentials.username;

      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);
      localStorage.setItem('username', credentials.username);

      // Pobierz profil użytkownika zaraz po zalogowaniu i zapisz w stanie/localStorage
      try {
        const profileResp = await authService.getProfile();
        const profile = profileResp.data;
        email.value = profile.email ?? null;
        firstName.value = profile.first_name ?? null;
        lastName.value = profile.last_name ?? null;
        if (profile.email) localStorage.setItem('email', profile.email);
        if (profile.first_name) localStorage.setItem('firstName', profile.first_name);
        if (profile.last_name) localStorage.setItem('lastName', profile.last_name);
      } catch (err) {
        console.warn('Nie udało się pobrać profilu po logowaniu', err);
      }

      return true;
    } catch (error) {
      console.error("Błąd logowania w Store:", error);
      throw error;
    }
  };

  const logout = () => {
    accessToken.value = null;
    username.value = null;
    email.value = null;
    firstName.value = null;
    lastName.value = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('username');
    localStorage.removeItem('email');
    localStorage.removeItem('firstName');
    localStorage.removeItem('lastName');
  };

  return { accessToken, username, email, firstName, lastName, isLoggedIn, login, logout };
});