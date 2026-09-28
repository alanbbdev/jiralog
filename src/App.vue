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
  Lock,
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

const CREDENTIALS_STORAGE_KEY = 'timelog.jira.credentials.v1'
const PBKDF2_ITERATIONS = 210000

const today = new Date()
const startDate = ref(format(startOfMonth(today), 'yyyy-MM-dd'))
const endDate = ref(format(today, 'yyyy-MM-dd'))
const entries = ref([])
const status = ref({ connected: false, demo: true, user: 'Nao conectado' })
const loading = ref(true)
const error = ref('')
const search = ref('')
const selectedProject = ref('Todos os projetos')
const selectedPerson = ref('Todas as pessoas')
const showModal = ref(false)
const showCredentialsModal = ref(false)
const saving = ref(false)
const toast = ref('')
const worklog = ref({ issue_key: '', hours: 1, date: format(today, 'yyyy-MM-dd'), comment: '' })
const encryptedSessionExists = ref(false)
const unlockPassphrase = ref('')
const unlocking = ref(false)
const credentialsForm = ref({ baseUrl: '', email: '', apiToken: '', passphrase: '' })
const savingCredentials = ref(false)
const jiraCredentials = ref(null)

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

function projectColor(projectName) {
  const colors = ['#2563eb', '#14b8a6', '#f97316', '#eab308', '#db2777']
  return colors[[...projectName].reduce((sum, char) => sum + char.charCodeAt(0), 0) % colors.length]
}

function plainText(value) {
  if (typeof value === 'string') return value
  if (!value || typeof value !== 'object') return ''
  const texts = []
  for (const node of value.content || []) {
    if (!node || typeof node !== 'object') continue
    if (typeof node.text === 'string') texts.push(node.text)
    const nested = plainText(node)
    if (nested) texts.push(nested)
  }
  return texts.join(' ').trim()
}

function toBase64(bytes) {
  let binary = ''
  bytes.forEach((value) => {
    binary += String.fromCharCode(value)
  })
  return btoa(binary)
}

function fromBase64(value) {
  const binary = atob(value)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return bytes
}

async function deriveKey(passphrase, saltBytes) {
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(passphrase),
    'PBKDF2',
    false,
    ['deriveKey'],
  )
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: saltBytes, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  )
}

async function encryptCredentials(credentials, passphrase) {
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const salt = crypto.getRandomValues(new Uint8Array(16))
  const key = await deriveKey(passphrase, salt)
  const payload = new TextEncoder().encode(JSON.stringify(credentials))
  const cipher = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, payload)
  return {
    version: 1,
    iv: toBase64(iv),
    salt: toBase64(salt),
    cipher: toBase64(new Uint8Array(cipher)),
    iterations: PBKDF2_ITERATIONS,
  }
}

async function decryptCredentials(record, passphrase) {
  const iv = fromBase64(record.iv)
  const salt = fromBase64(record.salt)
  const key = await deriveKey(passphrase, salt)
  const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, fromBase64(record.cipher))
  return JSON.parse(new TextDecoder().decode(decrypted))
}

function readEncryptedSession() {
  try {
    const raw = sessionStorage.getItem(CREDENTIALS_STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function clearSessionCredentials() {
  sessionStorage.removeItem(CREDENTIALS_STORAGE_KEY)
  encryptedSessionExists.value = false
  jiraCredentials.value = null
  status.value = { connected: false, demo: true, user: 'Nao conectado' }
  entries.value = []
  toast.value = 'Credenciais removidas da sessao.'
  window.setTimeout(() => { toast.value = '' }, 3000)
}

async function saveCredentials() {
  if (!credentialsForm.value.baseUrl || !credentialsForm.value.email || !credentialsForm.value.apiToken) {
    error.value = 'Preencha URL, e-mail e API token do Jira.'
    return
  }
  if (credentialsForm.value.passphrase.length < 8) {
    error.value = 'Use uma senha da sessao com pelo menos 8 caracteres.'
    return
  }

  savingCredentials.value = true
  error.value = ''
  try {
    const normalized = {
      baseUrl: credentialsForm.value.baseUrl.trim().replace(/\/$/, ''),
      email: credentialsForm.value.email.trim(),
      apiToken: credentialsForm.value.apiToken.trim(),
    }
    const encrypted = await encryptCredentials(normalized, credentialsForm.value.passphrase)
    sessionStorage.setItem(CREDENTIALS_STORAGE_KEY, JSON.stringify(encrypted))
    jiraCredentials.value = normalized
    encryptedSessionExists.value = true
    credentialsForm.value.passphrase = ''
    showCredentialsModal.value = false
    toast.value = 'Credenciais salvas com criptografia na sessao.'
    window.setTimeout(() => { toast.value = '' }, 3500)
    await Promise.all([loadStatus(), loadDashboard()])
  } catch {
    error.value = 'Nao foi possivel criptografar as credenciais nesta sessao.'
  } finally {
    savingCredentials.value = false
  }
}

async function unlockCredentials() {
  const record = readEncryptedSession()
  if (!record) {
    encryptedSessionExists.value = false
    error.value = 'Nenhuma sessao criptografada foi encontrada.'
    return
  }
  if (!unlockPassphrase.value) {
    error.value = 'Informe a senha da sessao para desbloquear.'
    return
  }

  unlocking.value = true
  error.value = ''
  try {
    jiraCredentials.value = await decryptCredentials(record, unlockPassphrase.value)
    unlockPassphrase.value = ''
    toast.value = 'Sessao desbloqueada.'
    window.setTimeout(() => { toast.value = '' }, 3000)
    await Promise.all([loadStatus(), loadDashboard()])
  } catch {
    error.value = 'Senha invalida ou dados de sessao corrompidos.'
  } finally {
    unlocking.value = false
  }
}

function connectionLabel() {
  if (status.value.connected) return 'Jira conectado no navegador'
  if (encryptedSessionExists.value) return 'Sessao bloqueada'
  return 'Credenciais nao configuradas'
}

function authHeader() {
  if (!jiraCredentials.value) {
    throw new Error('Configure as credenciais do Jira para continuar.')
  }
  return `Basic ${btoa(`${jiraCredentials.value.email}:${jiraCredentials.value.apiToken}`)}`
}

async function jiraApi(path, options = {}) {
  const baseUrl = jiraCredentials.value?.baseUrl
  if (!baseUrl) throw new Error('Configure as credenciais do Jira para continuar.')

  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')
  headers.set('Authorization', authHeader())
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  let response
  try {
    response = await fetch(`${baseUrl}${path}`, { ...options, headers })
  } catch {
    throw new Error('Falha ao conectar com Jira. Verifique URL e CORS do navegador.')
  }

  if (!response.ok) {
    let detail = 'Nao foi possivel concluir a operacao no Jira.'
    try {
      const body = await response.json()
      detail = body.errorMessages?.[0] || body.errors?.[Object.keys(body.errors || {})[0]] || detail
    } catch {
      detail = response.statusText || detail
    }
    throw new Error(detail)
  }

  return response.status === 204 ? {} : response.json()
}

async function issuesWithWorklogs(start, end, project) {
  const filters = [
    `worklogDate >= "${start}"`,
    `worklogDate <= "${end}"`,
    'worklogAuthor = currentUser()',
  ]
  if (project && project !== 'Todos os projetos') {
    filters.push(`project = "${project.replaceAll('"', '\\"')}"`)
  }

  const issues = []
  let nextPageToken
  while (true) {
    const params = new URLSearchParams({
      jql: `${filters.join(' AND ')} ORDER BY updated DESC`,
      fields: 'summary,project,issuetype,status',
      maxResults: '100',
    })
    if (nextPageToken) params.set('nextPageToken', nextPageToken)
    const page = await jiraApi(`/rest/api/3/search/jql?${params.toString()}`)
    issues.push(...(page.issues || []))
    nextPageToken = page.nextPageToken
    if (page.isLast || !nextPageToken) break
  }
  return issues
}

async function issueWorklogs(issueKey) {
  const worklogs = []
  let startAt = 0
  while (true) {
    const params = new URLSearchParams({ startAt: String(startAt), maxResults: '100' })
    const page = await jiraApi(`/rest/api/3/issue/${issueKey}/worklog?${params.toString()}`)
    worklogs.push(...(page.worklogs || []))
    startAt += (page.worklogs || []).length
    if (startAt >= (page.total || 0)) break
  }
  return worklogs
}

async function loadDashboard() {
  if (!jiraCredentials.value) {
    loading.value = false
    entries.value = []
    return
  }

  loading.value = true
  error.value = ''
  try {
    const me = await jiraApi('/rest/api/3/myself')
    status.value = { connected: true, demo: false, user: me.displayName || me.emailAddress || 'Usuario Jira' }
    const issues = await issuesWithWorklogs(startDate.value, endDate.value, selectedProject.value)
    const worklogGroups = await Promise.all(issues.map((issue) => issueWorklogs(issue.key)))

    const normalized = []
    issues.forEach((issue, index) => {
      const fields = issue.fields || {}
      const projectName = fields.project?.name || 'Sem projeto'
      const logs = worklogGroups[index] || []

      logs.forEach((worklog) => {
        const worklogDate = (worklog.started || '').slice(0, 10)
        if (worklog.author?.accountId !== me.accountId) return
        if (worklogDate < startDate.value || worklogDate > endDate.value) return

        const displayName = worklog.author?.displayName || 'Usuario Jira'
        normalized.push({
          id: worklog.id,
          issueKey: issue.key,
          summary: fields.summary || 'Sem titulo',
          project: projectName,
          projectColor: projectColor(projectName),
          author: displayName,
          initials: displayName.split(' ').slice(0, 2).map((part) => part[0]).join('').toUpperCase(),
          date: worklogDate,
          seconds: worklog.timeSpentSeconds,
          hours: Number((worklog.timeSpentSeconds / 3600).toFixed(2)),
          comment: plainText(worklog.comment) || 'Sem comentario',
        })
      })
    })

    entries.value = normalized.sort((a, b) => b.date.localeCompare(a.date))
  } catch (requestError) {
    error.value = requestError.message
    status.value = { connected: false, demo: true, user: 'Nao conectado' }
  } finally {
    loading.value = false
  }
}

async function loadStatus() {
  if (!jiraCredentials.value) {
    status.value = {
      connected: false,
      demo: true,
      user: encryptedSessionExists.value ? 'Sessao protegida' : 'Nao conectado',
    }
    return
  }

  try {
    const me = await jiraApi('/rest/api/3/myself')
    status.value = { connected: true, demo: false, user: me.displayName || me.emailAddress || 'Usuario Jira' }
  } catch (requestError) {
    status.value = { connected: false, demo: true, user: 'Nao conectado' }
    error.value = requestError.message
  }
}

function setPeriod(days) {
  endDate.value = format(today, 'yyyy-MM-dd')
  startDate.value = format(subDays(today, days - 1), 'yyyy-MM-dd')
}

async function saveWorklog() {
  if (!jiraCredentials.value) {
    error.value = 'Configure as credenciais do Jira para registrar horas.'
    return
  }

  saving.value = true
  error.value = ''
  try {
    const payload = {
      timeSpentSeconds: Math.round(Number(worklog.value.hours) * 3600),
      started: `${worklog.value.date}T09:00:00.000-0300`,
    }
    if (worklog.value.comment?.trim()) {
      payload.comment = {
        type: 'doc',
        version: 1,
        content: [{ type: 'paragraph', content: [{ type: 'text', text: worklog.value.comment.trim() }] }],
      }
    }
    await jiraApi(`/rest/api/3/issue/${worklog.value.issue_key.toUpperCase()}/worklog`, {
      method: 'POST',
      body: JSON.stringify(payload),
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
watch([startDate, endDate, selectedProject], () => {
  clearTimeout(debounce)
  debounce = window.setTimeout(loadDashboard, 250)
})

onMounted(() => {
  setPeriod(1)
  encryptedSessionExists.value = Boolean(readEncryptedSession())
  loadStatus()
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
                  <span class="connection" :class="{ live: status.connected }"><i></i>{{ connectionLabel() }}</span>
            </div>
        </div>
        <div class="top-actions">
            <button class="secondary-button" @click="showCredentialsModal = true"><Settings :size="16" /> Credenciais Jira</button>
            <button class="primary-button" :disabled="!status.connected" @click="showModal = true"><Plus :size="17" /> Novo apontamento</button>
        </div>
      </header>

      <div class="content">
          <div v-if="!status.connected" class="demo-banner"><Activity :size="18" /><span><strong>Modo frontend-only ativo.</strong> Configure suas credenciais do Jira para consultar e registrar apontamentos direto do navegador.</span></div>
          <div v-if="encryptedSessionExists && !jiraCredentials" class="demo-banner">
            <Lock :size="18" />
            <span><strong>Sessao criptografada encontrada.</strong> Digite a senha para desbloquear sem reenviar token.</span>
            <div class="unlock-wrap">
              <input v-model="unlockPassphrase" type="password" placeholder="Senha da sessao" />
              <button class="secondary-button" :disabled="unlocking" @click="unlockCredentials">{{ unlocking ? 'Desbloqueando...' : 'Desbloquear' }}</button>
            </div>
          </div>
        <div v-if="error" class="error-banner"><span>{{ error }}</span><button aria-label="Fechar erro" @click="error = ''"><X :size="17" /></button></div>

        <section class="filters" aria-label="Filtros do dashboard">
          <div class="quick-period"><button @click="setPeriod(1)">Hoje</button><button @click="setPeriod(7)">7 dias</button><button @click="startDate = format(startOfWeek(today), 'yyyy-MM-dd')">Esta semana</button><button @click="setPeriod(30)">30 dias</button><button @click="startDate = format(startOfMonth(today), 'yyyy-MM-dd')">Este mês</button></div>
          <label><CalendarDays :size="17" /><span>De</span><input v-model="startDate" type="date" /></label>
          <span class="date-separator">ate</span>
          <label><span class="sr-only">Ate</span><input v-model="endDate" type="date" /></label>
          <label class="select-wrap"><BriefcaseBusiness :size="17" /><select v-model="selectedProject"><option>Todos os projetos</option><option v-for="project in projects" :key="project">{{ project }}</option></select><ChevronDown :size="15" /></label>
        <button class="refresh-button" :disabled="loading || !status.connected" title="Atualizar dados" @click="loadDashboard"><RefreshCw :size="18" :class="{ spin: loading }" /> Atualizar</button>
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
        <footer>Atualizado agora · Fonte: Jira Cloud (browser)</footer>
      </div>
    </main>

    <div v-if="showCredentialsModal" class="modal-backdrop" @mousedown.self="showCredentialsModal = false">
      <form class="modal" @submit.prevent="saveCredentials">
        <div class="modal-head"><div><p class="eyebrow">CONFIGURACAO</p><h2>Credenciais Jira</h2></div><button type="button" aria-label="Fechar" @click="showCredentialsModal = false"><X :size="20" /></button></div>
        <label>Base URL do Jira<input v-model="credentialsForm.baseUrl" required placeholder="https://suaempresa.atlassian.net" /></label>
        <label>E-mail<input v-model="credentialsForm.email" required type="email" placeholder="voce@empresa.com" /></label>
        <label>API Token<input v-model="credentialsForm.apiToken" required type="password" placeholder="Token gerado no Atlassian" /></label>
        <label>Senha da sessao (criptografia)<input v-model="credentialsForm.passphrase" required type="password" minlength="8" placeholder="Minimo 8 caracteres" /></label>
        <p class="modal-note">As credenciais sao criptografadas com AES-GCM e salvas apenas no sessionStorage desta aba.</p>
        <div class="modal-actions">
          <button v-if="encryptedSessionExists" type="button" class="secondary-button" @click="clearSessionCredentials">Limpar sessao</button>
          <button type="button" class="secondary-button" @click="showCredentialsModal = false">Cancelar</button>
          <button class="primary-button" :disabled="savingCredentials"><Check :size="17" />{{ savingCredentials ? 'Salvando...' : 'Salvar credenciais' }}</button>
        </div>
      </form>
    </div>

    <div v-if="showModal" class="modal-backdrop" @mousedown.self="showModal = false">
      <form class="modal" @submit.prevent="saveWorklog">
        <div class="modal-head"><div><p class="eyebrow">JIRA WORKLOG</p><h2>Novo apontamento</h2></div><button type="button" aria-label="Fechar" @click="showModal = false"><X :size="20" /></button></div>
        <label>Issue do Jira<input v-model="worklog.issue_key" required placeholder="Ex.: PLAT-142" /></label>
        <div class="form-row"><label>Horas<input v-model.number="worklog.hours" required type="number" min="0.25" max="24" step="0.25" /></label><label>Data<input v-model="worklog.date" required type="date" /></label></div>
        <label>Descricao<textarea v-model="worklog.comment" rows="4" placeholder="O que foi realizado?"></textarea></label>
        <p v-if="!status.connected" class="modal-note">Conecte o Jira no modal de credenciais para habilitar o envio.</p>
        <div class="modal-actions"><button type="button" class="secondary-button" @click="showModal = false">Cancelar</button><button class="primary-button" :disabled="saving || !status.connected"><Clock3 :size="17" />{{ saving ? 'Registrando...' : 'Registrar horas' }}</button></div>
      </form>
    </div>
    <div v-if="toast" class="toast"><Check :size="18" />{{ toast }}</div>
  </div>
</template>