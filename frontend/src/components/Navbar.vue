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

      <button class="hamburger" @click="toggleMobileMenu" :class="{ active: isMobileMenuOpen }">
        <span></span>
        <span></span>
        <span></span>
      </button>

      <div class="nav-right" :class="{ 'mobile-open': isMobileMenuOpen }">
        <template v-if="!authStore.isLoggedIn">
          <router-link to="/about" class="nav-link" @click="closeMobileMenu">O nas</router-link>
          <router-link to="/contact" class="nav-link" @click="closeMobileMenu">Kontakt</router-link>
          <router-link to="/auth" class="nav-link login-btn" @click="closeMobileMenu">Zaloguj się</router-link>
        </template>
        <template v-else>
          <router-link to="/settlements" class="nav-link" @click="closeMobileMenu">Rozliczenia</router-link>
          <router-link to="/trip-calculator" class="nav-link" @click="closeMobileMenu">Kalkulator transportu</router-link>
          <router-link to="/ocr-upload" class="nav-link" @click="closeMobileMenu">Zeskanuj paragon!</router-link>
          <router-link to="/about" class="nav-link" @click="closeMobileMenu">O nas</router-link>
          <router-link to="/contact" class="nav-link" @click="closeMobileMenu">Kontakt</router-link>
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
import { ref } from 'vue'

const router = useRouter()
const authStore = useAuthStore()
const isMobileMenuOpen = ref(false)

const logout = () => {
  authStore.logout()
  router.push('/')
  isMobileMenuOpen.value = false
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
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
  transition: var(--transition-transform);
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
  background: var(--gradient-button);
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
  transition: var(--transition-fast);
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  font-family: inherit;
}

.nav-link:hover {
  color: var(--color-purple);
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--gradient-button);
  transition: var(--transition-normal);
}

.nav-link:hover::after {
  width: 100%;
}

.login-btn {
  padding: 0.5rem 1.5rem;
  background: var(--gradient-button);
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

.hamburger {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  z-index: 1001;
}

.hamburger span {
  width: 25px;
  height: 3px;
  background: #e5e7eb;
  border-radius: 3px;
  transition: var(--transition-normal);
}

.hamburger.active span:nth-child(1) {
  transform: rotate(45deg) translate(8px, 8px);
}

.hamburger.active span:nth-child(2) {
  opacity: 0;
}

.hamburger.active span:nth-child(3) {
  transform: rotate(-45deg) translate(7px, -7px);
}

@media (max-width: 768px) {
  .hamburger {
    display: flex;
  }

  .nav-right {
    position: fixed;
    top: 73px;
    right: -100%;
    width: 100%;
    height: calc(100vh - 73px);
    background: rgba(17, 24, 39, 0.98);
    backdrop-filter: blur(10px);
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    padding: var(--spacing-lg);
    transition: var(--transition-normal);
    border-left: 1px solid rgba(139, 92, 246, 0.2);
  }

  .nav-right.mobile-open {
    right: 0;
  }

  .nav-link {
    padding: 1rem;
    text-align: center;
    border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  }

  .nav-link::after {
    display: none;
  }

  .login-btn,
  .logout-btn {
    margin-top: 1rem;
  }
}
</style>
