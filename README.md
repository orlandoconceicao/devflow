# DevFlow

Plataforma SaaS multi-tenant para freelancers, agências e pequenas equipes administrarem clientes, projetos, tarefas, horas, finanças, cobranças e colaboração em um único workspace.

[Aplicação](https://devflow-frontend-delta.vercel.app) · [API](https://devflow-backend-swart.vercel.app) · [Repositório](https://github.com/orlandoconceicao/devflow)

## Estado atual

O DevFlow possui autenticação por email e JWT, workspaces isolados, controle de acesso por função e módulos operacionais integrados. A aplicação pública está implantada na Vercel, com frontend e backend em projetos separados.

Principais funcionalidades:

- cadastro, login, logout com blacklist do refresh token, recuperação de senha e perfil com preview de avatar;
- organizações multi-tenant com papéis `OWNER`, `ADMIN` e `MEMBER`;
- convites de equipe por email em HTML e texto, com aceite seguro, aprovação de alterações e chat interno;
- clientes, projetos, membros de projeto, atividades e dashboard;
- tarefas em Kanban, responsáveis, labels, comentários e anexos privados;
- controle de horas, custos, receitas, despesas, faturas e relatórios CSV;
- cobranças Pix responsivas, com resumo antes da confirmação, e assinatura Pro integradas ao Mercado Pago;
- portal do cliente, convites, entregas, aprovações e notificações;
- preferências persistentes de idioma português/inglês, timezone, tema claro/escuro e notificações;
- health checks, testes automatizados, CI e imagens Docker.

## Arquitetura e tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | React 19, TypeScript, Vite, React Router, TanStack Query, Axios, React Hook Form, Zod |
| Backend | Python, Django 5.2, Django REST Framework, SimpleJWT, Channels, Celery |
| Dados e infraestrutura | PostgreSQL, Redis opcional, Docker Compose, Nginx |
| Integrações | Gmail/SMTP, Mercado Pago e suporte opcional à WhatsApp Cloud API |
| Qualidade | Vitest, Testing Library, Django TestCase, Ruff, ESLint, Prettier, Coverage, GitHub Actions |

O frontend preserva a organização selecionada, separa o cache do TanStack Query por `organization_id` e envia `X-Organization-ID` nas operações vinculadas ao workspace. O backend valida a membership ativa e aplica o isolamento da organização em cada consulta; o header seleciona o contexto, mas não concede autorização. `OWNER` e `ADMIN` podem criar projetos, enquanto `MEMBER` mantém acesso operacional sem receber permissão administrativa implicitamente.

Ao sair, o frontend remove access token, refresh token, contexto da organização e usuário global antes de aguardar a rede. O backend coloca o refresh token na blacklist; a aplicação substitui a entrada atual do histórico pela tela de login. Avatares JPG/JPEG, PNG e WebP passam por validação de MIME, assinatura do arquivo e limite máximo inclusivo de 10 MB no backend e no frontend.

## Estrutura

```text
devflow/
├── backend/              # API Django e tarefas Celery
│   ├── apps/             # accounts, organizations, subscriptions, work, finance, portal
│   └── config/           # settings, URLs, ASGI, WSGI e Celery
├── frontend/             # SPA React/Vite
│   └── src/              # pages, components, features, services, layouts e tipos
├── deploy/               # configuração Nginx para Docker/VPS
├── docs/                 # arquitetura e implantação
├── tests/                # testes transversais do repositório
├── docker-compose.yml    # desenvolvimento
└── docker-compose.prod.yml
```

Consulte [frontend/README.md](frontend/README.md) e [backend/README.md](backend/README.md) para detalhes de cada aplicação.

## Execução local com Docker

Pré-requisitos: Docker Engine e Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

No Windows PowerShell, use `Copy-Item .env.example .env` no lugar de `cp`.

- Frontend: <http://localhost:5173>
- API: <http://localhost:8000/api>
- Health: <http://localhost:8000/health/>

O backend aplica migrations e sincroniza os planos ao iniciar. O Compose também sobe PostgreSQL, Redis, worker e beat do Celery. Para criar os dados de demonstração:

```bash
docker compose exec backend python manage.py seed_demo
```

Credenciais locais: `demo@devflow.local` / `DevFlowDemo!2026`.

## Execução manual

Requer Python 3.13, Node.js 22, PostgreSQL 16 e, opcionalmente, Redis 7.

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py seed_plans
python backend/manage.py runserver
```

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

Ao executar o backend fora do Docker, use `DB_HOST=localhost`. Se usar Redis local, defina `REDIS_URL=redis://localhost:6379/0`; dentro do Compose os hosts são `db` e `redis`.

## Variáveis de ambiente

Use `.env.example` como referência local e `.env.production.example` como referência de produção. Nunca versione chaves ou senhas reais.

Grupos principais:

- Django: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DJANGO_SETTINGS_MODULE`;
- origens: `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`;
- banco: `DATABASE_URL` ou `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`;
- filas: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CELERY_TASK_ALWAYS_EAGER`;
- email: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`;
- pagamentos: `MERCADO_PAGO_ENVIRONMENT`, `MERCADO_PAGO_ACCESS_TOKEN`, `MERCADO_PAGO_WEBHOOK_SECRET`, `MERCADO_PAGO_BASE_URL`;
- frontend: `VITE_API_URL`, `VITE_PROXY_TARGET` e, quando houver infraestrutura compatível, `VITE_WS_URL`.

Sem `REDIS_URL`, o backend usa cache e Channels em memória e tarefas Celery eager. Para Gmail, `EMAIL_HOST_PASSWORD` deve conter uma senha de app configurada também no ambiente de produção.

Os convites de equipe são enviados em formato multipart: HTML com botão de aceite e uma alternativa em texto simples. O link é pessoal, de uso único e expira em 7 dias.

## Testes e qualidade

```bash
python tests/run_all.py
python -m coverage run --rcfile=pyproject.toml backend/manage.py test apps
python -m coverage report --rcfile=pyproject.toml
ruff check backend tests

cd frontend
npm run lint
npm run test:coverage
npm run build
```

A suíte cobre regressões de autenticação/logout, seleção e isolamento de organizações, criação de projetos por Owner/Admin, financeiro e limite de queries, criação de cobranças, idioma e upload de avatar no limite de 10 MB. O dashboard financeiro agrega custo e duração no banco, e a página carrega apenas o endpoint da aba ativa para evitar trabalho desnecessário. A integração contínua também verifica migrations, cobertura mínima do backend, auditoria de dependências e build das imagens Docker. Consulte [tests/README.md](tests/README.md) para comandos específicos e critérios de novos testes.

## Deploy na Vercel

Produção atual:

- Frontend: <https://devflow-frontend-delta.vercel.app>
- Backend: <https://devflow-backend-swart.vercel.app>

Configure dois projetos na Vercel, apontando seus diretórios raiz para `frontend` e `backend`. No frontend, defina `VITE_API_URL=https://devflow-backend-swart.vercel.app/api`. No backend, use as URLs públicas exatas em `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` e `ALLOWED_HOSTS`.

Como a Vercel não mantém um worker Celery tradicional, a configuração atual usa `REDIS_URL` vazio e `CELERY_TASK_ALWAYS_EAGER=True`. Defina as credenciais SMTP, incluindo a senha de app em `EMAIL_HOST_PASSWORD`, no ambiente **Production** do projeto backend e faça um novo deploy após alterá-las.

O fallback em [frontend/vercel.json](frontend/vercel.json) entrega `index.html` para as rotas da SPA. O endpoint do Mercado Pago deve apontar para `https://devflow-backend-swart.vercel.app/api/webhooks/mercado-pago/`.

## Segurança

Tokens de convite são armazenados como hash, uploads exigem autorização e validação de conteúdo, JWTs usam rotação e blacklist, e webhooks de pagamento são validados e processados de forma idempotente. Querysets e serializers validam organização, cliente, projeto e papel mesmo quando IDs ou `X-Organization-ID` são enviados manualmente. Consulte [SECURITY.md](SECURITY.md) para contato e política de reporte.

## Autor

Orlando Conceição Vilhalba de Almeida

- [GitHub](https://github.com/orlandoconceicao)
- [LinkedIn](https://www.linkedin.com/in/orlando-concei%C3%A7%C3%A3o-582234315)
- [Portfólio](https://orlandoconceicao.github.io/)
