<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import api from '../services/api'

const bookings = ref([])
const loading  = ref(true)
const error    = ref(null)
const selectedIds = ref(new Set())
const deleting = ref(false)
const openMenuId = ref(null)
const updatingId = ref(null)

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

// === Selection ===

const allSelected = computed(() =>
  bookings.value.length > 0 && selectedIds.value.size === bookings.value.length
)
const someSelected = computed(() =>
  selectedIds.value.size > 0 && !allSelected.value
)

function toggleOne(id) {
  // Cloning the Set forces Vue to detect the change (reactivity on Set
  // mutation isn't tracked otherwise).
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedIds.value = next
}

function toggleAll() {
  if (allSelected.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(bookings.value.map(b => b.Booking_ID))
  }
}

// === Status menu (PENDING → Confirm | Cancel) ===

function toggleStatusMenu(id) {
  openMenuId.value = openMenuId.value === id ? null : id
}

// Close the popover when the user clicks anywhere that isn't inside a menu
// trigger or panel. Listener attaches once on mount and detaches on unmount.
function handleDocumentClick(e) {
  if (!e.target.closest('[data-status-menu]')) {
    openMenuId.value = null
  }
}

onMounted(() => document.addEventListener('click', handleDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', handleDocumentClick))

async function confirmBooking(booking) {
  updatingId.value = booking.Booking_ID
  try {
    const { data } = await api.put(`/bookings/${booking.Booking_ID}`, { status: 'CONFIRMED' })
    const idx = bookings.value.findIndex(b => b.Booking_ID === booking.Booking_ID)
    if (idx >= 0) bookings.value[idx] = data
    openMenuId.value = null
  } catch {
    alert('Could not confirm this booking. Please try again.')
  } finally {
    updatingId.value = null
  }
}

// === Delete ===

async function cancelBooking(booking) {
  const label = (booking.Booking_Type || 'booking').toLowerCase()
  if (!confirm(`Cancel this ${label}? This will permanently remove it from your bookings.`)) return
  try {
    await api.delete(`/bookings/${booking.Booking_ID}`)
    bookings.value = bookings.value.filter(b => b.Booking_ID !== booking.Booking_ID)
    const next = new Set(selectedIds.value)
    next.delete(booking.Booking_ID)
    selectedIds.value = next
    openMenuId.value = null
  } catch {
    alert('Could not cancel this booking. Please try again.')
  }
}

async function deleteSelected() {
  const ids = [...selectedIds.value]
  if (ids.length === 0) return
  if (!confirm(`Permanently delete ${ids.length} booking${ids.length > 1 ? 's' : ''}? This can't be undone.`)) return
  deleting.value = true
  try {
    const results = await Promise.allSettled(
      ids.map(id => api.delete(`/bookings/${id}`))
    )
    const deletedIds = new Set(
      ids.filter((_, i) => results[i].status === 'fulfilled')
    )
    bookings.value = bookings.value.filter(b => !deletedIds.has(b.Booking_ID))
    selectedIds.value = new Set()
    const failedCount = results.filter(r => r.status === 'rejected').length
    if (failedCount > 0) {
      alert(`${failedCount} booking${failedCount > 1 ? 's' : ''} could not be deleted. Please try again.`)
    }
  } finally {
    deleting.value = false
  }
}

// === Formatting ===

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
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">My Bookings</h1>
      <button
        v-if="selectedIds.size > 0"
        @click="deleteSelected"
        :disabled="deleting"
        class="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition"
      >
        {{ deleting ? 'Deleting…' : `Delete ${selectedIds.size} selected` }}
      </button>
    </div>

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
            <th class="px-4 py-3 w-10">
              <input
                type="checkbox"
                :checked="allSelected"
                :indeterminate.prop="someSelected"
                @change="toggleAll"
                aria-label="Select all bookings"
                class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
            </th>
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
            :class="selectedIds.has(booking.Booking_ID) ? 'bg-blue-50' : 'hover:bg-slate-50'"
            class="transition"
          >
            <td class="px-4 py-3">
              <input
                type="checkbox"
                :checked="selectedIds.has(booking.Booking_ID)"
                @change="toggleOne(booking.Booking_ID)"
                :aria-label="`Select booking ${booking.Booking_ID}`"
                class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
            </td>
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
            <td class="px-4 py-3 relative" data-status-menu>
              <button
                v-if="booking.Status === 'PENDING'"
                @click.stop="toggleStatusMenu(booking.Booking_ID)"
                :class="statusClass(booking.Status)"
                class="px-2 py-0.5 rounded text-xs font-semibold cursor-pointer hover:ring-2 hover:ring-yellow-400 transition"
                :aria-expanded="openMenuId === booking.Booking_ID"
              >
                {{ booking.Status }} ▾
              </button>
              <span
                v-else
                :class="statusClass(booking.Status)"
                class="px-2 py-0.5 rounded text-xs font-semibold"
              >
                {{ booking.Status }}
              </span>

              <!-- Popover: appears under the PENDING badge -->
              <div
                v-if="openMenuId === booking.Booking_ID"
                data-status-menu
                class="absolute z-20 mt-1 left-4 w-32 bg-white border border-slate-200 rounded-lg shadow-lg overflow-hidden"
              >
                <button
                  @click.stop="confirmBooking(booking)"
                  :disabled="updatingId === booking.Booking_ID"
                  class="w-full text-left px-3 py-2 text-sm text-green-700 hover:bg-green-50 disabled:opacity-50 transition"
                >
                  {{ updatingId === booking.Booking_ID ? 'Confirming…' : '✓ Confirm' }}
                </button>
                <button
                  @click.stop="cancelBooking(booking)"
                  class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 border-t border-slate-100 transition"
                >
                  ✕ Cancel
                </button>
              </div>
            </td>
            <td class="px-4 py-3 text-right">
              <button
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
