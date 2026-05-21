<script setup>
import { computed } from 'vue'
import { useTripStore } from '../stores/trip'

const props = defineProps({
  attraction: { type: Object, required: true }
})

const tripStore = useTripStore()

const inTrip = computed(() => tripStore.isActivitySelected(props.attraction.offer_token))

function toggle() {
  if (inTrip.value) {
    tripStore.removeActivity(props.attraction.offer_token)
  } else {
    tripStore.addActivity(props.attraction)
  }
}

const isFree = computed(() => props.attraction.price === 0)

const shortDesc = computed(() => {
  const d = props.attraction.description || ''
  return d.length > 100 ? d.slice(0, 100) + '…' : d
})
</script>

<template>
  <div class="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition flex flex-col">
    <!-- Photo -->
    <div class="h-36 bg-slate-100 overflow-hidden relative">
      <img
        v-if="attraction.photo_url"
        :src="attraction.photo_url"
        :alt="attraction.name"
        class="w-full h-full object-cover"
        @error="$event.target.style.display = 'none'"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-4xl text-slate-300">🎡</div>

      <!-- Overlay badges -->
      <div class="absolute top-2 right-2 flex flex-col gap-1">
        <span v-if="attraction.is_bestseller"
          class="bg-amber-400 text-amber-900 text-xs font-bold px-2 py-0.5 rounded shadow">
          Bestseller
        </span>
        <span v-if="attraction.has_free_cancellation"
          class="bg-green-100 text-green-700 text-xs font-medium px-2 py-0.5 rounded shadow">
          Free cancel
        </span>
      </div>
    </div>

    <div class="p-4 flex flex-col gap-2 flex-1">
      <h3 class="font-semibold text-slate-800 leading-tight">{{ attraction.name }}</h3>
      <p v-if="shortDesc" class="text-xs text-slate-500">{{ shortDesc }}</p>

      <!-- Rating -->
      <div v-if="attraction.rating" class="flex items-center gap-1 text-xs text-slate-500">
        <span class="text-amber-400">★</span>
        <span>{{ attraction.rating.toFixed(1) }}</span>
        <span v-if="attraction.review_count">({{ attraction.review_count.toLocaleString() }})</span>
      </div>

      <!-- Price + button — AC 2.4: "Free" must be prominent when price = 0 -->
      <div class="mt-auto flex items-center justify-between pt-2 border-t border-slate-100">
        <span v-if="isFree" class="text-green-600 font-bold text-lg">Free</span>
        <span v-else class="text-xl font-bold text-slate-800">${{ attraction.price.toFixed(2) }}</span>

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
