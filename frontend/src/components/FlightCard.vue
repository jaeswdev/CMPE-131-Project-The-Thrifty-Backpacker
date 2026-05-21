<script setup>
import { computed } from 'vue'
import { useTripStore } from '../stores/trip'

const props = defineProps({
  flight: { type: Object, required: true }
})

const tripStore = useTripStore()

const inTrip = computed(() => tripStore.flight?.offer_token === props.flight.offer_token)

function toggle() {
  if (inTrip.value) {
    tripStore.setFlight(null)
  } else {
    // trip store reads .price; backend returns .price_usd — normalize here
    tripStore.setFlight({ ...props.flight, price: props.flight.price_usd })
  }
}

function formatDuration(mins) {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

function formatTime(isoStr) {
  // Tipsters' datetime carries the airport's local time + offset.
  // Strip the offset (and the date) so we render the wall-clock time
  // the traveler will actually see at the airport, not the viewer's TZ.
  if (!isoStr) return ''
  const m = String(isoStr).match(/T(\d{2}):(\d{2})/)
  if (!m) return ''
  const hour = Number(m[1])
  const min  = m[2]
  const period = hour >= 12 ? 'PM' : 'AM'
  const h12 = ((hour + 11) % 12) + 1
  return `${h12}:${min} ${period}`
}

function formatDate(isoStr) {
  // Render the airport-local calendar date, not the viewer's. Tipsters
  // already encodes airport-local in the YYYY-MM-DD prefix.
  if (!isoStr) return ''
  const [y, m, d] = String(isoStr).slice(0, 10).split('-').map(Number)
  if (!y) return ''
  return new Date(y, m - 1, d).toLocaleDateString([], { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="bg-white rounded-xl border border-slate-200 p-4 flex flex-col gap-3 shadow-sm hover:shadow-md transition">
    <!-- Airline row -->
    <div class="flex items-center gap-3">
      <img
        v-if="flight.airline_logo_url"
        :src="flight.airline_logo_url"
        :alt="flight.airline_name"
        class="h-8 w-8 object-contain"
        @error="$event.target.style.display = 'none'"
      />
      <span class="font-semibold text-slate-800">{{ flight.airline_name }}</span>
      <span class="ml-auto text-xs text-slate-400 uppercase tracking-wider">{{ flight.airline_code }}</span>
    </div>

    <!-- Outbound leg -->
    <div>
      <p v-if="flight.return_departure" class="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1">
        Outbound · {{ formatDate(flight.departure.datetime) }}
      </p>
      <div class="flex items-center justify-between text-slate-700">
        <div class="text-center">
          <p class="text-lg font-bold">{{ flight.departure.airport_code }}</p>
          <p class="text-xs text-slate-500">{{ formatTime(flight.departure.datetime) }}</p>
          <p class="text-xs text-slate-400">{{ flight.departure.city }}</p>
        </div>

        <div class="flex-1 text-center px-3">
          <p class="text-xs text-slate-400 mb-1">{{ formatDuration(flight.duration_minutes) }}</p>
          <div class="flex items-center gap-1">
            <div class="flex-1 h-px bg-slate-300"></div>
            <svg class="w-4 h-4 text-slate-400 rotate-90" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2h-1A1.5 1.5 0 0 0 9 3.5V9L1 14v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L12 19v-5.5l9 2.5z"/>
            </svg>
            <div class="flex-1 h-px bg-slate-300"></div>
          </div>
          <p class="text-xs text-slate-400 mt-1">
            {{ flight.stops === 0 ? 'Direct' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}` }}
          </p>
        </div>

        <div class="text-center">
          <p class="text-lg font-bold">{{ flight.arrival.airport_code }}</p>
          <p class="text-xs text-slate-500">{{ formatTime(flight.arrival.datetime) }}</p>
          <p class="text-xs text-slate-400">{{ flight.arrival.city }}</p>
        </div>
      </div>
    </div>

    <!-- Return leg -->
    <div v-if="flight.return_departure" class="border-t border-slate-100 pt-3">
      <p class="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1">
        Return · {{ formatDate(flight.return_departure.datetime) }}
      </p>
      <div class="flex items-center justify-between text-slate-700">
        <div class="text-center">
          <p class="text-lg font-bold">{{ flight.return_departure.airport_code }}</p>
          <p class="text-xs text-slate-500">{{ formatTime(flight.return_departure.datetime) }}</p>
          <p class="text-xs text-slate-400">{{ flight.return_departure.city }}</p>
        </div>

        <div class="flex-1 text-center px-3">
          <p class="text-xs text-slate-400 mb-1">{{ formatDuration(flight.return_duration_minutes) }}</p>
          <div class="flex items-center gap-1">
            <div class="flex-1 h-px bg-slate-300"></div>
            <svg class="w-4 h-4 text-slate-400 -rotate-90" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2h-1A1.5 1.5 0 0 0 9 3.5V9L1 14v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L12 19v-5.5l9 2.5z"/>
            </svg>
            <div class="flex-1 h-px bg-slate-300"></div>
          </div>
          <p class="text-xs text-slate-400 mt-1">
            {{ flight.return_stops === 0 ? 'Direct' : `${flight.return_stops} stop${flight.return_stops > 1 ? 's' : ''}` }}
          </p>
        </div>

        <div class="text-center">
          <p class="text-lg font-bold">{{ flight.return_arrival.airport_code }}</p>
          <p class="text-xs text-slate-500">{{ formatTime(flight.return_arrival.datetime) }}</p>
          <p class="text-xs text-slate-400">{{ flight.return_arrival.city }}</p>
        </div>
      </div>
    </div>

    <!-- Price + button row -->
    <div class="flex items-center justify-between pt-2 border-t border-slate-100">
      <p class="text-xl font-bold text-slate-800">${{ flight.price_usd.toFixed(2) }}</p>
      <button
        @click="toggle"
        :class="inTrip
          ? 'bg-slate-100 text-slate-700 hover:bg-red-50 hover:text-red-600 border border-slate-300'
          : 'bg-blue-600 text-white hover:bg-blue-700'"
        class="px-4 py-1.5 rounded-lg text-sm font-medium transition"
      >
        {{ inTrip ? 'Remove from trip' : 'Add to trip' }}
      </button>
    </div>
  </div>
</template>
