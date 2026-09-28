<script setup>
import { Plus } from '@lucide/vue'

const props = defineProps({
  status: {
    type: Object,
    required: true,
  },
  currentView: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['create-worklog', 'change-view'])

function userInitials(name) {
  return (name || '')
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
}
</script>

<template>
  <header class="topbar">
    <div class="view-switch" role="tablist" aria-label="Navegacao principal">
      <button
        class="view-tab"
        :class="{ active: props.currentView === 'dashboard' }"
        role="tab"
        :aria-selected="props.currentView === 'dashboard'"
        @click="emit('change-view', 'dashboard')"
      >
        Dashboard
      </button>
      <button
        class="view-tab"
        :class="{ active: props.currentView === 'report' }"
        role="tab"
        :aria-selected="props.currentView === 'report'"
        @click="emit('change-view', 'report')"
      >
        Report
      </button>
    </div>

    <div class="top-user">
      <div class="avatar">
        {{ userInitials(props.status.user) }}
      </div>
      <div>
        <strong>{{ props.status.user }}</strong>
        <span class="connection" :class="{ live: props.status.connected }">
          <i></i>
          {{ props.status.demo ? 'Dados de demonstracao' : props.status.connected ? 'Jira sincronizado' : 'Jira desconectado' }}
        </span>
      </div>
    </div>
    <div class="top-actions">
      <button v-if="props.currentView === 'dashboard'" class="primary-button" @click="emit('create-worklog')">
        <Plus :size="17" />
        Novo apontamento
      </button>
    </div>
  </header>
</template>
