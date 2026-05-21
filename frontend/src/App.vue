<script setup>
// App root component. Will hold AppHeader (T5) + <RouterView /> for routed pages.
// Current state: routing scaffold only.
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <!-- AppHeader will go here in T5 -->
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
      </div>
    </header>

    <main class="max-w-6xl mx-auto">
      <RouterView />
    </main>
  </div>
</template>