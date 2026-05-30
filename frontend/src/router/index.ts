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
import TripCalculatorView from '../views/TripCalculatorView.vue'
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
    },
    {
      path: '/trip-calculator',
      name: 'trip-calculator',
      component: TripCalculatorView,
      meta: { requiresAuth: true },
      props: () => ({ settlementId: null, tripId: null }),
    },
    {
      path: '/trip-calculator/:tripId',
      name: 'trip-calculator-edit',
      component: TripCalculatorView,
      meta: { requiresAuth: true },
      props: (r) => ({ settlementId: null, tripId: r.params.tripId as string }),
    },
    {
      path: '/settlements/:id/trip-calculator',
      name: 'settlement-trip-calculator',
      component: TripCalculatorView,
      meta: { requiresAuth: true },
      props: (r) => ({ settlementId: r.params.id as string, tripId: null }),
    },
    {
      path: '/settlements/:id/trip-calculator/:tripId',
      name: 'settlement-trip-calculator-edit',
      component: TripCalculatorView,
      meta: { requiresAuth: true },
      props: (r) => ({ settlementId: r.params.id as string, tripId: r.params.tripId as string }),
    }
  ]
})

router.beforeEach((to, _, next) => {
  const authStore = useAuthStore();

  if (to.path === '/auth' && authStore.isLoggedIn) {
    next({ name: 'home' });
  }
  else if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    if (to.path === '/auth') {
      next();
    } else {
      next({
        name: 'auth',
        query: { redirect: to.fullPath }
      });
    }
  } else {
    next();
  }
});



export default router
