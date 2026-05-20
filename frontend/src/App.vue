<script setup>
// App root component. Will hold AppHeader + <RouterView /> once routing
// and the header are added in tasks T2 and T5.
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <main class="max-w-6xl mx-auto p-6">
      <h1 class="text-3xl font-bold text-slate-800">
        The Thrifty Backpacker
      </h1>
      <p class="mt-2 text-slate-600">
        Frontend scaffold is alive. Tailwind is wired up. Vue is reactive.
      </p>
      <div class="mt-6 p-4 rounded-lg" :style="{ backgroundColor: 'var(--color-brand)' }">
        <p class="text-white">
          This box uses the <code class="bg-white/20 px-2 py-0.5 rounded">--color-brand</code>
          CSS variable. T5 (branded header) will set this dynamically based on tenant.
        </p>
      </div>
    </main>
  </div>
</template>