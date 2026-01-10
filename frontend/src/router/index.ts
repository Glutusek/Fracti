import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import AuthPage from '../views/AuthPage.vue'
import MapView from '../views/MapView.vue'
import SettlementsView from '../views/SettlementsView.vue'
import SettlementDetailsView from '../views/SettlementDetailsView.vue'
import OCRUploadView from '../views/OCRUploadView.vue'
import AboutUsView from '../views/AboutUsView.vue'
import ContactView from '../views/ContactView.vue'

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

router.beforeEach((to, _from, next) => {

  if (to.meta.requiresAuth) {

    const token = localStorage.getItem('accessToken');


    if (!token) {
      next({ name: 'auth', query: { redirect: to.fullPath } });
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router
