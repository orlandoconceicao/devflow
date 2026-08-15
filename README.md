# DevFlow

DevFlow é uma plataforma SaaS multi-tenant para freelancers, agências e pequenas equipes. Os Prompts 1 e 2 entregam autenticação, workspaces, RBAC, planos, clientes, projetos, equipes de projeto e dashboard com dados reais — sem pagamentos reais.

## Stack e arquitetura

- Backend: Python, Django 5, Django REST Framework, SimpleJWT, PostgreSQL.
- Frontend: React, TypeScript, Vite, React Router, TanStack Query, Axios, React Hook Form e Zod.
- Infra: Docker Compose com `frontend`, `backend` e `db`.
- Domínios backend: `accounts`, `organizations`, `subscriptions`, `work` e `core`.
- Frontend organizado em `components`, `features`, `layouts`, `pages`, `services` e `types`.

O isolamento multi-tenant é aplicado nas queries do backend. IDs enviados pelo cliente nunca concedem acesso. Criação de workspace, membership OWNER e assinatura Free ocorre em uma única transação.

## Instalação com Docker

```bash
cp .env.example .env
docker compose up --build
```

Acesse o frontend em `http://localhost:5173` e a API em `http://localhost:8000/api`. O backend executa migrations e sincroniza os planos ao iniciar.

Se essas portas já estiverem ocupadas, defina `BACKEND_PORT` e `FRONTEND_PORT` no `.env` (e ajuste `VITE_API_URL`/`FRONTEND_URL` para os mesmos endereços).

## Execução manual

Requer Python 3.12+, Node 22+ e PostgreSQL 16+.

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_plans
python manage.py runserver
```

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

## Variáveis de ambiente

Copie `.env.example`. São necessárias `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `FRONTEND_URL` e `VITE_API_URL`. As variáveis `PAYMENT_PROVIDER`, `PAYMENT_API_KEY`, `PAYMENT_WEBHOOK_SECRET` e `PAYMENT_CONTACT` estão reservadas e devem permanecer vazias nesta etapa.

## Endpoints

| Método | Endpoint | Acesso |
|---|---|---|
| POST | `/api/auth/register/` | Público |
| POST | `/api/auth/login/` | Público |
| POST | `/api/auth/refresh/` | Público (refresh válido) |
| POST | `/api/auth/logout/` | Autenticado |
| GET/PATCH | `/api/auth/me/` | Autenticado |
| GET/POST | `/api/organizations/` | Autenticado |
| GET/PATCH | `/api/organizations/:id/` | Membro / OWNER para edição |
| GET | `/api/organizations/:id/members/` | Membro |
| GET | `/api/plans/` | Público |
| GET | `/api/subscription/?organization_id=:id` | Membro da organização |
| GET/POST | `/api/clients/` | Membros leem; OWNER/ADMIN gerenciam |
| GET/PATCH/DELETE | `/api/clients/:id/` | Tenant atual e RBAC |
| GET/POST | `/api/projects/` | Projetos permitidos; OWNER/ADMIN criam |
| GET/PATCH/DELETE | `/api/projects/:id/` | Tenant atual e RBAC |
| GET/POST | `/api/projects/:id/members/` | Leitura permitida; OWNER/ADMIN adicionam |
| DELETE | `/api/projects/:id/members/:membership_id/` | OWNER/ADMIN |
| GET | `/api/projects/:id/activities/` | Usuários com acesso ao projeto |
| GET | `/api/dashboard/` | Dashboard agregado do workspace |

Não existe endpoint de alteração de plano. Portanto, um cliente não pode ativar Pro manualmente.

## Rotas da interface

`/login`, `/register`, `/onboarding/workspace`, `/onboarding/plan`, `/dashboard`, `/clients`, `/clients/:id`, `/projects`, `/projects/:id`, `/settings/profile` e `/settings/billing`. Tarefas, Kanban, arquivos e financeiro continuam preparados como próximas etapas.

## RBAC de clientes e projetos

| Ação | OWNER | ADMIN | MEMBER | CLIENT |
|---|---:|---:|---:|---:|
| Visualizar clientes | Sim | Sim | Sim | Não |
| Criar/editar/excluir clientes | Sim | Sim | Não | Não |
| Visualizar projetos | Todos | Todos | Somente como ProjectMember | Não nesta etapa |
| Criar/editar/excluir projetos | Sim | Sim | Não | Não |
| Gerenciar membros do projeto | Sim | Sim | Não | Não |

O frontend envia `X-Organization-ID`; o backend sempre valida a membership antes de aplicar o tenant. Alterar o header não concede acesso externo.

## Testes e build

```bash
docker compose run --rm backend python manage.py test
cd frontend && npm run build
```

Os testes cobrem autenticação, validações, refresh/logout, perfil, workspaces, planos, clientes, projetos, membros, filtros, validações, dashboard, RBAC e tentativas de IDOR entre tenants.

## Roadmap

- Prompt 1: concluído — fundação SaaS.
- Prompt 2: concluído — clientes, projetos e RBAC avançado.
- Prompt 3: concluído — tarefas, Kanban, comentários e anexos.
- Próximo: Prompt 4 — controle de horas e financeiro.

## Tarefas e Kanban

O Prompt 3 adiciona tarefas com estados `BACKLOG`, `TODO`, `IN_PROGRESS`, `REVIEW` e `DONE`, prioridades, posições persistentes, múltiplos responsáveis, labels, comentários e anexos privados. O progresso do projeto é calculado no backend pela proporção de tarefas concluídas.

Uploads aceitam PDF, PNG, JPG/JPEG, WEBP, TXT, DOCX e XLSX, com limite de 10 MB e validação de extensão/MIME. Downloads exigem JWT e acesso ao projeto; os arquivos não são expostos por uma rota pública de media.

| Método | Endpoint |
|---|---|
| GET/POST | `/api/tasks/` |
| GET/PATCH/DELETE | `/api/tasks/:id/` |
| PATCH | `/api/tasks/:id/move/` |
| GET | `/api/projects/:id/tasks/` |
| GET/POST | `/api/tasks/:id/comments/` |
| PATCH/DELETE | `/api/task-comments/:id/` |
| GET/POST | `/api/tasks/:id/attachments/` |
| GET | `/api/task-attachments/:id/download/` |
| DELETE | `/api/task-attachments/:id/` |
| GET/POST | `/api/task-labels/` |

## Pricing

- Free: R$ 0/mês.
- DevFlow Pro: R$ 25/mês.

O backend é a fonte de verdade dos preços. Pagamentos, cartões, PIX, gateways e webhooks ainda não foram implementados.

## Horas, financeiro e relatórios

O Prompt 4 adiciona timer com somente um registro ativo por pessoa/workspace, lançamentos manuais, custos e valores de cobrança, receitas, despesas, faturas de clientes, relatórios agrupados e exportação CSV. Faturas de clientes são independentes da assinatura SaaS do DevFlow.

Principais rotas: `/api/time-entries/`, `/api/expenses/`, `/api/revenues/`, `/api/invoices/`, `/api/finance/dashboard/`, `/api/reports/` e `/api/reports/hours/export/`.

## Portal, notificações e assinatura Pro

O Prompt 5 adiciona portal isolado para clientes, convites com token armazenado como hash, entregas com aprovação ou solicitação de alterações, notificações persistentes, preferências, email assíncrono, Redis, Celery worker/beat e WebSocket autenticado por JWT.

O plano Free permite 3 projetos ativos, 2 membros e 500 MB. O Pro custa R$ 25,00/mês, permite projetos ilimitados, 20 membros, 10 GB, portal do cliente e recursos avançados. Os limites ficam centralizados em `SubscriptionPolicy`; downgrade nunca exclui dados.

Billing usa Stripe Checkout em modo `subscription`. O backend usa exclusivamente o plano Pro de R$ 25 cadastrado e o `STRIPE_PRO_PRICE_ID`; o frontend não informa valor. A assinatura só muda mediante webhook Stripe assinado e idempotente. Eventos tratados: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated` e `customer.subscription.deleted`.

Para ativar checkout sandbox, configure `PAYMENT_PROVIDER=stripe`, `PAYMENT_API_KEY`, `PAYMENT_WEBHOOK_SECRET` e `STRIPE_PRO_PRICE_ID`. Para testar webhooks localmente, use o Stripe CLI oficial encaminhando para `/api/webhooks/payments/stripe/`. Sem essas credenciais, todo o restante funciona localmente e o checkout retorna erro de configuração sem ativar Pro.

Serviços locais:

```powershell
docker compose up --build
docker compose logs -f celery_worker
```

## Demonstração local

```powershell
docker compose up -d --build
docker compose exec backend python manage.py seed_demo
```

Credenciais exclusivamente locais: `demo@devflow.local` / `DevFlowDemo!2026`.

## Qualidade e operação

- Health: `/health/`
- Readiness (PostgreSQL + Redis): `/health/ready/`
- CI: backend lint/migrations/testes/coverage/audit, frontend lint/build/audit e Docker build.
- Produção: consulte `docs/DEPLOYMENT.md` e `.env.production.example`.
- Arquitetura: consulte `docs/ARCHITECTURE.md`.
- Segurança: consulte `SECURITY.md`.

O deploy público não é executado automaticamente: domínio, VPS, DNS, certificados, conta Stripe sandbox/produção e credenciais SMTP continuam sendo decisões externas do proprietário.

## Autor

**Orlando Conceição Vilhalba de Almeida**

Desenvolvedor Backend em formação, com foco em Python, Django, Django REST Framework, APIs REST, PostgreSQL, Docker e integração de aplicações web com React e TypeScript.

GitHub: [orlandoconceicao](https://github.com/orlandoconceicao)
