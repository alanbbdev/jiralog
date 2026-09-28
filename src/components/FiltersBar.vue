<script setup>
import { BriefcaseBusiness, CalendarDays, ChevronDown, RefreshCw } from '@lucide/vue'

const props = defineProps({
  startDate: {
    type: String,
    required: true,
  },
  endDate: {
    type: String,
    required: true,
  },
  projects: {
    type: Array,
    default: () => [],
  },
  selectedProject: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update:startDate',
  'update:endDate',
  'update:selectedProject',
  'set-period',
  'set-this-week',
  'set-this-month',
  'refresh',
])
</script>

<template>
  <section class="filters" aria-label="Filtros do dashboard">
    <div class="quick-period">
      <button @click="emit('set-period', 1)">Hoje</button>
      <button @click="emit('set-period', 7)">7 dias</button>
      <button @click="emit('set-this-week')">Esta semana</button>
      <button @click="emit('set-period', 30)">30 dias</button>
      <button @click="emit('set-this-month')">Este mes</button>
    </div>

    <label>
      <CalendarDays :size="17" />
      <span>De</span>
      <input
        :value="props.startDate"
        type="date"
        @input="emit('update:startDate', $event.target.value)"
      />
    </label>

    <span class="date-separator">ate</span>

    <label>
      <span class="sr-only">Ate</span>
      <input
        :value="props.endDate"
        type="date"
        @input="emit('update:endDate', $event.target.value)"
      />
    </label>

    <label class="select-wrap">
      <BriefcaseBusiness :size="17" />
      <select
        :value="props.selectedProject"
        @change="emit('update:selectedProject', $event.target.value)"
      >
        <option>Todos os projetos</option>
        <option v-for="project in props.projects" :key="project">{{ project }}</option>
      </select>
      <ChevronDown :size="15" />
    </label>

    <button
      class="refresh-button"
      :disabled="props.loading"
      title="Atualizar dados"
      @click="emit('refresh')"
    >
      <RefreshCw :size="18" :class="{ spin: props.loading }" />
      Atualizar
    </button>
  </section>
</template>
