<script setup>
import { ref } from 'vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'
import { useTenantStore } from '../stores/tenant'
import { setTenantSubdomain } from '../services/api'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const tenant = useTenantStore()

// Test state
const status = ref('idle')  // 'idle' | 'loading' | 'success' | 'error'
const errorMessage = ref('')
const sessionExpiredMessage = ref('')

if (route.query.reason === 'session_expired') {
  sessionExpiredMessage.value = 'Your session expired. Please log in again.'
}

async function testLogin() {
  status.value = 'loading'
  errorMessage.value = ''

  // T4 smoke test: hardcoded seed credentials + Tenant A subdomain.
  // T6 will replace this with a real form.
  setTenantSubdomain('agenta')

  try {
    const res = await api.get('/users/login', {
      params: {
        email: 'john.doe@example.com',
        password: 'CMPE-131@2026',
      },
    })

    // Save the session in the auth store
    auth.setSession(res.data.access_token, {
      user_id: res.data.User_ID,
      email: 'john.doe@example.com',
    })

    // Fetch tenant info now that we have a JWT + subdomain
    const tenantRes = await api.get('/tenants/me')
    tenant.setTenant(tenantRes.data)

    status.value = 'success'

    // Navigate to /search
    setTimeout(() => router.push({ name: 'search' }), 800)
  } catch (err) {
    status.value = 'error'
    errorMessage.value = err.response?.data?.detail || err.message || 'Unknown error'
  }
}

function testLogout() {
  auth.clearSession()
  tenant.clearTenant()
  setTenantSubdomain(null)
  status.value = 'idle'
}
</script>

<template>
  <div class="p-8 max-w-xl">
    <h2 class="text-2xl font-bold text-slate-800">Login (T4 smoke test)</h2>
    <p class="mt-2 text-slate-600">
      This is a temporary test page. T6 will replace it with a real form.
    </p>

    <div v-if="sessionExpiredMessage" class="mt-4 p-3 bg-amber-100 text-amber-800 rounded">
      {{ sessionExpiredMessage }}
    </div>

    <div class="mt-6 space-y-3">
      <button
        @click="testLogin"
        :disabled="status === 'loading'"
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {{ status === 'loading' ? 'Logging in…' : 'Test login as John Doe (agenta)' }}
      </button>

      <button
        @click="testLogout"
        class="ml-2 px-4 py-2 bg-slate-200 text-slate-700 rounded hover:bg-slate-300"
      >
        Logout
      </button>
    </div>

    <div v-if="status === 'success'" class="mt-4 p-3 bg-green-100 text-green-800 rounded">
      ✅ Logged in! Redirecting to /search in 800ms…
    </div>

    <div v-if="status === 'error'" class="mt-4 p-3 bg-red-100 text-red-800 rounded">
      ❌ Login failed: {{ errorMessage }}
    </div>

    <div class="mt-6 p-3 bg-slate-100 rounded text-xs">
      <p class="font-bold text-slate-600">Current state:</p>
      <p>auth.isLoggedIn: {{ auth.isLoggedIn }}</p>
      <p>auth.user: {{ JSON.stringify(auth.user) }}</p>
      <p>tenant.tenantName: {{ tenant.tenantName }}</p>
      <p>tenant.brandColor: {{ tenant.brandColor }}</p>
    </div>
  </div>
</template>