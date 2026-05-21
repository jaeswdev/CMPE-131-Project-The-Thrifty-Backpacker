// src/services/api.js
//
// Axios instance configured for our backend API.
//
// Request interceptor:
//   - Attaches Authorization: Bearer <token> from auth store (if logged in)
//   - Attaches X-Tenant-Subdomain header based on localStorage
//
// Response interceptor:
//   - On 401: clears auth + tenant stores, redirects to /login
//   - All other errors propagate to the caller
//
// Usage from any component:
//   import api from '@/services/api'
//   const res = await api.get('/flights/search', { params: { destination: 'London' } })

import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useTenantStore } from '../stores/tenant'
import router from '../router'

const TENANT_SUBDOMAIN_KEY = 'tenant_subdomain'

// Create the Axios instance. Base URL pulled from .env.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 15000,  // 15s — long enough for slow Tipsters responses
  headers: {
    'Content-Type': 'application/json',
  },
})

// === Request interceptor ===
api.interceptors.request.use(
  (config) => {
    // Auth header (only if logged in)
    const auth = useAuthStore()
    if (auth.token) {
      config.headers.Authorization = `Bearer ${auth.token}`
    }

    // Tenant header — read from localStorage so it survives page refreshes.
    // Login flow (T6) sets this when the user enters a tenant subdomain.
    const tenantSubdomain = localStorage.getItem(TENANT_SUBDOMAIN_KEY)
    if (tenantSubdomain) {
      config.headers['X-Tenant-Subdomain'] = tenantSubdomain
    }

    return config
  },
  (error) => Promise.reject(error)
)

// === Response interceptor ===
api.interceptors.response.use(
  (response) => response,  // pass through successful responses
  (error) => {
    // 401 = stale or invalid token. Auto-logout for graceful UX.
    if (error.response?.status === 401) {
      const auth = useAuthStore()
      const tenant = useTenantStore()
      auth.clearSession()
      tenant.clearTenant()
      localStorage.removeItem(TENANT_SUBDOMAIN_KEY)

      // Only redirect if we're not already on /login (avoid redirect loops)
      if (router.currentRoute.value.name !== 'login') {
        router.push({ name: 'login', query: { reason: 'session_expired' } })
      }
    }

    // Re-throw so component-level .catch() blocks can still handle other errors
    return Promise.reject(error)
  }
)

// Helper: write the tenant subdomain on login. Call from LoginView (T6).
export function setTenantSubdomain(subdomain) {
  if (subdomain) {
    localStorage.setItem(TENANT_SUBDOMAIN_KEY, subdomain)
  } else {
    localStorage.removeItem(TENANT_SUBDOMAIN_KEY)
  }
}

export function getTenantSubdomain() {
  return localStorage.getItem(TENANT_SUBDOMAIN_KEY)
}

export default api