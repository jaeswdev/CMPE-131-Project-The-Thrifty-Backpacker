<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTripStore } from '../stores/trip'

const router = useRouter()
const trip = useTripStore()

// === Helpers ===
function todayIsoDate() {
  return new Date().toISOString().slice(0, 10)
}

function isoDatePlusDays(baseIso, days) {
  const d = new Date(baseIso + 'T00:00:00')
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

// === Form state ===
// Sensible defaults — London, next week-ish, $1500 — matches Violet's persona
const origin = ref('SFO')
const destination = ref('LON')
const startDate = ref(isoDatePlusDays(todayIsoDate(), 14))   // 2 weeks out
const endDate = ref(isoDatePlusDays(todayIsoDate(), 21))     // +1 week trip
const budget = ref(1500)
const travelers = ref(1)
const cabinClass = ref('ECONOMY')

// === Validation per AC 1.1, AC 1.5 ===
const today = todayIsoDate()

const validationError = computed(() => {
  if (!origin.value.trim()) return 'Origin is required'
  if (origin.value.trim().length < 2) return 'Origin must be at least 2 characters'
  if (!destination.value.trim()) return 'Destination is required'
  if (destination.value.trim().length < 2) return 'Destination must be at least 2 characters'

  if (!startDate.value) return 'Departure date is required'
  if (!endDate.value) return 'Return date is required'
  if (startDate.value < today) return 'Departure date cannot be in the past'
  if (endDate.value <= startDate.value) return 'Return date must be after departure'

  // AC 1.5: $1-$100,000 cap, no zero, no negative, no non-numeric
  if (budget.value === '' || budget.value === null) return 'Please enter a budget greater than $0'
  if (Number.isNaN(Number(budget.value))) return 'Budget must be a number'
  const budgetNum = Number(budget.value)
  if (budgetNum <= 0) return 'Please enter a budget greater than $0'
  if (budgetNum > 100000) return 'Budget cannot exceed $100,000'

  if (travelers.value < 1) return 'At least 1 traveler is required'
  if (travelers.value > 10) return 'Maximum 10 travelers'

  return null
})

const canSubmit = computed(() => !validationError.value)

// === Submit handler ===
function handleSearch() {
  if (validationError.value) return

  // Save the budget to the trip store so the Trip Total widget (T9)
  // knows what to compare against on the results page.
  trip.setBudget(Number(budget.value), 'USD')

  // Reset the cart so previous trips don't bleed into a new search
  trip.clearCart()

  // Navigate to /results with all search params in the URL.
  // This makes results bookmarkable + refresh-safe.
  router.push({
    name: 'results',
    query: {
      origin: origin.value.trim().toUpperCase(),
      destination: destination.value.trim().toUpperCase(),
      depart_date: startDate.value,
      return_date: endDate.value,
      budget: String(budget.value),
      adults: String(travelers.value),
      cabin_class: cabinClass.value,
    },
  })
}
</script>

<template>
  <div class="max-w-3xl mx-auto mt-6">
    <h2 class="text-2xl font-bold text-slate-800">Plan your trip</h2>
    <p class="mt-1 text-sm text-slate-600">
      Tell us where you're going and how much you can spend — we'll find the best combinations.
    </p>

    <form @submit.prevent="handleSearch" class="mt-6 bg-white rounded-lg shadow p-6 space-y-5">
      <!-- Origin + Destination -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label for="origin" class="block text-sm font-medium text-slate-700">
            From
          </label>
          <input
            id="origin"
            v-model="origin"
            type="text"
            required
            placeholder="SFO or San Francisco"
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   uppercase"
          />
          <p class="mt-1 text-xs text-slate-500">Airport code or city name</p>
        </div>
        <div>
          <label for="destination" class="block text-sm font-medium text-slate-700">
            To
          </label>
          <input
            id="destination"
            v-model="destination"
            type="text"
            required
            placeholder="LON or London"
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   uppercase"
          />
          <p class="mt-1 text-xs text-slate-500">Airport code or city name</p>
        </div>
      </div>

      <!-- Dates -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label for="startDate" class="block text-sm font-medium text-slate-700">
            Departure
          </label>
          <input
            id="startDate"
            v-model="startDate"
            type="date"
            :min="today"
            required
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label for="endDate" class="block text-sm font-medium text-slate-700">
            Return
          </label>
          <input
            id="endDate"
            v-model="endDate"
            type="date"
            :min="startDate"
            required
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <!-- Budget + Travelers + Cabin -->
      <div class="grid grid-cols-3 gap-4">
        <div>
          <label for="budget" class="block text-sm font-medium text-slate-700">
            Total budget (USD)
          </label>
          <div class="relative mt-1">
            <span class="absolute left-3 top-2.5 text-slate-500">$</span>
            <input
              id="budget"
              v-model.number="budget"
              type="number"
              min="1"
              max="100000"
              step="1"
              required
              class="block w-full pl-7 pr-3 py-2 border border-slate-300 rounded-md
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <p class="mt-1 text-xs text-slate-500">$1 – $100,000</p>
        </div>

        <div>
          <label for="travelers" class="block text-sm font-medium text-slate-700">
            Travelers
          </label>
          <input
            id="travelers"
            v-model.number="travelers"
            type="number"
            min="1"
            max="10"
            required
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label for="cabinClass" class="block text-sm font-medium text-slate-700">
            Cabin
          </label>
          <select
            id="cabinClass"
            v-model="cabinClass"
            class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   bg-white"
          >
            <option value="ECONOMY">Economy</option>
            <option value="PREMIUM_ECONOMY">Premium Economy</option>
            <option value="BUSINESS">Business</option>
            <option value="FIRST">First</option>
          </select>
        </div>
      </div>

      <!-- Inline validation error -->
      <div v-if="validationError" class="p-3 bg-amber-50 border border-amber-200 rounded text-sm text-amber-800">
        {{ validationError }}
      </div>

      <!-- Submit -->
      <button
        type="submit"
        :disabled="!canSubmit"
        class="w-full py-2.5 px-4 rounded-md text-white font-medium
               bg-blue-600 hover:bg-blue-700
               disabled:bg-slate-300 disabled:cursor-not-allowed
               transition"
      >
        Search trips
      </button>
    </form>
  </div>
</template>