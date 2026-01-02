import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import AuthPage from '../views/AuthPage.vue'
import MapView from '../views/MapView.vue'
import SettlementsView from '../views/SettlementsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: LandingPage
    },
    {
      path: '/auth',
      name: 'auth',
      component: AuthPage
    },
    {
      path: '/settlements',
      name: 'settlements',
      component: SettlementsView
    },
    {
      path: '/map',
      name: 'map',
      component: MapView
    },
    {
      path: '/map/:uuid',
      name: 'map-settlement',
      component: MapView
    }
  ]
})

export default router
