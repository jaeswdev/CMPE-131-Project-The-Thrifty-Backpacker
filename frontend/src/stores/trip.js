// src/stores/trip.js
//
// Trip cart — what the user has added before clicking Book Now.
//
// Deliberately NOT persisted to localStorage:
//   - Cart state should clear on refresh (standard shopping-cart UX)
//   - Persistence is for bookings (POST /bookings on Book Now click)
//
// State shape:
//   budget: number          — what the user typed on the search form
//   currency: string        — defaults to USD
//   flight: object | null   — one flight (replaces if user picks another)
//   hotel: object | null    — one hotel (same — single selection)
//   activities: array       — multiple allowed
//
// Getters:
//   totalCost     — flight.price + hotel.total_price + sum(activities.price)
//   percentUsed   — (total / budget) * 100
//   status        — 'green' | 'yellow' | 'red' per US-3 AC 3
//   isOverBudget  — true if percentUsed > 100 (used to disable Book Now)

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTripStore = defineStore('trip', () => {
  const budget = ref(1500)
  const currency = ref('USD')
  const flight = ref(null)
  const hotel = ref(null)
  const activities = ref([])

  // === Pricing math ===
  const flightCost = computed(() => flight.value?.price ?? 0)
  const hotelCost = computed(() => hotel.value?.total_price ?? 0)
  const activitiesCost = computed(() =>
    activities.value.reduce((sum, a) => sum + (a.price ?? 0), 0)
  )
  const totalCost = computed(() =>
    flightCost.value + hotelCost.value + activitiesCost.value
  )

  const percentUsed = computed(() =>
    budget.value > 0 ? (totalCost.value / budget.value) * 100 : 0
  )

  // US-3 AC 3.2 thresholds, mirrored from backend trip.py
  const status = computed(() => {
    if (percentUsed.value <= 90) return 'green'
    if (percentUsed.value <= 100) return 'yellow'
    return 'red'
  })

  const isOverBudget = computed(() => percentUsed.value > 100)

  // === Mutations ===
  function setBudget(amount, curr = 'USD') {
    budget.value = amount
    currency.value = curr
  }

  function setFlight(newFlight) {
    flight.value = newFlight  // null clears
  }

  function setHotel(newHotel) {
    hotel.value = newHotel
  }

  function addActivity(activity) {
    // Avoid duplicates by offer_token
    if (!activities.value.find(a => a.offer_token === activity.offer_token)) {
      activities.value.push(activity)
    }
  }

  function removeActivity(offerToken) {
    activities.value = activities.value.filter(a => a.offer_token !== offerToken)
  }

  function isActivitySelected(offerToken) {
    return activities.value.some(a => a.offer_token === offerToken)
  }

  function clearCart() {
    flight.value = null
    hotel.value = null
    activities.value = []
  }

  return {
    budget,
    currency,
    flight,
    hotel,
    activities,
    flightCost,
    hotelCost,
    activitiesCost,
    totalCost,
    percentUsed,
    status,
    isOverBudget,
    setBudget,
    setFlight,
    setHotel,
    addActivity,
    removeActivity,
    isActivitySelected,
    clearCart,
  }
})