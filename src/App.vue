<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
} from 'chart.js'
import { Check } from '@lucide/vue'
import { eachDayOfInterval, format, startOfMonth, startOfWeek, subDays } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import TopBar from './components/TopBar.vue'
import StatusBanners from './components/StatusBanners.vue'
import FiltersBar from './components/FiltersBar.vue'
import EntriesTable from './components/EntriesTable.vue'
import ChartsSection from './components/ChartsSection.vue'
import MetricsSection from './components/MetricsSection.vue'
import WorklogModal from './components/WorklogModal.vue'
import ReportSection from './components/ReportSection.vue'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip)

const today = new Date()

const ALL_PROJECTS = 'Todos os projetos'
const ALL_PEOPLE = 'Todas as pessoas'
const VALID_VIEWS = ['dashboard', 'report']
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/

function readUrlParams() {
  return new URLSearchParams(window.location.search)
}

const initialParams = readUrlParams()
const initialStart = initialParams.get('start')
const initialEnd = initialParams.get('end')
const initialView = initialParams.get('view')

const startDate = ref(DATE_PATTERN.test(initialStart) ? initialStart : format(today, 'yyyy-MM-dd'))
const endDate = ref(DATE_PATTERN.test(initialEnd) ? initialEnd : format(today, 'yyyy-MM-dd'))
const entries = ref([])
const status = ref({ connected: false, demo: true, user: 'Carregando...' })
const loading = ref(true)
const error = ref('')
const search = ref(initialParams.get('q') || '')
const currentView = ref(VALID_VIEWS.includes(initialView) ? initialView : 'dashboard')
const selectedProject = ref(initialParams.get('project') || ALL_PROJECTS)
const selectedPerson = ref(initialParams.get('person') || ALL_PEOPLE)
const showModal = ref(false)
const saving = ref(false)
const toast = ref('')
const worklog = ref({ issue_key: '', hours: 1, date: format(today, 'yyyy-MM-dd'), comment: '' })

const hours = (seconds) => seconds / 3600
const hoursLabel = (value) => `${value.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}h`
const dateLabel = (value) => format(new Date(`${value}T12:00:00`), "dd 'de' MMM", { locale: ptBR })

const projects = computed(() => [...new Set(entries.value.map((entry) => entry.project))].sort())
const people = computed(() => [...new Set(entries.value.map((entry) => entry.author))].sort())
const filteredEntries = computed(() => {
  const term = search.value.trim().toLowerCase()
  return entries.value.filter((entry) => {
    const matchesProject = selectedProject.value === ALL_PROJECTS || entry.project === selectedProject.value
    const matchesPerson = selectedPerson.value === ALL_PEOPLE || entry.author === selectedPerson.value
    const matchesSearch = !term || [entry.issueKey, entry.summary, entry.comment, entry.author]
      .some((value) => value.toLowerCase().includes(term))
    return matchesProject && matchesPerson && matchesSearch
  })
})

const totalHours = computed(() => filteredEntries.value.reduce((sum, entry) => sum + hours(entry.seconds), 0))
const businessDays = computed(() => eachDayOfInterval({
  start: new Date(`${startDate.value}T12:00:00`),
  end: new Date(`${endDate.value}T12:00:00`),
}).filter((day) => day.getDay() !== 0 && day.getDay() !== 6).length)
const expectedHours = computed(() => businessDays.value * 9 * (selectedPerson.value === ALL_PEOPLE ? people.value.length || 1 : 1))
const utilization = computed(() => expectedHours.value ? Math.round((totalHours.value / expectedHours.value) * 100) : 0)
const averageHours = computed(() => businessDays.value ? totalHours.value / businessDays.value : 0)

const dailyChart = computed(() => {
  const totals = new Map()
  filteredEntries.value.forEach((entry) => totals.set(entry.date, (totals.get(entry.date) || 0) + entry.hours))
  const days = eachDayOfInterval({
    start: new Date(`${startDate.value}T12:00:00`),
    end: new Date(`${endDate.value}T12:00:00`),
  }).filter((day) => day.getDay() !== 0 && day.getDay() !== 6)
  return {
    labels: days.map((day) => format(day, 'dd/MM')),
    datasets: [{
      data: days.map((day) => totals.get(format(day, 'yyyy-MM-dd')) || 0),
      backgroundColor: '#1677ff',
      hoverBackgroundColor: '#0b5fcc',
      borderRadius: 3,
      borderSkipped: false,
      maxBarThickness: 24,
    }],
  }
})

const projectTotals = computed(() => {
  const totals = new Map()
  filteredEntries.value.forEach((entry) => {
    const current = totals.get(entry.project) || { value: 0, color: entry.projectColor }
    current.value += entry.hours
    totals.set(entry.project, current)
  })
  return [...totals.entries()].map(([name, data]) => ({ name, ...data })).sort((a, b) => b.value - a.value)
})
const projectChart = computed(() => ({
  labels: projectTotals.value.map((item) => item.name),
  datasets: [{
    data: projectTotals.value.map((item) => item.value),
    backgroundColor: projectTotals.value.map((item) => item.color),
    borderWidth: 0,
    spacing: 2,
  }],
}))

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { displayColors: false } },
  scales: {
    x: { grid: { display: false }, border: { display: false }, ticks: { color: '#7a8998', maxTicksLimit: 12 } },
    y: { beginAtZero: true, grid: { color: '#edf1f4' }, border: { display: false }, ticks: { color: '#7a8998', callback: (value) => `${value}h` } },
  },
}
const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '72%',
  plugins: { legend: { display: false } },
}

async function api(path, options) {
  const response = await fetch(path, options)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || 'Nao foi possivel concluir a operacao.')
  }
  return response.json()
}

async function loadDashboard() {
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams({ start: startDate.value, end: endDate.value })
    const result = await api(`/api/dashboard?${params}`)
    entries.value = result.entries
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    loading.value = false
  }
}

async function loadStatus() {
  try {
    status.value = await api('/api/status')
  } catch (requestError) {
    status.value = { connected: false, demo: false, user: 'API indisponivel' }
  }
}

function setPeriod(days) {
  endDate.value = format(today, 'yyyy-MM-dd')
  startDate.value = format(subDays(today, days - 1), 'yyyy-MM-dd')
}

function setThisWeek() {
  startDate.value = format(startOfWeek(today), 'yyyy-MM-dd')
}

function setThisMonth() {
  startDate.value = format(startOfMonth(today), 'yyyy-MM-dd')
}

function clearError() {
  error.value = ''
}

function changeView(nextView) {
  currentView.value = nextView
}

function openModal() {
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

function updateWorklog(nextWorklog) {
  worklog.value = nextWorklog
}

async function saveWorklog() {
  saving.value = true
  error.value = ''
  try {
    await api('/api/worklogs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        issue_key: worklog.value.issue_key,
        seconds: Math.round(Number(worklog.value.hours) * 3600),
        started: `${worklog.value.date}T09:00:00-03:00`,
        comment: worklog.value.comment,
      }),
    })
    showModal.value = false
    toast.value = 'Apontamento registrado no Jira.'
    await loadDashboard()
    window.setTimeout(() => { toast.value = '' }, 3500)
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    saving.value = false
  }
}

let debounce
watch([startDate, endDate], () => {
  clearTimeout(debounce)
  debounce = window.setTimeout(loadDashboard, 250)
})

let syncingFromUrl = false

function buildQueryString() {
  const params = new URLSearchParams()
  const defaultDate = format(today, 'yyyy-MM-dd')
  if (startDate.value && startDate.value !== defaultDate) params.set('start', startDate.value)
  if (endDate.value && endDate.value !== defaultDate) params.set('end', endDate.value)
  if (currentView.value && currentView.value !== 'dashboard') params.set('view', currentView.value)
  if (selectedProject.value && selectedProject.value !== ALL_PROJECTS) params.set('project', selectedProject.value)
  if (selectedPerson.value && selectedPerson.value !== ALL_PEOPLE) params.set('person', selectedPerson.value)
  if (search.value) params.set('q', search.value)
  return params.toString()
}

function syncUrlFromState() {
  if (syncingFromUrl) return
  const query = buildQueryString()
  const next = `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`
  if (next !== `${window.location.pathname}${window.location.search}${window.location.hash}`) {
    window.history.replaceState(null, '', next)
  }
}

function syncStateFromUrl() {
  const params = readUrlParams()
  const nextStart = params.get('start')
  const nextEnd = params.get('end')
  const nextView = params.get('view')
  syncingFromUrl = true
  startDate.value = DATE_PATTERN.test(nextStart) ? nextStart : format(today, 'yyyy-MM-dd')
  endDate.value = DATE_PATTERN.test(nextEnd) ? nextEnd : format(today, 'yyyy-MM-dd')
  currentView.value = VALID_VIEWS.includes(nextView) ? nextView : 'dashboard'
  selectedProject.value = params.get('project') || ALL_PROJECTS
  selectedPerson.value = params.get('person') || ALL_PEOPLE
  search.value = params.get('q') || ''
  // Release the guard after Vue flushes watchers on next tick.
  window.setTimeout(() => { syncingFromUrl = false }, 0)
}

watch(
  [startDate, endDate, currentView, selectedProject, selectedPerson, search],
  syncUrlFromState,
)

function handlePopState() {
  syncStateFromUrl()
}

onMounted(() => {
  window.addEventListener('popstate', handlePopState)
  syncUrlFromState()
  Promise.all([loadStatus(), loadDashboard()])
})

onBeforeUnmount(() => {
  window.removeEventListener('popstate', handlePopState)
})
</script>

<template>
  <div class="app-shell">
    <main class="main">
      <TopBar :status="status" :current-view="currentView" @create-worklog="openModal" @change-view="changeView" />

      <div class="content">
        <StatusBanners :demo="status.demo" :error="error" @clear-error="clearError" />

        <FiltersBar
          v-model:start-date="startDate"
          v-model:end-date="endDate"
          v-model:selected-project="selectedProject"
          :projects="projects"
          :loading="loading"
          @set-period="setPeriod"
          @set-this-week="setThisWeek"
          @set-this-month="setThisMonth"
          @refresh="loadDashboard"
        />

        <div v-if="currentView === 'dashboard'" class="grid">
            <div class="grid-item">
                <EntriesTable
                v-model:search="search"
                :filtered-entries="filteredEntries"
                :loading="loading"
                :date-label="dateLabel"
                :hours-label="hoursLabel"
                />
            </div>
            <div class="grid-item">
                <ChartsSection
                singleColumn
                :loading="loading"
                :daily-chart="dailyChart"
                :bar-options="barOptions"
                :project-totals="projectTotals"
                :project-chart="projectChart"
                :doughnut-options="doughnutOptions"
                :hours-label="hoursLabel"
                :total-hours="totalHours"
                />
            </div>

        </div>
        <MetricsSection
          v-if="currentView === 'dashboard'"
          :total-hours="totalHours"
          :expected-hours="expectedHours"
          :utilization="utilization"
          :average-hours="averageHours"
          :business-days="businessDays"
          :project-count="projectTotals.length"
          :people-count="people.length"
          :hours-label="hoursLabel"
        />

        <ReportSection
          v-if="currentView === 'report'"
          :entries="filteredEntries"
          :start-date="startDate"
          :end-date="endDate"
          :loading="loading"
        />

        <footer>Atualizado agora · Fonte: Jira Cloud</footer>
      </div>
    </main>

    <WorklogModal
      :show="showModal"
      :saving="saving"
      :status-demo="status.demo"
      :worklog="worklog"
      @close="closeModal"
      @submit="saveWorklog"
      @update:worklog="updateWorklog"
    />

    <div v-if="toast" class="toast"><Check :size="18" />{{ toast }}</div>
  </div>
</template>