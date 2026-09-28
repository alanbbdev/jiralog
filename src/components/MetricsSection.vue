<script setup>
import { Activity, BriefcaseBusiness, Check, Clock3 } from '@lucide/vue'

const props = defineProps({
  totalHours: {
    type: Number,
    required: true,
  },
  expectedHours: {
    type: Number,
    required: true,
  },
  utilization: {
    type: Number,
    required: true,
  },
  averageHours: {
    type: Number,
    required: true,
  },
  businessDays: {
    type: Number,
    required: true,
  },
  projectCount: {
    type: Number,
    required: true,
  },
  peopleCount: {
    type: Number,
    required: true,
  },
  hoursLabel: {
    type: Function,
    required: true,
  },
})
</script>

<template>
  <section class="metric-grid">
    <article class="metric">
      <div class="metric-icon blue"><Clock3 :size="20" /></div>
      <div>
        <span>Horas apontadas</span>
        <strong>{{ props.hoursLabel(props.totalHours) }}</strong>
        <small><b>+8,4%</b> vs. periodo anterior</small>
      </div>
    </article>

    <article class="metric">
      <div class="metric-icon teal"><Check :size="20" /></div>
      <div>
        <span>Aproveitamento</span>
        <strong>{{ props.utilization }}%</strong>
        <small>{{ props.hoursLabel(props.expectedHours) }} previstas no periodo</small>
      </div>
    </article>

    <article class="metric">
      <div class="metric-icon orange"><Activity :size="20" /></div>
      <div>
        <span>Media por dia</span>
        <strong>{{ props.hoursLabel(props.averageHours) }}</strong>
        <small>{{ props.businessDays }} dias uteis analisados</small>
      </div>
    </article>

    <article class="metric">
      <div class="metric-icon yellow"><BriefcaseBusiness :size="20" /></div>
      <div>
        <span>Projetos ativos</span>
        <strong>{{ props.projectCount }}</strong>
        <small>{{ props.peopleCount }} pessoas com registros</small>
      </div>
    </article>
  </section>
</template>
