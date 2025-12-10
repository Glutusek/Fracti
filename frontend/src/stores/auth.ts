import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // State
  const isLoggedIn = ref(false)
  const user = ref<{ name: string; email: string } | null>(null)

  // Actions
  const login = (userData: { name: string; email: string }) => {
    isLoggedIn.value = true
    user.value = userData
    // Store in localStorage for persistence
    localStorage.setItem('isLoggedIn', 'true')
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const logout = () => {
    isLoggedIn.value = false
    user.value = null
    localStorage.removeItem('isLoggedIn')
    localStorage.removeItem('user')
  }

  const checkAuth = () => {
    const savedAuth = localStorage.getItem('isLoggedIn')
    const savedUser = localStorage.getItem('user')

    if (savedAuth === 'true' && savedUser) {
      isLoggedIn.value = true
      user.value = JSON.parse(savedUser)
    }
  }

  // Initialize auth state on store creation
  checkAuth()

  return {
    isLoggedIn,
    user,
    login,
    logout,
    checkAuth
  }
})
