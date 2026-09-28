<script setup>
import { Clock3, X } from '@lucide/vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  saving: {
    type: Boolean,
    default: false,
  },
  statusDemo: {
    type: Boolean,
    default: false,
  },
  worklog: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['close', 'submit', 'update:worklog'])

function updateField(field, value) {
  emit('update:worklog', { ...props.worklog, [field]: value })
}
</script>

<template>
  <div v-if="props.show" class="modal-backdrop" @mousedown.self="emit('close')">
    <form class="modal" @submit.prevent="emit('submit')">
      <div class="modal-head">
        <div>
          <p class="eyebrow">JIRA WORKLOG</p>
          <h2>Novo apontamento</h2>
        </div>
        <button type="button" aria-label="Fechar" @click="emit('close')">
          <X :size="20" />
        </button>
      </div>

      <label>
        Issue do Jira
        <input
          :value="props.worklog.issue_key"
          required
          placeholder="Ex.: PLAT-142"
          @input="updateField('issue_key', $event.target.value)"
        />
      </label>

      <div class="form-row">
        <label>
          Horas
          <input
            :value="props.worklog.hours"
            required
            type="number"
            min="0.25"
            max="24"
            step="0.25"
            @input="updateField('hours', Number($event.target.value))"
          />
        </label>

        <label>
          Data
          <input
            :value="props.worklog.date"
            required
            type="date"
            @input="updateField('date', $event.target.value)"
          />
        </label>
      </div>

      <label>
        Descricao
        <textarea
          :value="props.worklog.comment"
          rows="4"
          placeholder="O que foi realizado?"
          @input="updateField('comment', $event.target.value)"
        ></textarea>
      </label>

      <p v-if="props.statusDemo" class="modal-note">O envio fica disponivel quando o Jira estiver conectado.</p>

      <div class="modal-actions">
        <button type="button" class="secondary-button" @click="emit('close')">Cancelar</button>
        <button class="primary-button" :disabled="props.saving || props.statusDemo">
          <Clock3 :size="17" />
          {{ props.saving ? 'Registrando...' : 'Registrar horas' }}
        </button>
      </div>
    </form>
  </div>
</template>
