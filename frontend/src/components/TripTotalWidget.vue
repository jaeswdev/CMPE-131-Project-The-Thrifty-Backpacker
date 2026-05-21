<script setup>
// US-3 deliverable: real-time trip total + traffic-light budget status.
//
// AC 3.1: visible at top of results page (sticky positioning)
// AC 3.2: green ≤90% / yellow 90-100% / red >100% of budget
// AC 3.3: updates within 1 second of add/remove/swap (Vue reactivity = ~16ms)
// AC 3.4: Book Now disabled when over budget, tooltip explains why

import { computed, ref, watch } from 'vue'
import { useTripStore } from '../stores/trip'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import api from '../services/api'

const trip = useTripStore()
const auth = useAuthStore()
const router = useRouter()

// === Booking state ===
const booking = ref('idle')  // 'idle' | 'loading' | 'success' | 'error'
const bookingMessage = ref('')

// === Currency formatter — memoize for perf ===
const usd = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

// === AC 3.2: traffic-light status styling ===
// Maps the trip store's 'green' | 'yellow' | 'red' to Tailwind classes.
// Wrap the status in a function so any future tweak (e.g. amber when very close
// to budget) is a one-line change here.
const statusStyles = computed(() => {
  switch (trip.status) {
    case 'green':
      return {
        bg: 'bg-emerald-50',
        border: 'border-emerald-500',
        text: 'text-emerald-900',
        bar: 'bg-emerald-500',
        label: 'On budget',
        icon: '✓',
      }
    case 'yellow':
      return {
        bg: 'bg-amber-50',
        border: 'border-amber-500',
        text: 'text-amber-900',
        bar: 'bg-amber-500',
        label: 'Almost at budget',
        icon: '⚠',
      }
    case 'red':
      return {
        bg: 'bg-red-50',
        border: 'border-red-500',
        text: 'text-red-900',
        bar: 'bg-red-500',
        label: 'Over budget',
        icon: '✕',
      }
    default:
      return {
        bg: 'bg-slate-50',
        border: 'border-slate-300',
        text: 'text-slate-900',
        bar: 'bg-slate-500',
        label: '',
        icon: '',
      }
  }
})

// Progress bar fill % capped at 100% (don't draw beyond container)
const progressPercent = computed(() => Math.min(100, trip.percentUsed))

// === AC 3.4: disable Book Now if over budget OR cart empty ===
const hasItems = computed(() =>
  !!trip.flight || !!trip.hotel || trip.activities.length > 0
)

const canBook = computed(() => hasItems.value && !trip.isOverBudget && booking.value !== 'loading')

const disabledTooltip = computed(() => {
  if (!hasItems.value) return 'Add a flight, hotel, or activity to your trip first.'
  if (trip.isOverBudget) {
    const overAmount = trip.totalCost - trip.budget
    return `You're ${usd.format(overAmount)} over budget. Remove an item to enable booking.`
  }
  if (booking.value === 'loading') return 'Processing booking…'
  return ''
})

// === Backend sanity check via /trip/calculate (debounced) ===
// Optimistic client math is instant; the backend call is for authoritative
// numbers (currency, validation). Run AFTER store changes settle.
const serverStatus = ref(null)  // last backend response
let calcTimer = null

watch(
  () => [trip.flightCost, trip.hotelCost, trip.activitiesCost, trip.budget],
  () => {
    if (calcTimer) clearTimeout(calcTimer)
    calcTimer = setTimeout(syncWithBackend, 300)  // 300ms debounce
  }
)

async function syncWithBackend() {
  // Skip if not logged in or cart is empty (no need)
  if (!auth.isLoggedIn || !hasItems.value) {
    serverStatus.value = null
    return
  }
  try {
    const res = await api.post('/trip/calculate', {
      budget: trip.budget,
      flight_cost: trip.flightCost,
      hotel_cost: trip.hotelCost,
      activity_costs: trip.activities.map(a => a.price ?? 0),
      currency: trip.currency,
    })
    serverStatus.value = res.data
  } catch (err) {
    // Silent failure — frontend numbers still work. Log for dev debugging.
    console.warn('Trip calculate failed:', err.message)
    serverStatus.value = null
  }
}

// === Book Now handler ===
async function handleBookNow() {
  if (!canBook.value) return
  booking.value = 'loading'
  bookingMessage.value = ''

  // Book each item type in the cart. Stop on the first failure.
  try {
    // Flight
    if (trip.flight) {
      await api.post('/bookings/flights', {
        booking_type: 'FLIGHT',
        flight: trip.flight,
      })
    }
    // Hotel
    if (trip.hotel) {
      await api.post('/bookings/hotels', {
        booking_type: 'HOTEL',
        hotel: trip.hotel,
      })
    }
    // Activities
    for (const activity of trip.activities) {
      await api.post('/bookings/attractions', {
        booking_type: 'ATTRACTION',
        attraction: activity,
      })
    }

    booking.value = 'success'
    bookingMessage.value = 'Trip booked! Redirecting to dashboard…'
    trip.clearCart()
    setTimeout(() => router.push({ name: 'dashboard' }), 1500)
  } catch (err) {
    booking.value = 'error'
    bookingMessage.value =
      err.response?.data?.detail || 'Booking failed. Some items may have been booked. Check the dashboard.'
  }
}
</script>

<template>
  <aside
    class="sticky top-20 z-30 rounded-lg border-2 shadow-md transition-colors"
    :class="[statusStyles.bg, statusStyles.border]"
    role="status"
    aria-live="polite"
  >
    <div class="p-4">
      <!-- Header row: status label + budget vs total -->
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <span class="text-xl" :class="statusStyles.text">{{ statusStyles.icon }}</span>
          <span class="font-semibold" :class="statusStyles.text">
            {{ statusStyles.label || 'Trip Total' }}
          </span>
        </div>
        <div class="text-right" :class="statusStyles.text">
          <div class="text-sm opacity-75">
            Budget: <span class="font-medium">{{ usd.format(trip.budget) }}</span>
          </div>
          <div class="text-lg font-bold">
            {{ usd.format(trip.totalCost) }}
          </div>
        </div>
      </div>

      <!-- Progress bar -->
      <div class="mt-3 h-2 bg-white/60 rounded-full overflow-hidden">
        <div
          class="h-full transition-all duration-200"
          :class="statusStyles.bar"
          :style="{ width: `${progressPercent}%` }"
        ></div>
      </div>
      <div class="mt-1 flex justify-between text-xs" :class="statusStyles.text">
        <span>{{ trip.percentUsed.toFixed(0) }}% used</span>
        <span v-if="!trip.isOverBudget">
          {{ usd.format(trip.budget - trip.totalCost) }} remaining
        </span>
        <span v-else class="font-semibold">
          {{ usd.format(trip.totalCost - trip.budget) }} over
        </span>
      </div>

      <!-- Breakdown (if any items selected) -->
      <div v-if="hasItems" class="mt-3 pt-3 border-t" :class="statusStyles.border + ' ' + statusStyles.text">
        <dl class="grid grid-cols-3 gap-2 text-xs">
          <div>
            <dt class="opacity-75">Flights</dt>
            <dd class="font-semibold">{{ usd.format(trip.flightCost) }}</dd>
          </div>
          <div>
            <dt class="opacity-75">Hotels</dt>
            <dd class="font-semibold">{{ usd.format(trip.hotelCost) }}</dd>
          </div>
          <div>
            <dt class="opacity-75">Activities ({{ trip.activities.length }})</dt>
            <dd class="font-semibold">{{ usd.format(trip.activitiesCost) }}</dd>
          </div>
        </dl>
      </div>

      <!-- Book Now button (AC 3.4) -->
      <div class="mt-3">
        <button
          :disabled="!canBook"
          @click="handleBookNow"
          :title="disabledTooltip"
          class="w-full py-2 px-4 rounded-md font-medium transition-colors"
          :class="canBook
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-slate-200 text-slate-500 cursor-not-allowed'"
        >
          {{ booking === 'loading' ? 'Booking…' : 'Book Now' }}
        </button>
        <p v-if="!canBook && disabledTooltip" class="mt-1 text-xs italic" :class="statusStyles.text">
          {{ disabledTooltip }}
        </p>
      </div>

      <!-- Booking status messages -->
      <div v-if="booking === 'success'" class="mt-3 p-2 bg-green-100 text-green-800 rounded text-sm">
        ✓ {{ bookingMessage }}
      </div>
      <div v-if="booking === 'error'" class="mt-3 p-2 bg-red-100 text-red-800 rounded text-sm">
        ✗ {{ bookingMessage }}
      </div>
    </div>
  </aside>
</template>