<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const bookings = ref([])
const loading  = ref(true)
const error    = ref(null)

onMounted(async () => {
  try {
    const { data } = await api.get('/bookings/by-agent-user')
    bookings.value = data
  } catch (e) {
    // 401 is handled globally by the axios interceptor (redirect to /login)
    if (e.response?.status !== 401) {
      error.value = 'Could not load your bookings. Please try again.'
    }
  } finally {
    loading.value = false
  }
})

async function cancelBooking(booking) {
  if (!confirm(`Cancel this ${(booking.Booking_Type || 'booking').toLowerCase()}?`)) return
  try {
    const { data } = await api.patch(`/bookings/${booking.Booking_ID}/cancel`)
    const idx = bookings.value.findIndex(b => b.Booking_ID === booking.Booking_ID)
    if (idx >= 0) bookings.value[idx] = data
  } catch {
    alert('Could not cancel this booking. Please try again.')
  }
}

function statusClass(status) {
  return {
    CONFIRMED: 'bg-green-100 text-green-700',
    PENDING:   'bg-yellow-100 text-yellow-700',
    CANCELLED: 'bg-slate-100 text-slate-500',
  }[status] ?? 'bg-slate-100 text-slate-500'
}

// The dashboard shows the *travel* date, not Created_At (which is just the
// insert timestamp). Pull it from the cached item — different field per type.
//
// Format from the YYYY-MM-DD prefix directly; don't pass strings to
// `new Date()` and call `.toLocaleDateString()`, because:
//   - "2026-06-04"            is parsed as UTC midnight → shifts back a day west of UTC
//   - "2026-06-05T18:20:00-07:00" → renders in the viewer's TZ, not the airport's
// Both produce dates that disagree with what's actually stored.
function fmtCalendarDate(s) {
  if (!s) return null
  const [y, m, d] = String(s).slice(0, 10).split('-').map(Number)
  if (!y) return null
  return new Date(y, m - 1, d).toLocaleDateString()
}

function travelDateRange(booking) {
  const item = booking.item
  if (!item) return '—'
  let start, end
  if (booking.Booking_Type === 'FLIGHT') {
    start = fmtCalendarDate(item.Departure_Datetime)
    // Round-trip: span is outbound depart → return arrival.
    // One-way: span is outbound depart → outbound arrival.
    end = fmtCalendarDate(item.Return_Arrival_Datetime || item.Arrival_Datetime)
  } else if (booking.Booking_Type === 'HOTEL') {
    start = fmtCalendarDate(item.Checkin_Date)
    end   = fmtCalendarDate(item.Checkout_Date)
  } else if (booking.Booking_Type === 'ATTRACTION') {
    start = fmtCalendarDate(item.Start_Date)
    end   = fmtCalendarDate(item.End_Date)
  }
  if (!start) return '—'
  return start === end || !end ? start : `${start} → ${end}`
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold text-slate-800 mb-6">My Bookings</h1>

    <p v-if="loading" class="text-slate-400 text-sm">Loading your bookings…</p>

    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-600 rounded-xl p-4">
      {{ error }}
    </div>

    <!-- Empty state (per project brief) — TC-07: Tenant B user sees zero bookings -->
    <div v-else-if="!bookings.length" class="text-center py-20">
      <p class="text-5xl mb-4">🧳</p>
      <p class="text-lg font-medium text-slate-500">No bookings yet</p>
      <p class="text-sm text-slate-400 mt-1">Search for flights, hotels, and activities to get started.</p>
      <RouterLink
        to="/search"
        class="mt-5 inline-block px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
      >
        Start searching
      </RouterLink>
    </div>

    <!-- Bookings table -->
    <div v-else class="rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 border-b border-slate-200 text-left">
          <tr>
            <th class="px-4 py-3 font-semibold text-slate-600">Type</th>
            <th class="px-4 py-3 font-semibold text-slate-600">Price</th>
            <th class="px-4 py-3 font-semibold text-slate-600">Travel date</th>
            <th class="px-4 py-3 font-semibold text-slate-600">Status</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr
            v-for="booking in bookings"
            :key="booking.Booking_ID"
            class="hover:bg-slate-50 transition"
          >
            <td class="px-4 py-3 font-medium text-slate-700 capitalize">
              {{ (booking.Booking_Type || 'unknown').toLowerCase() }}
            </td>
            <td class="px-4 py-3 text-slate-700">
              ${{ Number(booking.Total_Price).toFixed(2) }}
              <span class="text-slate-400 text-xs ml-1">{{ booking.Currency }}</span>
            </td>
            <td class="px-4 py-3 text-slate-500 whitespace-nowrap">
              {{ travelDateRange(booking) }}
            </td>
            <td class="px-4 py-3">
              <span :class="statusClass(booking.Status)" class="px-2 py-0.5 rounded text-xs font-semibold">
                {{ booking.Status }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <button
                v-if="booking.Status !== 'CANCELLED'"
                @click="cancelBooking(booking)"
                class="text-xs text-red-500 hover:text-red-700 hover:underline transition"
              >
                Cancel
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
