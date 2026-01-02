import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import AuthPage from '../views/AuthPage.vue'
import MapView from '../views/MapView.vue'
import SettlementsView from '../views/SettlementsView.vue'
import SettlementDetailsView from '../views/SettlementDetailsView.vue'
import OCRUploadView from '../views/OCRUploadView.vue'

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
      path: '/settlements/:id',
      name: 'settlement-details',
      component: SettlementDetailsView
    },
    {
      path: '/ocr-upload',
      name: 'ocr-upload',
      component: OCRUploadView
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
