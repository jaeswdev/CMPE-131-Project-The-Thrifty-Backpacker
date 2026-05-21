<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../services/api'
import { useTripStore } from '../stores/trip'
import FlightCard from '../components/FlightCard.vue'
import HotelCard from '../components/HotelCard.vue'
import AttractionCard from '../components/AttractionCard.vue'
import ActivityFilter from '../components/ActivityFilter.vue'

const route = useRoute()
const router = useRouter()
const tripStore = useTripStore()
const bookingInProgress = ref(false)

// Read search params from the query string SearchView sends
const destination = computed(() => route.query.destination || '')
const origin      = computed(() => route.query.origin || '')
const budget      = computed(() => parseFloat(route.query.budget) || 1500)
const startDate   = computed(() => route.query.depart_date || route.query.start_date || '')
const endDate     = computed(() => route.query.return_date || route.query.end_date || '')
const travelers   = computed(() => parseInt(route.query.adults || route.query.travelers) || 1)

const flights          = ref([])
const hotels           = ref([])
const attractions      = ref([])
const flightMessage    = ref(null)
const hotelMessage     = ref(null)
const attractionMessage = ref(null)
const loadingFlights   = ref(false)
const loadingHotels    = ref(false)
const loadingAttractions = ref(false)
const pageError        = ref(null)

// Inline trip total banner — styled per US-3 status colors.
// Hyunjae's TripTotalWidget (T9) will replace this once it lands.
const bannerClass = computed(() => ({
  green:  'bg-green-50 border-green-300 text-green-800',
  yellow: 'bg-yellow-50 border-yellow-300 text-yellow-800',
  red:    'bg-red-50 border-red-300 text-red-800',
}[tripStore.status] ?? 'bg-slate-50 border-slate-200 text-slate-700'))

onMounted(async () => {
  if (!destination.value) {
    pageError.value = 'No destination provided. Go back and search again.'
    return
  }
  tripStore.setBudget(budget.value)
  tripStore.clearCart()
  await Promise.all([fetchFlights(), fetchHotels(), fetchAttractions(null)])
})

async function fetchFlights() {
  if (!origin.value || !startDate.value) {
    flightMessage.value = 'Provide an origin and travel date to see flights.'
    return
  }
  loadingFlights.value = true
  try {
    const { data } = await api.get('/flights/search', {
      params: {
        origin:      origin.value,
        destination: destination.value,
        depart_date: startDate.value,
        return_date: endDate.value || undefined,
        budget:      budget.value,
        adults:      travelers.value,
      },
    })
    flights.value       = data.items
    flightMessage.value = data.message || null
  } catch {
    flightMessage.value = 'Could not load flights. Please try again.'
  } finally {
    loadingFlights.value = false
  }
}

async function fetchHotels() {
  if (!startDate.value || !endDate.value) {
    hotelMessage.value = 'Provide check-in and check-out dates to see hotels.'
    return
  }
  loadingHotels.value = true
  try {
    const { data } = await api.get('/hotels/search', {
      params: {
        destination:   destination.value,
        checkin_date:  startDate.value,
        checkout_date: endDate.value,
        budget:        budget.value,
        adults:        travelers.value,
      },
    })
    hotels.value       = data.items
    hotelMessage.value = data.message || null
  } catch {
    hotelMessage.value = 'Could not load hotels. Please try again.'
  } finally {
    loadingHotels.value = false
  }
}

async function fetchAttractions(tier) {
  if (!startDate.value || !endDate.value) {
    attractionMessage.value = 'Provide travel dates to see activities.'
    return
  }
  loadingAttractions.value = true
  try {
    const params = {
      destination: destination.value,
      start_date:  startDate.value,
      end_date:    endDate.value,
    }
    if (tier) params.price_tier = tier

    const { data } = await api.get('/attractions/search', { params })
    attractions.value      = data.items
    attractionMessage.value = data.message || null
  } catch {
    attractionMessage.value = 'Could not load activities. Please try again.'
  } finally {
    loadingAttractions.value = false
  }
}

// ActivityFilter emits an array; backend accepts one tier — use the first selected
function onFilterChange(tiers) {
  fetchAttractions(tiers[0] || null)
}

async function bookTrip() {
  bookingInProgress.value = true
  try {
    const requests = []

    // Flight: flatten nested departure/arrival, map price_usd → price
    if (tripStore.flight) {
      const f = tripStore.flight
      requests.push(api.post('/bookings/flights', {
        booking_type: 'FLIGHT',
        flight: {
          offer_token: f.offer_token,
          airline_name: f.airline_name,
          airline_code: f.airline_code,
          airline_logo_url: f.airline_logo_url,
          departure_airport_code: f.departure?.airport_code ?? f.departure_airport_code,
          departure_airport_name: f.departure?.airport_name ?? f.departure_airport_name,
          departure_city: f.departure?.city ?? f.departure_city,
          departure_datetime: f.departure?.datetime ?? f.departure_datetime,
          arrival_airport_code: f.arrival?.airport_code ?? f.arrival_airport_code,
          arrival_airport_name: f.arrival?.airport_name ?? f.arrival_airport_name,
          arrival_city: f.arrival?.city ?? f.arrival_city,
          arrival_datetime: f.arrival?.datetime ?? f.arrival_datetime,
          stops: f.stops ?? 0,
          duration_minutes: f.duration_minutes,
          price: f.price ?? f.price_usd,
          currency: f.currency,
          trip_type: f.trip_type ?? 'ONEWAY',
        },
      }))
    }

    // Hotel: search uses `hotel_id` + omits dates; schema needs external_hotel_id + dates
    if (tripStore.hotel) {
      const h = tripStore.hotel
      requests.push(api.post('/bookings/hotels', {
        booking_type: 'HOTEL',
        hotel: {
          external_hotel_id: h.hotel_id,
          hotel_name: h.hotel_name,
          accommodation_type: h.accommodation_type,
          star_class: h.star_class,
          city: h.city,
          address: h.address,
          checkin_date: startDate.value,
          checkout_date: endDate.value,
          total_price: h.total_price,
          price_per_night: h.price_per_night,
          currency: h.currency,
          photo_url: h.photo_url,
          booking_url: h.booking_url,
        },
      }))
    }

    // Activities: schema requires start_date/end_date and price > 0.
    // Free activities can't be booked through this endpoint — silently skip them.
    for (const a of (tripStore.activities ?? [])) {
      if (!a.price || a.price <= 0) continue
      requests.push(api.post('/bookings/attractions', {
        booking_type: 'ATTRACTION',
        attraction: {
          offer_token: a.offer_token,
          name: a.name,
          description: a.description,
          city: a.city,
          price: a.price,
          currency: a.currency,
          rating: a.rating,
          has_free_cancellation: a.has_free_cancellation ?? false,
          start_date: startDate.value,
          end_date: endDate.value,
          photo_url: a.photo_url,
          booking_url: a.booking_url,
        },
      }))
    }

    if (requests.length === 0) {
      alert('Pick at least one paid item (flight, hotel, or paid activity) before booking.')
      return
    }

    await Promise.all(requests)
    tripStore.clearCart()
    router.push({ name: 'dashboard' })
  } catch (err) {
    const detail = err.response?.data?.detail
    let msg = err.message
    if (Array.isArray(detail)) {
      msg = detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join('\n')
    } else if (typeof detail === 'string') {
      msg = detail
    }
    alert('Booking failed:\n' + msg)
    console.error('Full error:', err.response?.data)
  } finally {
    bookingInProgress.value = false
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <!-- Page error -->
    <div v-if="pageError" class="bg-red-50 border border-red-200 text-red-600 rounded-xl p-4 mb-6">
      {{ pageError }}
    </div>

    <!-- Trip total banner (sticky below the app header) -->
    <div
      v-if="tripStore.totalCost > 0"
      :class="bannerClass"
      class="sticky top-16 z-40 border rounded-xl px-4 py-3 mb-6 flex flex-wrap items-center gap-4 shadow-sm"
    >
      <div class="flex-1 grid grid-cols-4 gap-4 text-sm">
        <div>
          <span class="opacity-70 text-xs">Flights</span>
          <p class="font-bold">${{ tripStore.flightCost.toFixed(2) }}</p>
        </div>
        <div>
          <span class="opacity-70 text-xs">Hotels</span>
          <p class="font-bold">${{ tripStore.hotelCost.toFixed(2) }}</p>
        </div>
        <div>
          <span class="opacity-70 text-xs">Activities</span>
          <p class="font-bold">${{ tripStore.activitiesCost.toFixed(2) }}</p>
        </div>
        <div>
          <span class="opacity-70 text-xs">Total</span>
          <p class="font-bold">${{ tripStore.totalCost.toFixed(2) }}</p>
        </div>
      </div>
      <p class="text-sm font-semibold whitespace-nowrap">
        {{ tripStore.percentUsed.toFixed(0) }}% of ${{ tripStore.budget }} budget
      </p>
      <button
        @click="bookTrip"
        :disabled="bookingInProgress || tripStore.percentUsed > 100"
        :title="tripStore.percentUsed > 100 ? `Over budget by $${(tripStore.totalCost - tripStore.budget).toFixed(2)}` : ''"
        class="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium rounded-md whitespace-nowrap"
      >
        {{ bookingInProgress ? 'Booking…' : 'Book Now' }}
      </button>
    </div>

    <!-- Page heading -->
    <h1 class="text-2xl font-bold text-slate-800 mb-1">Results for {{ destination }}</h1>
    <p class="text-slate-500 text-sm mb-8">
      Budget: ${{ budget }} · {{ travelers }} traveler{{ travelers > 1 ? 's' : '' }}
    </p>

    <!-- Flights -->
    <section class="mb-10">
      <h2 class="text-xl font-semibold text-slate-700 mb-4">✈️ Flights</h2>
      <p v-if="loadingFlights" class="text-slate-400 text-sm">Loading flights…</p>
      <p v-else-if="flightMessage" class="text-slate-500 italic text-sm">{{ flightMessage }}</p>
      <div v-else-if="flights.length" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FlightCard v-for="f in flights" :key="f.offer_token" :flight="f" />
      </div>
      <p v-else class="text-slate-400 text-sm">No flights found.</p>
    </section>

    <!-- Hotels -->
    <section class="mb-10">
      <h2 class="text-xl font-semibold text-slate-700 mb-4">🏨 Hotels</h2>
      <p v-if="loadingHotels" class="text-slate-400 text-sm">Loading hotels…</p>
      <template v-else>
        <p v-if="hotelMessage" class="text-slate-500 italic text-sm mb-4">{{ hotelMessage }}</p>
        <div v-if="hotels.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <HotelCard v-for="h in hotels" :key="h.hotel_id" :hotel="h" />
        </div>
        <p v-else-if="!hotelMessage" class="text-slate-400 text-sm">No hotels found.</p>
      </template>
    </section>

    <!-- Activities -->
    <section class="mb-10">
      <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
        <h2 class="text-xl font-semibold text-slate-700">🎡 Activities</h2>
        <ActivityFilter @change="onFilterChange" />
      </div>
      <p v-if="loadingAttractions" class="text-slate-400 text-sm">Loading activities…</p>
      <p v-else-if="attractionMessage" class="text-slate-500 italic text-sm">{{ attractionMessage }}</p>
      <div v-else-if="attractions.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <AttractionCard v-for="a in attractions" :key="a.offer_token" :attraction="a" />
      </div>
      <p v-else class="text-slate-400 text-sm">No activities found.</p>
    </section>
  </div>
</template>
