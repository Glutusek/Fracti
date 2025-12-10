<template>
  <nav class="navbar">
    <div class="nav-container">
      <div class="nav-left">
        <router-link to="/" class="logo-link">

            <img
            :src="logoSrc"
            class="logo"
            alt="Fracti Logo"
            width="40"
            height="40"
          />
          <span class="logo-text">Fracti</span>
        </router-link>
      </div>

      <div class="nav-right">
        <template v-if="!authStore.isLoggedIn">
          <router-link to="/#about" class="nav-link">O nas</router-link>
          <router-link to="/#contact" class="nav-link">Kontakt</router-link>
          <router-link to="/auth" class="nav-link login-btn">Zaloguj się</router-link>
        </template>
        <template v-else>
          <router-link to="/expenses" class="nav-link">Rozliczenia</router-link>
          <router-link to="/ocr" class="nav-link">Paragony</router-link>
          <router-link to="/map" class="nav-link">Mapa</router-link>
          <button @click="logout" class="nav-link logout-btn">Wyloguj</button>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import logoSrc from '@/assets/fracti_logo.svg'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const logout = () => {
  authStore.logout()
  router.push('/')
}
</script>

<style scoped>
.navbar {
  background: rgba(17, 24, 39, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-left {
  display: flex;
  align-items: center;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  transition: transform 0.2s;
}

.logo-link:hover {
  transform: scale(1.05);
}

.logo {
  filter: drop-shadow(0 0 8px rgba(139, 92, 246, 0.5));
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.nav-link {
  color: #e5e7eb;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  font-family: inherit;
}

.nav-link:hover {
  color: #8b5cf6;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #8b5cf6, #6366f1);
  transition: width 0.3s;
}

.nav-link:hover::after {
  width: 100%;
}

.login-btn {
  padding: 0.5rem 1.5rem;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border-radius: 8px;
  -webkit-text-fill-color: white;
  color: white;
}

.login-btn::after {
  display: none;
}

.login-btn:hover {
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.6);
  transform: translateY(-2px);
  color: white;
}

.logout-btn {
  padding: 0.5rem 1.5rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #ef4444;
}

.logout-btn::after {
  display: none;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
}
</style>
