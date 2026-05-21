<script setup>
import { computed } from 'vue'
import { useTripStore } from '../stores/trip'

const props = defineProps({
  hotel: { type: Object, required: true }
})

const tripStore = useTripStore()

const inTrip = computed(() => tripStore.hotel?.hotel_id === props.hotel.hotel_id)

function toggle() {
  if (inTrip.value) {
    tripStore.setHotel(null)
  } else {
    tripStore.setHotel(props.hotel)
  }
}

const stars = computed(() => {
  const n = props.hotel.star_class || 0
  return '★'.repeat(n) + '☆'.repeat(Math.max(0, 5 - n))
})

const reviewBadgeColor = computed(() => {
  const s = props.hotel.review_score || 0
  if (s >= 9) return 'bg-green-600'
  if (s >= 8) return 'bg-green-500'
  if (s >= 7) return 'bg-yellow-500'
  return 'bg-slate-400'
})
</script>

<template>
  <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition flex flex-col">
    <!-- Photo -->
    <div class="h-40 bg-slate-100 overflow-hidden">
      <img
        v-if="hotel.photo_url"
        :src="hotel.photo_url"
        :alt="hotel.hotel_name"
        class="w-full h-full object-cover"
        @error="$event.target.style.display = 'none'"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-4xl text-slate-300">🏨</div>
    </div>

    <div class="p-4 flex flex-col gap-2 flex-1">
      <!-- Name + type + city -->
      <div>
        <h3 class="font-semibold text-slate-800 leading-tight">{{ hotel.hotel_name }}</h3>
        <p class="text-xs text-slate-500 mt-0.5">
          <span v-if="hotel.accommodation_type">{{ hotel.accommodation_type }} · </span>
          {{ hotel.city }}
          <span v-if="hotel.distance_to_center_km"> · {{ hotel.distance_to_center_km.toFixed(1) }}km from center</span>
        </p>
      </div>

      <!-- Stars -->
      <p v-if="hotel.star_class" class="text-amber-400 text-sm leading-none">{{ stars }}</p>

      <!-- Review score -->
      <div v-if="hotel.review_score" class="flex items-center gap-2">
        <span :class="reviewBadgeColor" class="text-white text-xs font-bold px-1.5 py-0.5 rounded">
          {{ hotel.review_score.toFixed(1) }}
        </span>
        <span class="text-xs text-slate-500">
          {{ hotel.review_score_word }}
          <span v-if="hotel.review_count">({{ hotel.review_count.toLocaleString() }} reviews)</span>
        </span>
      </div>

      <!-- Price + button -->
      <div class="mt-auto flex items-end justify-between pt-2 border-t border-slate-100">
        <div>
          <p class="text-xl font-bold text-slate-800">${{ hotel.total_price.toFixed(2) }}</p>
          <p v-if="hotel.price_per_night" class="text-xs text-slate-500">
            ${{ hotel.price_per_night.toFixed(2) }} / night
          </p>
        </div>
        <button
          @click="toggle"
          :class="inTrip
            ? 'bg-slate-100 text-slate-700 hover:bg-red-50 hover:text-red-600 border border-slate-300'
            : 'bg-blue-600 text-white hover:bg-blue-700'"
          class="px-4 py-1.5 rounded-lg text-sm font-medium transition"
        >
          {{ inTrip ? 'Remove' : 'Add to trip' }}
        </button>
      </div>
    </div>
  </div>
</template>
