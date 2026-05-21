<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useTenantStore } from '../stores/tenant'
import { setTenantSubdomain } from '../services/api'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const tenant = useTenantStore()
const router = useRouter()

// === Computed: pick readable text color based on brand color brightness ===
// Standard luminance formula. Returns 'light' or 'dark'.
// If brand bg is dark (low luminance), use light text; vice versa.
const textColor = computed(() => {
  const hex = tenant.brandColor.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  // Perceived brightness — see https://www.w3.org/TR/AERT/#color-contrast
  const brightness = (r * 299 + g * 587 + b * 114) / 1000
  return brightness > 155 ? 'text-slate-900' : 'text-white'
})

// === Logout handler ===
function handleLogout() {
  auth.clearSession()
  tenant.clearTenant()
  setTenantSubdomain(null)
  router.push({ name: 'login' })
}
</script>

<template>
  <header
    class="shadow-sm sticky top-0 z-50"
    :style="{ backgroundColor: 'var(--color-brand)' }"
  >
    <div
      class="max-w-6xl mx-auto px-4 py-3 flex items-center gap-6"
      :class="textColor"
    >
      <!-- === Tenant brand: logo + name === -->
      <RouterLink :to="auth.isLoggedIn ? '/search' : '/login'" class="flex items-center gap-3 hover:opacity-90">
        <!-- Logo: render if URL exists, otherwise fallback to text -->
        <img
          v-if="tenant.logoUrl"
          :src="tenant.logoUrl"
          :alt="tenant.tenantName"
          class="h-8 w-auto"
          @error="$event.target.style.display = 'none'"
        />
        <div class="flex flex-col">
          <span class="text-base font-bold leading-tight">{{ tenant.tenantName }}</span>
          <span v-if="tenant.info" class="text-xs opacity-75 leading-tight">
            powered by The Thrifty Backpacker
          </span>
        </div>
      </RouterLink>

      <!-- === Nav links (only when logged in) === -->
      <nav v-if="auth.isLoggedIn" class="flex items-center gap-4 text-sm font-medium">
        <RouterLink
          to="/search"
          class="px-2 py-1 rounded hover:bg-white/15 transition"
          active-class="bg-white/20"
        >
          Search
        </RouterLink>
        <RouterLink
          to="/dashboard"
          class="px-2 py-1 rounded hover:bg-white/15 transition"
          active-class="bg-white/20"
        >
          Dashboard
        </RouterLink>
      </nav>

      <!-- === Right side: user info + logout === -->
      <div class="ml-auto flex items-center gap-3 text-sm">
        <template v-if="auth.isLoggedIn">
          <span class="hidden sm:inline opacity-90">
            {{ auth.user?.email || 'logged in' }}
          </span>
          <button
            @click="handleLogout"
            class="px-3 py-1 rounded bg-white/15 hover:bg-white/25 transition text-sm font-medium"
          >
            Logout
          </button>
        </template>
        <template v-else>
          <RouterLink
            to="/login"
            class="px-3 py-1 rounded bg-white/15 hover:bg-white/25 transition font-medium"
          >
            Login
          </RouterLink>
          <RouterLink
            to="/signup"
            class="px-3 py-1 rounded border border-current hover:bg-white/15 transition font-medium"
          >
            Signup
          </RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>