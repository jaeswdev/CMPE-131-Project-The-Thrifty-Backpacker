<script setup>
import { useAuthStore } from './stores/auth'
import { useTenantStore } from './stores/tenant'
import { useTripStore } from './stores/trip'
import { onMounted } from 'vue'

const auth = useAuthStore()
const tenant = useTenantStore()
const trip = useTripStore()

// Apply tenant brand color on app mount (T5 will move this to AppHeader)
onMounted(() => {
  tenant.applyBrandColorToDocument()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <header class="bg-slate-800 text-white p-4">
      <div class="max-w-6xl mx-auto flex items-center gap-6">
        <h1 class="text-xl font-bold">The Thrifty Backpacker</h1>
        <nav class="flex gap-4 text-sm">
          <RouterLink to="/login" class="hover:text-slate-300">Login</RouterLink>
          <RouterLink to="/signup" class="hover:text-slate-300">Signup</RouterLink>
          <RouterLink to="/search" class="hover:text-slate-300">Search</RouterLink>
          <RouterLink to="/results" class="hover:text-slate-300">Results</RouterLink>
          <RouterLink to="/dashboard" class="hover:text-slate-300">Dashboard</RouterLink>
        </nav>
        <span class="ml-auto text-xs">
          {{ auth.isLoggedIn ? `Logged in: ${auth.user?.email || 'unknown'}` : 'Not logged in' }}
        </span>
      </div>
    </header>

    <main class="max-w-6xl mx-auto">
      <RouterView />
    </main>

    <!-- TEMP: Pinia store smoke test panel. Remove this before T5. -->
    <aside class="max-w-6xl mx-auto p-6 mt-6 bg-white rounded-lg shadow">
      <h2 class="font-semibold text-slate-700 mb-3">🧪 Pinia store smoke test (T3)</h2>
      <div class="grid grid-cols-3 gap-4 text-xs">
        <div>
          <p class="font-bold text-slate-600">auth</p>
          <p>isLoggedIn: {{ auth.isLoggedIn }}</p>
          <p>token: {{ auth.token ? auth.token.slice(0, 12) + '…' : 'null' }}</p>
        </div>
        <div>
          <p class="font-bold text-slate-600">tenant</p>
          <p>name: {{ tenant.tenantName }}</p>
          <p>brand: {{ tenant.brandColor }}</p>
        </div>
        <div>
          <p class="font-bold text-slate-600">trip</p>
          <p>budget: ${{ trip.budget }}</p>
          <p>total: ${{ trip.totalCost.toFixed(2) }} ({{ trip.status }})</p>
        </div>
      </div>
    </aside>
  </div>
</template>