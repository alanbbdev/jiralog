<script setup>
import { ArrowDown, Search } from '@lucide/vue'

const props = defineProps({
  filteredEntries: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  search: {
    type: String,
    default: '',
  },
  dateLabel: {
    type: Function,
    required: true,
  },
  hoursLabel: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['update:search'])
</script>

<template>
  <section id="apontamentos" class="panel table-panel">
    <div class="panel-head table-head">
      <div>
        <h2>Apontamentos recentes</h2>
        <p>{{ props.filteredEntries.length }} registros encontrados</p>
      </div>

      <label class="search">
        <Search :size="17" />
        <input
          :value="props.search"
          placeholder="Buscar issue, pessoa ou descricao"
          @input="emit('update:search', $event.target.value)"
        />
      </label>
    </div>

    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Issue</th>
            <th>Data</th>
            <th class="align-right">
              Tempo
              <ArrowDown :size="13" />
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="entry in props.filteredEntries.slice(0, 12)" :key="entry.id">
            <td>
              <a href="#">{{ entry.issueKey }}</a>
              <span>{{ entry.summary }}</span>
            </td>
            <td>{{ props.dateLabel(entry.date) }}</td>
            <td class="align-right"><strong>{{ props.hoursLabel(entry.hours) }}</strong></td>
          </tr>

          <tr v-if="!props.loading && !props.filteredEntries.length">
            <td colspan="3" class="empty-state">Nenhum apontamento encontrado para estes filtros.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
