<script setup>
import { ref } from 'vue'

const emit = defineEmits(['change'])

const tiers = [
  { value: 'free',     label: 'Free' },
  { value: 'under_25', label: 'Under $25' },
  { value: '25_75',    label: '$25–$75' },
  { value: '75_plus',  label: '$75+' },
]

const selected = ref([])

function toggle(tierValue) {
  const idx = selected.value.indexOf(tierValue)
  if (idx >= 0) {
    selected.value.splice(idx, 1)
  } else {
    selected.value.push(tierValue)
  }
  emit('change', [...selected.value])
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <span class="text-sm font-medium text-slate-600">Filter:</span>
    <button
      v-for="tier in tiers"
      :key="tier.value"
      @click="toggle(tier.value)"
      :class="selected.includes(tier.value)
        ? 'bg-blue-600 text-white border-blue-600'
        : 'bg-white text-slate-600 border-slate-300 hover:border-blue-400'"
      class="px-3 py-1 rounded-full text-sm border transition"
    >
      {{ tier.label }}
    </button>
  </div>
</template>
