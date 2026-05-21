<script setup>
import { onMounted } from 'vue'
import AppHeader from './components/AppHeader.vue'
import { useTenantStore } from './stores/tenant'

const tenant = useTenantStore()

// Apply tenant brand color on app boot (in case tenant info was persisted
// from a previous session via localStorage hydration in the store).
onMounted(() => {
  tenant.applyBrandColorToDocument()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <AppHeader />
    <main class="max-w-6xl mx-auto p-6">
      <RouterView />
    </main>
  </div>
</template>