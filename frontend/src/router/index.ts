import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import AuthPage from '../views/AuthPage.vue'
import MapView from '../views/MapView.vue'
import SettlementsView from '../views/SettlementsView.vue'
import SettlementDetailsView from '../views/SettlementDetailsView.vue'
import OCRUploadView from '../views/OCRUploadView.vue'
import AboutUsView from '../views/AboutUsView.vue'
import ContactView from '../views/ContactView.vue'
import LegalView from '../views/LegalView.vue'
import {useAuthStore} from "@/stores/auth.ts";

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
      component: SettlementsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/settlements/:id',
      name: 'settlement-details',
      component: SettlementDetailsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/ocr-upload',
      name: 'ocr-upload',
      component: OCRUploadView,
      meta: { requiresAuth: true }
    },
    {
      path: '/about',
      name: 'about',
      component: AboutUsView
    },
    {
      path: '/contact',
      name: 'contact',
      component: ContactView
    },
    {
      path: '/legal',
      name: 'legal',
      component: LegalView
    },
    {
      path: '/map',
      name: 'map',
      component: MapView,
      meta: { requiresAuth: true }
    },
    {
      path: '/map/:uuid',
      name: 'map-settlement',
      component: MapView,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, _, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({
      name: 'auth',
      query: { redirect: to.fullPath }
    });
  } else {
    next();
  }
});



export default router
