<script setup>
import { computed, ref } from 'vue'
import { eachDayOfInterval, endOfWeek, format, startOfWeek } from 'date-fns'
import { ptBR } from 'date-fns/locale'

const props = defineProps({
  entries: {
    type: Array,
    default: () => [],
  },
  startDate: {
    type: String,
    required: true,
  },
  endDate: {
    type: String,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const groupMode = ref('day')
const exporting = ref(false)

function entryHours(entry) {
  if (typeof entry.hours === 'number') {
    return entry.hours
  }
  if (typeof entry.seconds === 'number') {
    return entry.seconds / 3600
  }
  return 0
}

function weekLabel(day) {
  const start = startOfWeek(day, { weekStartsOn: 1 })
  const end = endOfWeek(day, { weekStartsOn: 1 })
  return `${format(start, 'dd/MM')} ate ${format(end, 'dd/MM')}`
}

function groupLabel(entry) {
  const day = new Date(`${entry.date}T12:00:00`)
  return groupMode.value === 'day'
    ? format(day, "dd/MM/yyyy (EEE)", { locale: ptBR })
    : `Semana ${weekLabel(day)}`
}

function sortValue(entry) {
  const day = new Date(`${entry.date}T12:00:00`)
  if (groupMode.value === 'day') {
    return day.getTime()
  }
  return startOfWeek(day, { weekStartsOn: 1 }).getTime()
}

const groupedRows = computed(() => {
  const bucket = new Map()

  props.entries.forEach((entry) => {
    const label = groupLabel(entry)
    const current = bucket.get(label) || {
      label,
      firstDate: sortValue(entry),
      totalHours: 0,
      logs: 0,
      issues: new Set(),
      people: new Set(),
    }

    current.totalHours += entryHours(entry)
    current.logs += 1
    current.issues.add(entry.issueKey)
    current.people.add(entry.author)
    current.firstDate = Math.min(current.firstDate, sortValue(entry))

    bucket.set(label, current)
  })

  return [...bucket.values()]
    .sort((a, b) => a.firstDate - b.firstDate)
    .map((row) => ({
      ...row,
      totalHours: Number(row.totalHours.toFixed(2)),
      issuesCount: row.issues.size,
      peopleCount: row.people.size,
    }))
})

const totalHours = computed(() => Number(props.entries.reduce((sum, entry) => sum + entryHours(entry), 0).toFixed(2)))
const totalLogs = computed(() => props.entries.length)

function hourClockLabel(value) {
  const totalMinutes = Math.round(value * 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours}:${String(minutes).padStart(2, '0')}`
}

const weekDays = computed(() => {
  if (!props.startDate || !props.endDate) {
    return []
  }

  const start = new Date(`${props.startDate}T12:00:00`)
  const end = new Date(`${props.endDate}T12:00:00`)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || start > end) {
    return []
  }

  return eachDayOfInterval({ start, end })
    .filter((day) => day.getDay() !== 0 && day.getDay() !== 6)
    .map((day) => ({
      key: format(day, 'yyyy-MM-dd'),
      label: format(day, 'EEE dd', { locale: ptBR }),
    }))
})

const weekRows = computed(() => {
  const dayKeys = new Set(weekDays.value.map((day) => day.key))
  const bucket = new Map()

  props.entries.forEach((entry) => {
    if (!dayKeys.has(entry.date)) {
      return
    }

    const key = entry.issueKey || 'Sem chave'
    const current = bucket.get(key) || {
      issueKey: key,
      summary: entry.summary || 'Sem resumo',
      logs: 0,
      totalHours: 0,
      dayHours: Object.fromEntries(weekDays.value.map((day) => [day.key, 0])),
    }

    const hours = entryHours(entry)
    current.logs += 1
    current.totalHours += hours
    current.dayHours[entry.date] = Number(((current.dayHours[entry.date] || 0) + hours).toFixed(2))
    bucket.set(key, current)
  })

  return [...bucket.values()]
    .map((row) => ({
      ...row,
      totalHours: Number(row.totalHours.toFixed(2)),
    }))
    .sort((a, b) => b.totalHours - a.totalHours)
})

const weekDayTotals = computed(() => {
  return weekDays.value.map((day) => {
    const sum = weekRows.value.reduce((acc, row) => acc + (row.dayHours[day.key] || 0), 0)
    return Number(sum.toFixed(2))
  })
})

const jiraRows = computed(() => {
  const bucket = new Map()

  props.entries.forEach((entry) => {
    const key = entry.issueKey || 'Sem chave'
    const current = bucket.get(key) || {
      issueKey: key,
      summary: entry.summary || 'Sem resumo',
      totalHours: 0,
      logs: 0,
    }

    current.totalHours += entryHours(entry)
    current.logs += 1
    bucket.set(key, current)
  })

  return [...bucket.values()]
    .map((row) => ({
      ...row,
      totalHours: Number(row.totalHours.toFixed(2)),
    }))
    .sort((a, b) => b.totalHours - a.totalHours)
})

const tableConfig = computed(() => {
  if (groupMode.value === 'jira') {
    return {
      title: 'Agrupado por Jira',
      subtitle: 'Total de horas por issue no periodo selecionado.',
      headers: ['Jira', 'Resumo', 'Total', 'Logs'],
      rows: jiraRows.value.map((row) => ({
        key: row.issueKey,
        values: [
          row.issueKey,
          row.summary,
          `${row.totalHours.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}h`,
          String(row.logs),
        ],
      })),
      rightAligned: new Set([2, 3]),
      emptyMessage: 'Nenhum Jira encontrado para os filtros selecionados.',
    }
  }

  return {
    title: groupMode.value === 'day' ? 'Agrupado por dia' : 'Agrupado por semana',
    subtitle: 'Consolidado por periodo com totais de logs, issues e pessoas.',
    headers: ['Grupo', 'Total', 'Logs', 'Issues', 'Pessoas'],
    rows: groupedRows.value.map((row) => ({
      key: row.label,
      values: [
        row.label,
        `${row.totalHours.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}h`,
        String(row.logs),
        String(row.issuesCount),
        String(row.peopleCount),
      ],
    })),
    rightAligned: new Set([1, 2, 3, 4]),
    emptyMessage: 'Nenhum log encontrado para os filtros selecionados.',
  }
})

async function exportPdf() {
  exporting.value = true
  try {
    const [{ default: jsPDF }, { default: autoTable }] = await Promise.all([
      import('jspdf'),
      import('jspdf-autotable'),
    ])

    const doc = new jsPDF({ unit: 'pt', format: 'a4' })
    const modeLabel = groupMode.value === 'day' ? 'Dia' : groupMode.value === 'week' ? 'Semana' : 'Jira'
    const title = `Report de Horas (${modeLabel})`
    const period = `Periodo: ${props.startDate} ate ${props.endDate}`

    doc.setFontSize(16)
    doc.text(title, 40, 48)
    doc.setFontSize(10)
    doc.setTextColor(90)
    doc.text(period, 40, 68)
    doc.text(`Total geral de horas: ${totalHours.value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}h`, 40, 84)

    if (groupMode.value === 'week') {
      autoTable(doc, {
        startY: 98,
        head: [[
          'Ticket',
          ...weekDays.value.map((day) => day.label),
          'Total',
        ]],
        body: weekRows.value.map((row) => [
          `${row.issueKey} - ${row.summary}`,
          ...weekDays.value.map((day) => {
            const value = row.dayHours[day.key] || 0
            return value > 0 ? hourClockLabel(value) : '-'
          }),
          hourClockLabel(row.totalHours),
        ]),
        styles: {
          fontSize: 8,
          cellPadding: 5,
        },
        headStyles: {
          fillColor: [22, 119, 255],
        },
        columnStyles: {
          0: { cellWidth: 180 },
          ...Object.fromEntries(
            weekDays.value.map((_, index) => [index + 1, { halign: 'center' }])
          ),
          [weekDays.value.length + 1]: { halign: 'right' },
        },
        foot: [[
          'Total',
          ...weekDayTotals.value.map((value) => value > 0 ? hourClockLabel(value) : '-'),
          hourClockLabel(totalHours.value),
        ]],
        footStyles: {
          fillColor: [239, 245, 255],
          textColor: [15, 56, 103],
          fontStyle: 'bold',
        },
      })
    } else {
      autoTable(doc, {
        startY: 98,
        head: [tableConfig.value.headers],
        body: tableConfig.value.rows.map((row) => row.values),
        styles: {
          fontSize: 9,
          cellPadding: 6,
        },
        headStyles: {
          fillColor: [22, 119, 255],
        },
        columnStyles: Object.fromEntries(
          [...tableConfig.value.rightAligned].map((index) => [index, { halign: 'right' }])
        ),
        foot: [[
          'Total geral',
          totalHours.value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
          totalLogs.value,
          ...new Array(Math.max(0, tableConfig.value.headers.length - 3)).fill(''),
        ]],
        footStyles: {
          fillColor: [239, 245, 255],
          textColor: [15, 56, 103],
          fontStyle: 'bold',
        },
      })
    }

    const fileName = `report-${groupMode.value}-${props.startDate}-${props.endDate}.pdf`
    doc.save(fileName)
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <section class="panel report-panel">
    <div class="panel-head report-head">
      <div>
        <h2>Report de horas</h2>
        <p>Agrupamento para exportacao PDF por dia ou por semana.</p>
      </div>

      <div class="report-actions">
        <div class="group-switch" role="radiogroup" aria-label="Modo de agrupamento">
          <button
            :class="{ active: groupMode === 'day' }"
            role="radio"
            :aria-checked="groupMode === 'day'"
            @click="groupMode = 'day'"
          >
            Dia
          </button>
          <button
            :class="{ active: groupMode === 'week' }"
            role="radio"
            :aria-checked="groupMode === 'week'"
            @click="groupMode = 'week'"
          >
            Semana
          </button>
          <button
            :class="{ active: groupMode === 'jira' }"
            role="radio"
            :aria-checked="groupMode === 'jira'"
            @click="groupMode = 'jira'"
          >
            Jira
          </button>
        </div>

        <button class="primary-button" :disabled="props.loading || (groupMode === 'week' ? !weekRows.length : !tableConfig.rows.length) || exporting" @click="exportPdf">
          {{ exporting ? 'Exportando...' : 'Exportar PDF' }}
        </button>
      </div>
    </div>

    <div class="report-totals">
      <div class="report-total-card">
        <span>Total geral de horas</span>
        <strong>{{ totalHours.toLocaleString('pt-BR', { maximumFractionDigits: 2 }) }}h</strong>
        <small>{{ totalLogs }} logs no periodo</small>
      </div>
      <div class="report-total-card">
        <span>Total de Jiras</span>
        <strong>{{ jiraRows.length }}</strong>
        <small>Use o modo Jira para ver o detalhamento</small>
      </div>
    </div>

    <div v-if="groupMode === 'week'" class="table-scroll">
      <table class="week-matrix-table">
        <thead>
          <tr>
            <th>Ticket</th>
            <th v-for="day in weekDays" :key="day.key" class="align-center">{{ day.label }}</th>
            <th class="align-right">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in weekRows" :key="row.issueKey">
            <td>
              <strong class="ticket-main">{{ row.issueKey }}</strong>
              <span class="ticket-sub">{{ row.summary }}</span>
            </td>
            <td v-for="day in weekDays" :key="`${row.issueKey}-${day.key}`" class="align-center">
              {{ row.dayHours[day.key] > 0 ? hourClockLabel(row.dayHours[day.key]) : '-' }}
            </td>
            <td class="align-right"><strong>{{ hourClockLabel(row.totalHours) }}</strong></td>
          </tr>
          <tr v-if="!props.loading && !weekRows.length">
            <td :colspan="weekDays.length + 2" class="empty-state">Nenhum ticket encontrado para os filtros selecionados.</td>
          </tr>
        </tbody>
        <tfoot v-if="weekRows.length">
          <tr>
            <td><strong>Total</strong></td>
            <td v-for="(total, index) in weekDayTotals" :key="`week-total-${index}`" class="align-center">
              <strong>{{ total > 0 ? hourClockLabel(total) : '-' }}</strong>
            </td>
            <td class="align-right"><strong>{{ hourClockLabel(totalHours) }}</strong></td>
          </tr>
        </tfoot>
      </table>
    </div>

    <div v-else class="table-scroll">
      <table>
        <thead>
          <tr>
            <th v-for="header in tableConfig.headers" :key="header">{{ header }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in tableConfig.rows" :key="row.key">
            <td
              v-for="(value, index) in row.values"
              :key="`${row.key}-${index}`"
              :class="{ 'align-right': tableConfig.rightAligned.has(index) }"
            >
              <strong v-if="index === 0">{{ value }}</strong>
              <span v-else>{{ value }}</span>
            </td>
          </tr>
          <tr v-if="!props.loading && !tableConfig.rows.length">
            <td :colspan="tableConfig.headers.length" class="empty-state">{{ tableConfig.emptyMessage }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
