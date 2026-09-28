# Tempo

Dashboard de timelog do Jira com frontend Vue 3 e backend FastAPI. A chave da API fica somente no backend e nunca e enviada ao navegador.

## Configuracao

1. Crie um token em <https://id.atlassian.com/manage-profile/security/api-tokens>.
2. Copie `backend/.env.example` para `backend/.env`.
3. Preencha `JIRA_BASE_URL`, `JIRA_EMAIL` e `JIRA_API_TOKEN`.
4. Defina `DEMO_MODE=false` para consultar dados reais.

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
npm install
npm run build
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Abra <http://127.0.0.1:8000>. Para desenvolver o frontend com hot reload, execute `npm run dev` em outro terminal e abra <http://127.0.0.1:5173>.

## Seguranca

O arquivo `backend/.env` esta ignorado pelo Git. Nao coloque tokens em variaveis `VITE_*`, pois elas sao incorporadas ao bundle publico do frontend.