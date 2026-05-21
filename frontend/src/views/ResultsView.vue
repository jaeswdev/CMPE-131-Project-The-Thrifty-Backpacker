<script setup>
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