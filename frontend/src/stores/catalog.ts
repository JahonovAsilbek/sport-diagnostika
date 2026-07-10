import { defineStore } from 'pinia'
import { ref } from 'vue'

import * as catalogApi from '@/api/catalog'
import type { AgeCategory, District, Exercise, Region, SportType } from '@/types/catalog'

// Reference data rarely changes → cache it once per session (FRNTND-8). The small global lists
// load together via ensureLoaded(); districts are fetched + memoized per region (cascade pickers).
export const useCatalogStore = defineStore('catalog', () => {
  const regions = ref<Region[]>([])
  const sportTypes = ref<SportType[]>([])
  const ageCategories = ref<AgeCategory[]>([])
  const exercises = ref<Exercise[]>([])
  const loaded = ref(false)
  let loading: Promise<void> | null = null

  async function ensureLoaded(): Promise<void> {
    if (loaded.value) return
    loading ??= (async () => {
      const [r, s, a, e] = await Promise.all([
        catalogApi.getRegions(),
        catalogApi.getSportTypes(),
        catalogApi.getAgeCategories(),
        catalogApi.getExercises(),
      ])
      regions.value = r
      sportTypes.value = s
      ageCategories.value = a
      exercises.value = e
      loaded.value = true
    })().finally(() => {
      loading = null
    })
    return loading
  }

  const districtsByRegion = ref<Record<number, District[]>>({})
  async function districtsFor(region: number): Promise<District[]> {
    if (!districtsByRegion.value[region]) {
      districtsByRegion.value[region] = await catalogApi.getDistricts(region)
    }
    return districtsByRegion.value[region]
  }

  return { regions, sportTypes, ageCategories, exercises, loaded, ensureLoaded, districtsFor }
})
