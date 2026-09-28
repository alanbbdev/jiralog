<script setup>
import { Plus } from '@lucide/vue'

const props = defineProps({
  status: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['create-worklog'])

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
      <button class="primary-button" @click="emit('create-worklog')">
        <Plus :size="17" />
        Novo apontamento
      </button>
    </div>
  </header>
</template>
