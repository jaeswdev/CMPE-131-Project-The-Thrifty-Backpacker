
// Vue Router setup. Defines all top-level routes and a navigation guard
// that redirects to /login when no JWT is present in localStorage.
//
// Routes:
//   /         → redirect to /search (default landing page)
//   /login    → LoginView (PUBLIC, no auth required)
//   /signup   → SignupView (PUBLIC)
//   /search   → SearchView (requires auth)
//   /results  → ResultsView (requires auth)
//   /dashboard → DashboardView (requires auth)

import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/search',
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/signup',
    name: 'signup',
    component: () => import('../views/SignupView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('../views/SearchView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/results',
    name: 'results',
    component: () => import('../views/ResultsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard: redirect to /login if a protected route is accessed without a JWT.
// We read the token directly from localStorage here because the Pinia auth store
// (T3) doesn't exist yet. T3 will refactor this to use the store.
router.beforeEach((to, from, next) => {
  const requiresAuth = to.meta.requiresAuth
  const hasToken = !!localStorage.getItem('access_token')

  if (requiresAuth && !hasToken) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router