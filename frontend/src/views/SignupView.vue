<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api, { setTenantSubdomain } from '../services/api'
import { useAuthStore } from '../stores/auth'
import { useTenantStore } from '../stores/tenant'

const router = useRouter()
const auth = useAuthStore()
const tenant = useTenantStore()

// === Form state ===
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const phoneNumber = ref('')
const password = ref('')
const tenantId = ref(1)             // default to Tenant A (matches DB seed)
const tenantSubdomain = ref('agenta') // for setting the X-Tenant-Subdomain header on follow-up calls

// === UI state ===
const status = ref('idle')  // 'idle' | 'loading' | 'error'
const errorMessage = ref('')

// === Client-side validation ===
const validationError = computed(() => {
  if (!firstName.value.trim()) return 'First name is required'
  if (!lastName.value.trim()) return 'Last name is required'
  if (!email.value.trim()) return 'Email is required'
  if (!email.value.includes('@')) return 'Please enter a valid email'
  if (!password.value) return 'Password is required'
  if (password.value.length < 8) return 'Password must be at least 8 characters'
  if (!tenantId.value || tenantId.value < 1) return 'Tenant ID must be 1 or higher'
  if (!tenantSubdomain.value.trim()) return 'Tenant subdomain is required'
  return null
})

const canSubmit = computed(() => !validationError.value && status.value !== 'loading')

// === Submit handler ===
async function handleSignup() {
  if (validationError.value) {
    errorMessage.value = validationError.value
    status.value = 'error'
    return
  }

  status.value = 'loading'
  errorMessage.value = ''

  // Set X-Tenant-Subdomain header so subsequent /tenants/me succeeds
  setTenantSubdomain(tenantSubdomain.value.trim())

  try {
    // Step 1: Create the user via POST /users/signup
    const signupRes = await api.post('/users/signup', {
      First_Name: firstName.value.trim(),
      Last_Name: lastName.value.trim(),
      Email: email.value.trim(),
      Phone_Number: phoneNumber.value.trim() || null,  // optional field
      Tenant_ID: Number(tenantId.value),
      Password: password.value,
    })

    // Step 2: Auto-login with the returned JWT
    auth.setSession(signupRes.data.access_token, {
      user_id: signupRes.data.User_ID,
      email: email.value.trim(),
    })

    // Step 3: Fetch tenant info to apply branding
    const tenantRes = await api.get('/tenants/me')
    tenant.setTenant(tenantRes.data)

    // Step 4: Off to search
    router.push({ name: 'search' })
  } catch (err) {
    status.value = 'error'
    const statusCode = err.response?.status

    if (statusCode === 409) {
      errorMessage.value = 'An account with this email already exists. Try logging in instead.'
    } else if (statusCode === 422) {
      // FastAPI validation errors come as an array of {loc, msg, type}
      const detail = err.response?.data?.detail
      if (Array.isArray(detail) && detail.length > 0) {
        const firstError = detail[0]
        const field = firstError.loc?.[firstError.loc.length - 1] || 'field'
        errorMessage.value = `${field}: ${firstError.msg}`
      } else {
        errorMessage.value = 'Some fields are invalid. Please check your input.'
      }
    } else if (statusCode === 400) {
      errorMessage.value = 'Unknown tenant. Check the Tenant subdomain and try again.'
    } else if (err.code === 'ECONNABORTED') {
      errorMessage.value = 'Request timed out. Is the backend running?'
    } else if (!err.response) {
      errorMessage.value = 'Could not reach the backend. Is it running on :8000?'
    } else {
      errorMessage.value = err.response?.data?.detail || 'Signup failed. Please try again.'
    }

    setTenantSubdomain(null)
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-8">
    <h2 class="text-2xl font-bold text-slate-800">Create your account</h2>
    <p class="mt-1 text-sm text-slate-600">
      Sign up to start planning your trip.
    </p>

    <form @submit.prevent="handleSignup" class="mt-6 space-y-4">
      <!-- Name fields (two columns on wider screens) -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label for="firstName" class="block text-sm font-medium text-slate-700">
            First name
          </label>
          <input
            id="firstName"
            v-model="firstName"
            type="text"
            autocomplete="given-name"
            required
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label for="lastName" class="block text-sm font-medium text-slate-700">
            Last name
          </label>
          <input
            id="lastName"
            v-model="lastName"
            type="text"
            autocomplete="family-name"
            required
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

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
        <label for="phone" class="block text-sm font-medium text-slate-700">
          Phone number <span class="text-xs text-slate-500 font-normal">(optional)</span>
        </label>
        <input
          id="phone"
          v-model="phoneNumber"
          type="tel"
          autocomplete="tel"
          placeholder="+1 555 123 4567"
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
          autocomplete="new-password"
          required
          minlength="8"
          placeholder="At least 8 characters"
          class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <!-- Tenant assignment: ID + subdomain side-by-side -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label for="tenantId" class="block text-sm font-medium text-slate-700">
            Tenant ID
          </label>
          <input
            id="tenantId"
            v-model.number="tenantId"
            type="number"
            min="1"
            required
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label for="tenantSubdomain" class="block text-sm font-medium text-slate-700">
            Tenant subdomain
          </label>
          <input
            id="tenantSubdomain"
            v-model="tenantSubdomain"
            type="text"
            autocomplete="organization"
            required
            placeholder="agenta"
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
      <p class="text-xs text-slate-500 -mt-2">
        Both fields must match the agency you're signing up under. Defaults to Tenant A.
      </p>

      <!-- Error display -->
      <div v-if="status === 'error' && errorMessage" class="p-3 bg-red-100 text-red-800 rounded text-sm">
        {{ errorMessage }}
      </div>

      <!-- Submit -->
      <button
        type="submit"
        :disabled="!canSubmit"
        class="w-full py-2 px-4 rounded-md text-white font-medium
               bg-blue-600 hover:bg-blue-700
               disabled:bg-slate-300 disabled:cursor-not-allowed
               transition"
      >
        {{ status === 'loading' ? 'Creating account…' : 'Sign up' }}
      </button>
    </form>

    <p class="mt-6 text-sm text-slate-600 text-center">
      Already have an account?
      <RouterLink to="/login" class="text-blue-600 hover:underline font-medium">
        Log in
      </RouterLink>
    </p>
  </div>
</template>