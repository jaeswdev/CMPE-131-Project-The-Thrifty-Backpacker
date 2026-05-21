<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api, { setTenantSubdomain } from '../services/api'
import { useAuthStore } from '../stores/auth'
import { useTenantStore } from '../stores/tenant'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const tenant = useTenantStore()

// === Form state ===
const email = ref('')
const password = ref('')
const tenantSubdomain = ref('agenta')  // default for convenience during testing

// === UI state ===
const status = ref('idle')  // 'idle' | 'loading' | 'error'
const errorMessage = ref('')

// === Session-expired banner from query param ===
const sessionExpired = computed(() => route.query.reason === 'session_expired')

// === Client-side validation ===
const validationError = computed(() => {
  if (!email.value.trim()) return 'Email is required'
  if (!email.value.includes('@')) return 'Please enter a valid email'
  if (!password.value) return 'Password is required'
  if (password.value.length < 8) return 'Password must be at least 8 characters'
  if (!tenantSubdomain.value.trim()) return 'Tenant ID is required'
  return null
})

const canSubmit = computed(() => !validationError.value && status.value !== 'loading')

// === Submit handler ===
async function handleLogin() {
  // Belt-and-suspenders: validate once more on submit (in case of stale state)
  if (validationError.value) {
    errorMessage.value = validationError.value
    status.value = 'error'
    return
  }

  status.value = 'loading'
  errorMessage.value = ''

  // Set tenant header BEFORE the login call (so backend resolves the right tenant)
  setTenantSubdomain(tenantSubdomain.value.trim())

  try {
    // Step 1: login → get JWT
    const loginRes = await api.get('/users/login', {
      params: {
        email: email.value.trim(),
        password: password.value,
      },
    })
    auth.setSession(loginRes.data.access_token, {
      user_id: loginRes.data.User_ID,
      email: email.value.trim(),
    })

    // Step 2: fetch tenant info (header carries our new JWT automatically)
    const tenantRes = await api.get('/tenants/me')
    tenant.setTenant(tenantRes.data)

    // Step 3: redirect to /search
    router.push({ name: 'search' })
  } catch (err) {
    status.value = 'error'

    // Friendly error mapping — translate API responses to human messages
    const statusCode = err.response?.status
    if (statusCode === 401) {
      errorMessage.value = 'Invalid email or password.'
    } else if (statusCode === 400) {
      errorMessage.value = 'Unknown tenant. Check the Tenant ID and try again.'
    } else if (err.code === 'ECONNABORTED') {
      errorMessage.value = 'Request timed out. Is the backend running?'
    } else if (!err.response) {
      errorMessage.value = 'Could not reach the backend. Is it running on :8000?'
    } else {
      errorMessage.value = err.response?.data?.detail || 'Login failed. Please try again.'
    }

    // Clear stored tenant since login failed
    setTenantSubdomain(null)
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-8">
    <h2 class="text-2xl font-bold text-slate-800">Log In</h2>
    <p class="mt-1 text-sm text-slate-600">
      Sign in to plan your trip within your budget.
    </p>

    <!-- Session-expired banner -->
    <div v-if="sessionExpired" class="mt-4 p-3 bg-amber-100 text-amber-800 rounded text-sm">
      Your session expired. Please log in again.
    </div>

    <!-- Login form -->
    <form @submit.prevent="handleLogin" class="mt-6 space-y-4">
      <div>
        <label for="email" class="block text-sm font-medium text-slate-700">
          Email
        </label>
        <input
          id="email"
          v-model="email"
          type="email"
          autocomplete="email"
          required
          placeholder="you@example.com"
          class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label for="password" class="block text-sm font-medium text-slate-700">
          Password
        </label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
          minlength="8"
          placeholder="At least 8 characters"
          class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label for="tenant" class="block text-sm font-medium text-slate-700">
          Tenant ID
          <span class="text-xs text-slate-500 font-normal">(your travel agency)</span>
        </label>
        <input
          id="tenant"
          v-model="tenantSubdomain"
          type="text"
          autocomplete="organization"
          required
          placeholder="e.g. agenta"
          class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p class="mt-1 text-xs text-slate-500">
          For testing: try <code class="bg-slate-100 px-1 rounded">agenta</code>,
          <code class="bg-slate-100 px-1 rounded">agentb</code>, or
          <code class="bg-slate-100 px-1 rounded">agentc</code>.
        </p>
      </div>

      <!-- Error display -->
      <div v-if="status === 'error' && errorMessage" class="p-3 bg-red-100 text-red-800 rounded text-sm">
        {{ errorMessage }}
      </div>

      <!-- Submit button -->
      <button
        type="submit"
        :disabled="!canSubmit"
        class="w-full py-2 px-4 rounded-md text-white font-medium
               bg-blue-600 hover:bg-blue-700
               disabled:bg-slate-300 disabled:cursor-not-allowed
               transition"
      >
        {{ status === 'loading' ? 'Signing in…' : 'Sign in' }}
      </button>
    </form>

    <p class="mt-6 text-sm text-slate-600 text-center">
      Don't have an account?
      <RouterLink to="/signup" class="text-blue-600 hover:underline font-medium">
        Sign up
      </RouterLink>
    </p>
  </div>
</template>