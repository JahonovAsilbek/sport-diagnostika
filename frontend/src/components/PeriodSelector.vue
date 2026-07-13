<script setup lang="ts">
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  PERIOD_TYPES,
  cleanPeriod,
  type PeriodParams,
  type PeriodType,
} from '@/composables/usePeriodQuery'

// v-model of PeriodParams. Empty (no type) = "latest overall". Picking a type defaults the year to
// the current one and the index to 1 so the selection is always a valid BCKND-70 combo.
const model = defineModel<PeriodParams>({ default: () => ({}) })
const { t } = useI18n({ useScope: 'global' })

const CURRENT_YEAR = new Date().getFullYear()

const typeOptions = computed(() => [
  { value: '', label: t('period.all') },
  ...PERIOD_TYPES.map((value) => ({ value, label: t(`enums.periodType.${value}`) })),
])

const indexOptions = computed(() => {
  const type = model.value.period_type
  if (type !== 'quarter' && type !== 'half') return []
  const count = type === 'quarter' ? 4 : 2
  const key = type === 'quarter' ? 'period.quarterN' : 'period.halfN'
  return Array.from({ length: count }, (_, i) => ({ value: i + 1, label: t(key, { n: i + 1 }) }))
})

const type = computed<PeriodType | ''>({
  get: () => model.value.period_type ?? '',
  set: (value) => {
    model.value = cleanPeriod(
      value
        ? {
            period_type: value,
            period_year: model.value.period_year ?? CURRENT_YEAR,
            period_index: value === 'year' ? undefined : (model.value.period_index ?? 1),
          }
        : {},
    )
  },
})

const year = computed<number>({
  get: () => model.value.period_year ?? CURRENT_YEAR,
  set: (value) => {
    if (value) model.value = cleanPeriod({ ...model.value, period_year: value })
  },
})

const index = computed<number>({
  get: () => model.value.period_index ?? 1,
  set: (value) => {
    if (value) model.value = cleanPeriod({ ...model.value, period_index: value })
  },
})
</script>

<template>
  <div class="period">
    <Select
      v-model="type"
      :options="typeOptions"
      option-label="label"
      option-value="value"
      :aria-label="$t('period.label')"
      class="period__type"
    />
    <InputNumber
      v-if="model.period_type"
      v-model="year"
      :min="2000"
      :max="2100"
      :use-grouping="false"
      :aria-label="$t('enums.periodType.year')"
      class="period__year"
    />
    <Select
      v-if="indexOptions.length"
      v-model="index"
      :options="indexOptions"
      option-label="label"
      option-value="value"
      :aria-label="$t('period.label')"
      class="period__index"
    />
  </div>
</template>

<style scoped>
.period {
  display: inline-flex;
  gap: 0.5rem;
  align-items: center;
}
.period__type {
  min-width: 9rem;
}
.period__year {
  width: 6rem;
}
.period__index {
  min-width: 7rem;
}
</style>
