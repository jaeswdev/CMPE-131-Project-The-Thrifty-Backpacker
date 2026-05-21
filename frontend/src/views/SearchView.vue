<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const destination = ref('')
const origin      = ref('')
const budget      = ref(1500)
const startDate   = ref('')
const endDate     = ref('')
const travelers   = ref(1)

const validationError = computed(() => {
  if (!destination.value.trim()) return 'Destination is required'
  if (budget.value <= 0)         return 'Budget must be greater than $0'
  if (!startDate.value)          return 'Departure date is required'
  if (!endDate.value)            return 'Return date is required'
  if (endDate.value <= startDate.value) return 'Return date must be after departure'
  return null
})

function handleSearch() {
  if (validationError.value) return
  router.push({
    name: 'results',
    query: {
      destination: destination.value.trim(),
      origin:      origin.value.trim(),
      budget:      budget.value,
      start_date:  startDate.value,
      end_date:    endDate.value,
      travelers:   travelers.value,
    },
  })
}
</script>

<template>
  <div class="max-w-lg mx-auto mt-10 px-4">
    <h2 class="text-2xl font-bold text-slate-800">Plan your trip</h2>
    <p class="mt-1 text-sm text-slate-600">Enter your details to find flights, hotels, and activities.</p>

    <form @submit.prevent="handleSearch" class="mt-6 space-y-4">
      <div>
        <label class="block text-sm font-medium text-slate-700">Destination</label>
        <input
          v-model="destination"
          type="text"
          placeholder="e.g. London"
          required
          class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700">
          Origin <span class="text-xs text-slate-500 font-normal">(airport or city, for flights)</span>
        </label>
        <input
          v-model="origin"
          type="text"
          placeholder="e.g. JFK"
          class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700">Total budget (USD)</label>
        <input
          v-model.number="budget"
          type="number"
          min="1"
          required
          class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-sm font-medium text-slate-700">Departure date</label>
          <input
            v-model="startDate"
            type="date"
            required
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700">Return date</label>
          <input
            v-model="endDate"
            type="date"
            required
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700">Travelers</label>
        <input
          v-model.number="travelers"
          type="number"
          min="1"
          max="10"
          required
          class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <p v-if="validationError" class="text-sm text-red-600">{{ validationError }}</p>

      <button
        type="submit"
        :disabled="!!validationError"
        class="w-full py-2 px-4 rounded-md text-white font-medium
               bg-blue-600 hover:bg-blue-700
               disabled:bg-slate-300 disabled:cursor-not-allowed transition"
      >
        Search trips
      </button>
    </form>
  </div>
</template>
