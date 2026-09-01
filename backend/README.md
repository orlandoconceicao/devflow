# DevFlow Backend

API REST do DevFlow, responsável por autenticação, isolamento multi-tenant, regras de negócio, persistência, integrações e tarefas de segundo plano.

- Produção: <https://devflow-backend-swart.vercel.app>
- Health: <https://devflow-backend-swart.vercel.app/health/>
- Repositório: <https://github.com/orlandoconceicao/devflow>

## Tecnologias

- Python 3.13 e Django 5.2;
- Django REST Framework e SimpleJWT;
- PostgreSQL, psycopg e `dj-database-url`;
- Channels, Daphne, Redis opcional e Celery;
- Pillow e Requests;
- Ruff, Coverage e `pip-audit`.

## Domínios e funcionalidades

| Aplicação | Responsabilidade |
|---|---|
| `accounts` | usuários, login por email, JWT, perfil e recuperação de senha |
| `organizations` | workspaces, memberships, RBAC, convites por email e chat de equipe |
| `subscriptions` | planos, limites, checkout, assinatura e webhooks Mercado Pago |
| `work` | clientes, projetos, tarefas, labels, comentários, anexos e dashboard |
| `finance` | horas, custos, receitas, despesas, faturas, Pix e relatórios |
| `portal` | portal do cliente, convites, entregas e notificações |
| `core` | health checks, middleware, erros, auditoria e comandos de apoio |

Os dados são filtrados pelo workspace indicado em `X-Organization-ID` e pela membership ativa do usuário. Os papéis internos são `OWNER`, `ADMIN` e `MEMBER`; o acesso do cliente é separado pelo portal.

## Estrutura

```text
backend/
├── apps/
│   ├── accounts/
│   ├── core/
│   ├── finance/
│   ├── organizations/
│   ├── payments/
│   ├── portal/
│   ├── subscriptions/
│   └── work/
├── config/              # settings, URLs, ASGI, WSGI e Celery
├── manage.py
├── requirements.txt
├── Dockerfile
└── Dockerfile.dev
```

## Instalação e execução local

Pré-requisitos: Python 3.13 e PostgreSQL 16. Redis 7 é recomendado para reproduzir a execução completa do Compose, mas não é obrigatório.

Na raiz do repositório:

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
python backend/manage.py migrate
python backend/manage.py seed_plans
python backend/manage.py runserver
```

No Windows, use `Copy-Item .env.example .env`. A API estará em <http://localhost:8000/api>.

Para executar toda a infraestrutura com containers:

```bash
docker compose up --build
```

O Compose sobe PostgreSQL, Redis, backend, worker Celery, beat Celery e frontend.

## Variáveis de ambiente

### Aplicação e segurança

```env
DJANGO_SETTINGS_MODULE=config.settings
DEBUG=True
SECRET_KEY=uma-chave-local
ALLOWED_HOSTS=localhost,127.0.0.1
FRONTEND_URL=http://localhost:5173
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
```

Em produção use `config.settings_production`, `DEBUG=False`, uma `SECRET_KEY` forte e os hosts/origens HTTPS exatos.

### Banco de dados

Defina `DATABASE_URL` ou os campos individuais:

```env
DB_NAME=devflow
DB_USER=devflow
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
```

### Redis e Celery

```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
CELERY_TASK_ALWAYS_EAGER=False
```

Quando `REDIS_URL` está vazio, o sistema usa cache e Channels em memória; por padrão, as tarefas executam em modo eager. Em infraestrutura persistente com Redis, execute também `celery -A config worker -l info` e `celery -A config beat -l info` dentro de `backend`.

### Email

Desenvolvimento sem entrega real:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

SMTP do Gmail:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=senha-de-app-do-google
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=DevFlow <seu-email@gmail.com>
```

Use uma senha de app do Google em `EMAIL_HOST_PASSWORD`; não use a senha normal da conta e nunca versione esse valor.

O convite de equipe usa `EmailMultiAlternatives`: envia uma versão HTML com botão de aceite e uma versão em texto simples para compatibilidade. O nome da equipe e o link são escapados no HTML. Cada convite é pessoal, de uso único e expira em 7 dias.

### Mercado Pago e mensagens

```env
MERCADO_PAGO_ENVIRONMENT=test
MERCADO_PAGO_ACCESS_TOKEN=
MERCADO_PAGO_WEBHOOK_SECRET=
MERCADO_PAGO_BASE_URL=https://api.mercadopago.com
PAYMENT_CONTACT=
MESSAGE_PROVIDER=
WHATSAPP_API_URL=
WHATSAPP_ACCESS_TOKEN=
```

O Access Token e o segredo do webhook pertencem exclusivamente ao backend.

## Endpoints principais

- `/api/auth/`: cadastro, login, refresh, logout, perfil e recuperação de senha;
- `/api/organizations/`: organizações, membros, convites e chat;
- `/api/clients/`, `/api/projects/`, `/api/tasks/`: operação do workspace;
- `/api/time-entries/`, `/api/expenses/`, `/api/revenues/`, `/api/invoices/`: financeiro;
- `/api/reports/` e `/api/reports/hours/export/`: relatórios;
- `/api/client-portal/`, `/api/deliverables/`, `/api/notifications/`: portal e notificações;
- `/api/plans/`, `/api/subscription/`, `/api/billing/`: planos e assinatura;
- `/api/public/payments/:token/`: consulta pública de cobrança;
- `/api/webhooks/mercado-pago/`: confirmação de pagamentos e assinaturas;
- `/health/` e `/health/ready/`: saúde e dependências.

## Testes e qualidade

Na raiz do repositório:

```bash
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test apps
ruff check backend
coverage run backend/manage.py test apps
coverage report
pip-audit -r backend/requirements.txt
```

## Deploy na Vercel

O backend atual está em <https://devflow-backend-swart.vercel.app>. Configure o projeto com `backend` como Root Directory e todas as variáveis no ambiente **Production**.

Valores essenciais para o ambiente atual:

```env
DJANGO_SETTINGS_MODULE=config.settings_production
DEBUG=False
ALLOWED_HOSTS=devflow-backend-swart.vercel.app
FRONTEND_URL=https://devflow-frontend-delta.vercel.app
CORS_ALLOWED_ORIGINS=https://devflow-frontend-delta.vercel.app
CSRF_TRUSTED_ORIGINS=https://devflow-frontend-delta.vercel.app,https://devflow-backend-swart.vercel.app
REDIS_URL=
CELERY_TASK_ALWAYS_EAGER=True
```

Também são obrigatórios uma `SECRET_KEY` forte, conexão PostgreSQL e as credenciais das integrações utilizadas. Para convites e recuperação de senha, configure todas as variáveis SMTP, principalmente `EMAIL_HOST_PASSWORD` com a senha de app do Google.

A Vercel não executa o worker/beat persistente definido no Docker Compose. Por isso, o ambiente atual deixa `REDIS_URL` vazio e usa `CELERY_TASK_ALWAYS_EAGER=True`. Após alterar qualquer variável, faça um redeploy do backend.

Configure o webhook do Mercado Pago em:

```text
https://devflow-backend-swart.vercel.app/api/webhooks/mercado-pago/
```

## Segurança

- JWT curto, refresh rotativo e blacklist no logout;
- tokens de convite armazenados apenas como SHA-256;
- validação de tenant e RBAC no backend;
- anexos privados com validação de tipo e tamanho;
- valores monetários com `Decimal`;
- webhooks assinados e processamento idempotente;
- headers HTTPS e cookies seguros em produção.
