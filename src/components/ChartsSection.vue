<script setup>
import { Bar, Doughnut } from 'vue-chartjs'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  dailyChart: {
    type: Object,
    required: true,
  },
  barOptions: {
    type: Object,
    required: true,
  },
  projectTotals: {
    type: Array,
    default: () => [],
  },
  projectChart: {
    type: Object,
    required: true,
  },
  doughnutOptions: {
    type: Object,
    required: true,
  },
  hoursLabel: {
    type: Function,
    required: true,
  },
  totalHours: {
    type: Number,
    required: true,
  },
})
</script>

<template>
  <section class="charts-grid">
    <article class="panel daily-panel">
      <div class="panel-head">
        <div>
          <h2>Horas por dia</h2>
          <p>Volume total de apontamentos no periodo</p>
        </div>
        <span class="panel-total">{{ props.hoursLabel(props.totalHours) }}</span>
      </div>

      <div class="bar-chart">
        <Bar v-if="!props.loading" :data="props.dailyChart" :options="props.barOptions" />
        <div v-else class="skeleton chart-skeleton"></div>
      </div>
    </article>

    <article id="projetos" class="panel project-panel">
      <div class="panel-head">
        <div>
          <h2>Por projeto</h2>
          <p>Distribuicao das horas</p>
        </div>
      </div>

      <div class="project-chart-wrap">
        <div class="doughnut">
          <Doughnut
            v-if="props.projectTotals.length"
            :data="props.projectChart"
            :options="props.doughnutOptions"
          />
          <div class="doughnut-label">
            <strong>{{ props.hoursLabel(props.totalHours) }}</strong>
            <span>total</span>
          </div>
        </div>

        <div class="legend">
          <div v-for="item in props.projectTotals" :key="item.name">
            <i :style="{ background: item.color }"></i>
            <span>{{ item.name }}</span>
            <strong>{{ props.hoursLabel(item.value) }}</strong>
          </div>
        </div>
      </div>
    </article>
  </section>
</template>
