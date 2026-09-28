<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Bar, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
} from 'chart.js'
import {
  Activity,
  ArrowDown,
  BriefcaseBusiness,
  CalendarDays,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  FileClock,
  LayoutDashboard,
  LogOut,
  Menu,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Users,
  X,
} from '@lucide/vue'
import { eachDayOfInterval, format, startOfMonth,  startOfWeek,subDays } from 'date-fns'
import { ptBR } from 'date-fns/locale'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip)

const today = new Date()
const startDate = ref(format(startOfMonth(today), 'yyyy-MM-dd'))
const endDate = ref(format(today, 'yyyy-MM-dd'))
const entries = ref([])
const status = ref({ connected: false, demo: true, user: 'Carregando...' })
const loading = ref(true)
const error = ref('')
const search = ref('')
const selectedProject = ref('Todos os projetos')
const selectedPerson = ref('Todas as pessoas')
const mobileNav = ref(false)
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
    const matchesProject = selectedProject.value === 'Todos os projetos' || entry.project === selectedProject.value
    const matchesPerson = selectedPerson.value === 'Todas as pessoas' || entry.author === selectedPerson.value
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
const expectedHours = computed(() => businessDays.value * 9 * (selectedPerson.value === 'Todas as pessoas' ? people.value.length || 1 : 1))
const utilization = computed(() => expectedHours.value ? Math.round((totalHours.value / expectedHours.value) * 100) : 0)
const averageHours = computed(() => businessDays.value ? totalHours.value / businessDays.value : 0)

const dailyChart = computed(() => {
  const totals = new Map()
  filteredEntries.value.forEach((entry) => totals.set(entry.date, (totals.get(entry.date) || 0) + entry.hours))
  const days = eachDayOfInterval({
    start: new Date(`${startDate.value}T12:00:00`),
    end: new Date(`${endDate.value}T12:00:00`),
  })
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

onMounted(() => {
    setPeriod(1)
    Promise.all([loadStatus(), loadDashboard()])

})
</script>

<template>
  <div class="app-shell">
    <main class="main">
        <header class="topbar">
        <div class="top-user">
            <div class="avatar">
                {{ status.user?.split(' ').map((part) => part[0]).slice(0, 2).join('') }}
            </div>
            <div>
                <strong>{{ status.user }}</strong>
                <span class="connection" :class="{ live: status.connected }"><i></i>{{ status.demo ? 'Dados de demonstracao' : status.connected ? 'Jira sincronizado' : 'Jira desconectado' }}</span>
            </div>
        </div>
        <div class="top-actions">
          <button class="primary-button" @click="showModal = true"><Plus :size="17" /> Novo apontamento</button>
        </div>
      </header>

      <div class="content">
        <section class="heading-row">
          <div><p class="eyebrow">PAINEL DE HORAS</p><h1>Como o tempo esta sendo investido?</h1><p>Acompanhe o ritmo da equipe e mantenha os apontamentos em dia.</p></div>
          <button class="refresh-button" :disabled="loading" title="Atualizar dados" @click="loadDashboard"><RefreshCw :size="18" :class="{ spin: loading }" /> Atualizar</button>
        </section>

        <div v-if="status.demo" class="demo-banner"><Activity :size="18" /><span><strong>Explorando com dados de exemplo.</strong> Adicione suas credenciais em <code>backend/.env</code> e defina <code>DEMO_MODE=false</code> para conectar o Jira.</span></div>
        <div v-if="error" class="error-banner"><span>{{ error }}</span><button aria-label="Fechar erro" @click="error = ''"><X :size="17" /></button></div>

        <section class="filters" aria-label="Filtros do dashboard">
          <div class="quick-period"><button @click="setPeriod(1)">Hoje</button><button @click="setPeriod(7)">7 dias</button><button @click="startDate = format(startOfWeek(today), 'yyyy-MM-dd')">Esta semana</button><button @click="setPeriod(30)">30 dias</button><button @click="startDate = format(startOfMonth(today), 'yyyy-MM-dd')">Este mês</button></div>
          <label><CalendarDays :size="17" /><span>De</span><input v-model="startDate" type="date" /></label>
          <span class="date-separator">ate</span>
          <label><span class="sr-only">Ate</span><input v-model="endDate" type="date" /></label>
          <label class="select-wrap"><BriefcaseBusiness :size="17" /><select v-model="selectedProject"><option>Todos os projetos</option><option v-for="project in projects" :key="project">{{ project }}</option></select><ChevronDown :size="15" /></label>
          <!-- <label class="select-wrap"><Users :size="17" /><select v-model="selectedPerson"><option>Todas as pessoas</option><option v-for="person in people" :key="person">{{ person }}</option></select><ChevronDown :size="15" /></label> -->
        </section>

        <section class="metric-grid">
          <article class="metric"><div class="metric-icon blue"><Clock3 :size="20" /></div><div><span>Horas apontadas</span><strong>{{ hoursLabel(totalHours) }}</strong><small><b>+8,4%</b> vs. periodo anterior</small></div></article>
          <article class="metric"><div class="metric-icon teal"><Check :size="20" /></div><div><span>Aproveitamento</span><strong>{{ utilization }}%</strong><small>{{ hoursLabel(expectedHours) }} previstas no periodo</small></div></article>
          <article class="metric"><div class="metric-icon orange"><Activity :size="20" /></div><div><span>Media por dia</span><strong>{{ hoursLabel(averageHours) }}</strong><small>{{ businessDays }} dias uteis analisados</small></div></article>
          <article class="metric"><div class="metric-icon yellow"><BriefcaseBusiness :size="20" /></div><div><span>Projetos ativos</span><strong>{{ projectTotals.length }}</strong><small>{{ people.length }} pessoas com registros</small></div></article>
        </section>

        <section class="charts-grid">
          <article class="panel daily-panel">
            <div class="panel-head"><div><h2>Horas por dia</h2><p>Volume total de apontamentos no periodo</p></div><span class="panel-total">{{ hoursLabel(totalHours) }}</span></div>
            <div class="bar-chart"><Bar v-if="!loading" :data="dailyChart" :options="barOptions" /><div v-else class="skeleton chart-skeleton"></div></div>
          </article>
          <article id="projetos" class="panel project-panel">
            <div class="panel-head"><div><h2>Por projeto</h2><p>Distribuicao das horas</p></div></div>
            <div class="project-chart-wrap">
              <div class="doughnut"><Doughnut v-if="projectTotals.length" :data="projectChart" :options="doughnutOptions" /><div class="doughnut-label"><strong>{{ hoursLabel(totalHours) }}</strong><span>total</span></div></div>
              <div class="legend"><div v-for="item in projectTotals" :key="item.name"><i :style="{ background: item.color }"></i><span>{{ item.name }}</span><strong>{{ hoursLabel(item.value) }}</strong></div></div>
            </div>
          </article>
        </section>

        <section id="apontamentos" class="panel table-panel">
          <div class="panel-head table-head"><div><h2>Apontamentos recentes</h2><p>{{ filteredEntries.length }} registros encontrados</p></div><label class="search"><Search :size="17" /><input v-model="search" placeholder="Buscar issue, pessoa ou descricao" /></label></div>
          <div class="table-scroll">
            <table>
              <thead><tr><th>Issue</th><th>Projeto</th><th>Responsavel</th><th>Data</th><th class="align-right">Tempo <ArrowDown :size="13" /></th></tr></thead>
              <tbody>
                <tr v-for="entry in filteredEntries.slice(0, 12)" :key="entry.id">
                  <td><a href="#">{{ entry.issueKey }}</a><span>{{ entry.summary }}</span></td>
                  <td><span class="project-name"><i :style="{ background: entry.projectColor }"></i>{{ entry.project }}</span></td>
                  <td><span class="person"><b>{{ entry.initials }}</b>{{ entry.author }}</span></td>
                  <td>{{ dateLabel(entry.date) }}</td>
                  <td class="align-right"><strong>{{ hoursLabel(entry.hours) }}</strong></td>
                </tr>
                <tr v-if="!loading && !filteredEntries.length"><td colspan="5" class="empty-state">Nenhum apontamento encontrado para estes filtros.</td></tr>
              </tbody>
            </table>
          </div>
        </section>
        <footer>Atualizado agora · Fonte: Jira Cloud</footer>
      </div>
    </main>

    <div v-if="showModal" class="modal-backdrop" @mousedown.self="showModal = false">
      <form class="modal" @submit.prevent="saveWorklog">
        <div class="modal-head"><div><p class="eyebrow">JIRA WORKLOG</p><h2>Novo apontamento</h2></div><button type="button" aria-label="Fechar" @click="showModal = false"><X :size="20" /></button></div>
        <label>Issue do Jira<input v-model="worklog.issue_key" required placeholder="Ex.: PLAT-142" /></label>
        <div class="form-row"><label>Horas<input v-model.number="worklog.hours" required type="number" min="0.25" max="24" step="0.25" /></label><label>Data<input v-model="worklog.date" required type="date" /></label></div>
        <label>Descricao<textarea v-model="worklog.comment" rows="4" placeholder="O que foi realizado?"></textarea></label>
        <p v-if="status.demo" class="modal-note">O envio fica disponivel quando o Jira estiver conectado.</p>
        <div class="modal-actions"><button type="button" class="secondary-button" @click="showModal = false">Cancelar</button><button class="primary-button" :disabled="saving || status.demo"><Clock3 :size="17" />{{ saving ? 'Registrando...' : 'Registrar horas' }}</button></div>
      </form>
    </div>
    <div v-if="toast" class="toast"><Check :size="18" />{{ toast }}</div>
  </div>
</template>