<template>
  <div class="auth-page">

    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h1>{{ isLogin ? 'Zaloguj się' : 'Utwórz konto' }}</h1>
          <p>{{ isLogin ? 'Witaj ponownie!' : 'Rozpocznij zarządzanie wydatkami' }}</p>
        </div>

        <form @submit.prevent="handleSubmit" class="auth-form">
          <div class="form-group">
            <label for="username">Login</label>
            <input
              id="username"
              v-model="formData.username"
              type="text"
              placeholder="Login"
              required
            />
          </div>

          <div v-if="!isLogin" class="form-group">
            <label for="email">Email</label>
            <input
              id=""
              v-model="formData.email"
              type="text"
              placeholder="Email"
              :required="!isLogin"
            />
          </div>

          <div class="form-group">
            <label for="password">Hasło</label>
            <input
              id="password"
              v-model="formData.password"
              type="password"
              placeholder="••••••••"
              required
            />
          </div>

          <div v-if="!isLogin" class="form-group">
            <label for="confirmPassword">Potwierdź hasło</label>
            <input
              id="confirmPassword"
              v-model="formData.confirmPassword"
              type="password"
              placeholder="••••••••"
              :required="!isLogin"
            />
          </div>

          <div v-if="errorMsg" class="error-message">
            {{ errorMsg }}
          </div>

          <button type="submit" class="submit-button" :disabled="isLoading">
            <span v-if="isLoading">Przetwarzanie...</span>
            <span v-else>{{ isLogin ? 'Zaloguj się' : 'Utwórz konto' }}</span>
          </button>
        </form>

        <div class="auth-footer">
          <button @click="toggleMode" class="toggle-button">
            {{ isLogin ? 'Nie masz konta? Zarejestruj się' : 'Masz już konto? Zaloguj się' }}
          </button>
        </div>
      </div>

      <div class="auth-background">
        <div class="gradient-orb orb-1"></div>
        <div class="gradient-orb orb-2"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../services/auth.service' // Importujemy API do rejestracji (jeśli store tego nie ma)

const router = useRouter()
const authStore = useAuthStore()

const isLogin = ref(true)
const isLoading = ref(false) // Blokada przycisku
const errorMsg = ref('')     // Wyświetlanie błędów

// Dane formularza
const formData = reactive({
  username: '',   // Wymagane przez Django
  email: '',
  password: '',
  confirmPassword: ''
})

const toggleMode = () => {
  isLogin.value = !isLogin.value
  errorMsg.value = '' // Czyścimy błędy przy przełączaniu
  // Reset hasła dla bezpieczeństwa
  formData.password = ''
  formData.confirmPassword = ''
}

const handleSubmit = async () => {
  errorMsg.value = ''
  isLoading.value = true

  try {
    if (isLogin.value) {
      // --- LOGIKA LOGOWANIA ---
      // Używamy naszego Store'a, który gada z API i zapisuje token
      await authStore.login({
        username: formData.username,
        password: formData.password
      })

      // Jak nie wywaliło błędu, to znaczy że sukces -> idziemy na mapę
      router.push('/')

    } else {
      // --- LOGIKA REJESTRACJI ---
      if (formData.password !== formData.confirmPassword) {
        throw new Error('Hasła nie są identyczne!')
      }

      // Tu zakładamy, że w api.ts dodamy metodę register,
      // albo użyjemy generycznego post.
      // Django wymaga zazwyczaj: username i password.
      await api.register({
         username: formData.username,
         email: formData.email,
         password: formData.password,
      })

      // Po udanej rejestracji od razu logujemy użytkownika
      await authStore.login({
        username: formData.username,
        password: formData.password
      })

      router.push('/')
    }

  } catch (err: any) {
    console.error("Błąd auth:", err)
    // Obsługa błędów z backendu (np. "Brak konta" lub "Złe hasło")
    if (err.response && err.response.status === 401) {
      errorMsg.value = "Nieprawidłowy login lub hasło."
    } else if (err.message) {
      errorMsg.value = err.message
    } else {
      errorMsg.value = "Wystąpił błąd połączenia. Spróbuj ponownie."
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* --- TWOJE STYLE POZOSTAJĄ BEZ ZMIAN --- */
/* Wklej tutaj cały swój CSS, który mi pokazałeś. */
/* Jedyne co dodajemy to klasa dla komunikatu błędu: */

.error-message {
  color: #ff6b6b;
  font-size: 0.9rem;
  text-align: center;
  background: rgba(255, 107, 107, 0.1);
  padding: 0.5rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 107, 107, 0.3);
}

.submit-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  filter: grayscale(0.5);
}

/* ... Reszta Twojego CSS (auth-page, gradienty itd.) ... */
.auth-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
}
/* ... (wklej resztę stylów z Twojego pliku) ... */
.auth-container {
  min-height: calc(100vh - 80px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
}

.auth-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.3;
  animation: float 15s infinite ease-in-out;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
  top: -150px;
  right: -100px;
}

.orb-2 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, #6366f1 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
  animation-delay: -7s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(30px, -30px);
  }
}

.auth-card {
  position: relative;
  z-index: 1;
  background: rgba(17, 24, 39, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 24px;
  padding: 3rem;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.auth-header h1 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #ffffff 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.auth-header p {
  color: #9ca3af;
  font-size: 1rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: #e5e7eb;
  font-weight: 500;
  font-size: 0.95rem;
}

.form-group input {
  padding: 0.875rem 1rem;
  background: rgba(30, 27, 75, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 12px;
  color: #e5e7eb;
  font-size: 1rem;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.6);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.form-group input::placeholder {
  color: #6b7280;
}

.submit-button {
  padding: 1rem;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 0.5rem;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(139, 92, 246, 0.4);
}

.submit-button:active {
  transform: translateY(0);
}

.auth-footer {
  margin-top: 2rem;
  text-align: center;
  padding-top: 2rem;
  border-top: 1px solid rgba(139, 92, 246, 0.2);
}

.toggle-button {
  background: none;
  border: none;
  color: #8b5cf6;
  font-size: 0.95rem;
  cursor: pointer;
  transition: color 0.2s;
}

.toggle-button:hover {
  color: #a78bfa;
  text-decoration: underline;
}

@media (max-width: 640px) {
  .auth-card {
    padding: 2rem;
  }

  .auth-header h1 {
    font-size: 1.75rem;
  }
}
</style>