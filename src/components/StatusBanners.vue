<script setup>
import { Activity, X } from '@lucide/vue'

const props = defineProps({
  demo: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['clear-error'])
</script>

<template>
  <div v-if="props.demo" class="demo-banner">
    <Activity :size="18" />
    <span>
      <strong>Explorando com dados de exemplo.</strong>
      Adicione suas credenciais em <code>backend/.env</code> e defina <code>DEMO_MODE=false</code> para conectar o Jira.
    </span>
  </div>

  <div v-if="props.error" class="error-banner">
    <span>{{ props.error }}</span>
    <button aria-label="Fechar erro" @click="emit('clear-error')">
      <X :size="17" />
    </button>
  </div>
</template>
