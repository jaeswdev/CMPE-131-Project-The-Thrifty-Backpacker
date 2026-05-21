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

const status = ref('idle')
const errorMessage = ref('')
const sessionExpiredMessage = ref('')

if (route.query.reason === 'session_expired') {
  sessionExpiredMessage.value = 'Your session expired. Please log in again.'
}

// === Smoke-test helper: logs in as the seed user for the given tenant ===
async function loginAsSeed(subdomain, email = 'john.doe@example.com', password = 'CMPE-131@2026') {
  status.value = 'loading'
  errorMessage.value = ''
  setTenantSubdomain(subdomain)

  try {
    const res = await api.get('/users/login', { params: { email, password } })
    auth.setSession(res.data.access_token, {
      user_id: res.data.User_ID,
      email,
    })

    const tenantRes = await api.get('/tenants/me')
    tenant.setTenant(tenantRes.data)

    status.value = 'success'
    setTimeout(() => router.push({ name: 'search' }), 500)
  } catch (err) {
    status.value = 'error'
    errorMessage.value = err.response?.data?.detail || err.message || 'Unknown error'
  }
}
</script>

<template>
  <div class="max-w-md">
    <h2 class="text-2xl font-bold text-slate-800">Login</h2>
    <p class="mt-2 text-slate-600">
      Temporary smoke-test login (T6 will replace with a real form).
      <br/>
      Try different tenants to see the header re-brand.
    </p>

    <div v-if="sessionExpiredMessage" class="mt-4 p-3 bg-amber-100 text-amber-800 rounded">
      {{ sessionExpiredMessage }}
    </div>

    <div class="mt-6 flex flex-col gap-2">
      <button
        @click="loginAsSeed('agenta')"
        :disabled="status === 'loading'"
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 font-medium"
      >
        Login as Tenant A (Travel Agency A) — blue
      </button>
      <button
        @click="loginAsSeed('agentb')"
        :disabled="status === 'loading'"
        class="px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50 font-medium"
      >
        Login as Tenant B (Travel Agency B) — green
      </button>
      <button
        @click="loginAsSeed('agentc')"
        :disabled="status === 'loading'"
        class="px-4 py-2 bg-slate-600 text-white rounded hover:bg-slate-700 disabled:opacity-50 font-medium"
      >
        Login as Tenant C (no theme) — default gray
      </button>
    </div>

    <div v-if="status === 'success'" class="mt-4 p-3 bg-green-100 text-green-800 rounded">
      ✅ Logged in! Redirecting to /search…
    </div>

    <div v-if="status === 'error'" class="mt-4 p-3 bg-red-100 text-red-800 rounded">
      ❌ Login failed: {{ errorMessage }}
    </div>
  </div>
</template>