<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../services/api'
import { useTripStore } from '../stores/trip'
import FlightCard from '../components/FlightCard.vue'
import HotelCard from '../components/HotelCard.vue'
import AttractionCard from '../components/AttractionCard.vue'
import ActivityFilter from '../components/ActivityFilter.vue'

const route = useRoute()
const tripStore = useTripStore()

// Read search params from the query string SearchView sends
const destination = computed(() => route.query.destination || '')
const origin      = computed(() => route.query.origin || '')
const budget      = computed(() => parseFloat(route.query.budget) || 1500)
const startDate   = computed(() => route.query.start_date || '')
const endDate     = computed(() => route.query.end_date || '')
const travelers   = computed(() => parseInt(route.query.travelers) || 1)

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

const MOCK_ATTRACTIONS = [
  { offer_token: 'mock-1', name: 'Free Walking Tour of London', description: 'Explore the city on foot.', price: 0, currency: 'USD', rating: 4.8, review_count: 312, city: 'London', photo_url: null, booking_url: null },
  { offer_token: 'mock-2', name: 'Hyde Park Self-Guided Walk', description: 'A peaceful stroll through royal parklands.', price: 0, currency: 'USD', rating: 4.5, review_count: 198, city: 'London', photo_url: null, booking_url: null },
  { offer_token: 'mock-3', name: 'Tower Bridge Photo Walk', description: 'Iconic views of Tower Bridge.', price: 0, currency: 'USD', rating: 4.7, review_count: 87, city: 'London', photo_url: null, booking_url: null },
  { offer_token: 'mock-4', name: 'British Museum Highlights Tour', description: 'Guided highlights of world history.', price: 22, currency: 'USD', rating: 4.9, review_count: 541, city: 'London', photo_url: null, booking_url: null },
  { offer_token: 'mock-5', name: 'Thames River Evening Cruise', description: 'Sunset cruise along the Thames.', price: 45, currency: 'USD', rating: 4.6, review_count: 230, city: 'London', photo_url: null, booking_url: null },
  { offer_token: 'mock-6', name: 'Harry Potter Studio Tour', description: 'Behind-the-scenes look at the films.', price: 89, currency: 'USD', rating: 4.9, review_count: 1024, city: 'London', photo_url: null, booking_url: null },
]

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
    // Fall back to mock data so the filter UI is always demonstrable
    const tierRanges = { free: [0, 0.01], under_25: [0.01, 25], '25_75': [25, 75], '75_plus': [75, Infinity] }
    const range = tier ? tierRanges[tier] : null
    attractions.value = range
      ? MOCK_ATTRACTIONS.filter(a => a.price >= range[0] && a.price < range[1])
      : MOCK_ATTRACTIONS
    attractionMessage.value = null
  } finally {
    loadingAttractions.value = false
  }
}

// ActivityFilter emits an array; backend accepts one tier — use the first selected
function onFilterChange(tiers) {
  fetchAttractions(tiers[0] || null)
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
      <p v-else-if="hotelMessage" class="text-slate-500 italic text-sm">{{ hotelMessage }}</p>
      <div v-else-if="hotels.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <HotelCard v-for="h in hotels" :key="h.hotel_id" :hotel="h" />
      </div>
      <p v-else class="text-slate-400 text-sm">No hotels found.</p>
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
import { useTripStore } from '../stores/trip'
import TripTotalWidget from '../components/TripTotalWidget.vue'

const trip = useTripStore()

// === Test fixtures (T14 will replace with real search results) ===
const sampleFlight = {
  offer_token: 'demo-flight-1',
  airline_name: 'British Airways',
  airline_code: 'BA',
  departure_airport_code: 'SFO',
  departure_airport_name: 'San Francisco Intl',
  departure_city: 'San Francisco',
  departure_datetime: '2026-09-18T10:30:00',
  arrival_airport_code: 'LHR',
  arrival_airport_name: 'Heathrow',
  arrival_city: 'London',
  arrival_datetime: '2026-09-19T05:45:00',
  duration_minutes: 615,
  price: 800,
  currency: 'USD',
}

const sampleHotel = {
  external_hotel_id: 123,
  hotel_name: 'YHA London Central',
  star_class: 3,
  city: 'London',
  checkin_date: '2026-09-19',
  checkout_date: '2026-09-25',
  total_price: 450,
  currency: 'USD',
}

const sampleActivity1 = {
  offer_token: 'demo-act-1',
  name: 'Free Walking Tour: City of London',
  price: 0,
  currency: 'USD',
  start_date: '2026-09-20',
  end_date: '2026-09-25',
}

const sampleActivity2 = {
  offer_token: 'demo-act-2',
  name: 'Tower of London Tickets',
  price: 50,
  currency: 'USD',
  start_date: '2026-09-21',
  end_date: '2026-09-21',
}

// === Test buttons ===
function addFlight() { trip.setFlight(sampleFlight) }
function addHotel() { trip.setHotel(sampleHotel) }
function addFreeActivity() { trip.addActivity(sampleActivity1) }
function addPaidActivity() { trip.addActivity(sampleActivity2) }
function addExpensiveItem() {
  trip.setFlight({ ...sampleFlight, offer_token: 'expensive', price: 2000 })
}
function reset() { trip.clearCart() }
</script>

<template>
  <div class="grid grid-cols-3 gap-6 mt-6">
    <!-- Main content (will be flight/hotel/activity cards in T14) -->
    <div class="col-span-2 space-y-4">
      <h2 class="text-2xl font-bold text-slate-800">Search Results</h2>
      <p class="text-sm text-slate-600">
        Placeholder — Anahi's T14 will populate this with real flight/hotel/attraction cards.
        For now, use the buttons below to mutate the trip cart and watch the Trip Total widget update.
      </p>

      <div class="bg-white rounded-lg shadow p-4 space-y-3">
        <h3 class="font-semibold text-slate-700">🧪 Trip cart smoke test</h3>
        <div class="flex flex-wrap gap-2">
          <button @click="addFlight" class="px-3 py-1.5 bg-blue-100 text-blue-800 rounded text-sm hover:bg-blue-200">
            Add $800 flight
          </button>
          <button @click="addHotel" class="px-3 py-1.5 bg-purple-100 text-purple-800 rounded text-sm hover:bg-purple-200">
            Add $450 hotel
          </button>
          <button @click="addFreeActivity" class="px-3 py-1.5 bg-emerald-100 text-emerald-800 rounded text-sm hover:bg-emerald-200">
            Add free activity
          </button>
          <button @click="addPaidActivity" class="px-3 py-1.5 bg-amber-100 text-amber-800 rounded text-sm hover:bg-amber-200">
            Add $50 activity
          </button>
          <button @click="addExpensiveItem" class="px-3 py-1.5 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200">
            Swap to $2000 flight (over budget)
          </button>
          <button @click="reset" class="px-3 py-1.5 bg-slate-200 text-slate-800 rounded text-sm hover:bg-slate-300">
            Clear cart
          </button>
        </div>
      </div>
    </div>

    <!-- Sidebar: Trip Total widget -->
    <aside class="col-span-1">
      <TripTotalWidget />
    </aside>
  </div>
</template>
