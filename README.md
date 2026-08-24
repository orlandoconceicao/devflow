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

Copie `.env.example`. São necessárias `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `FRONTEND_URL` e `VITE_API_URL`. As variáveis de pagamento só devem ser preenchidas no backend e podem permanecer vazias quando checkout e cobranças Pix não forem usados.

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

## Autenticação, workspace e equipe

Todo mundo usa o mesmo `/login`, mas ninguém compartilha credenciais. `User` é a identidade global da pessoa — email, senha individual com hash e sessão JWT. `Organization` é o workspace da empresa. `OrganizationMembership` liga uma pessoa a um workspace e guarda a função atual (`OWNER`, `ADMIN`, `MEMBER`; `CLIENT` permanece separado para o portal). A autorização consulta a membership ativa no banco em cada requisição, portanto uma mudança de função ou remoção passa a valer mesmo para um JWT emitido anteriormente.

Quem cria o workspace recebe automaticamente a membership `OWNER`. Somente esse Owner abre `/team`, lista a equipe, convida, muda entre ADMIN/MEMBER e remove acesso. O Owner não pode remover a si mesmo nem ser rebaixado. Admin atua nas operações já permitidas, mas não gerencia propriedade ou equipe. Member visualiza somente projetos dos quais é `ProjectMember`; pertencer à empresa não concede automaticamente acesso a todos os projetos, financeiro ou configurações administrativas.

O convite começa em **Equipe > Convidar membro**. O backend aceita somente ADMIN ou MEMBER, normaliza o email, cria um token aleatório e armazena apenas seu SHA-256. `/team-invitations/accept?token=...` expira em sete dias e é de uso único. Uma pessoa nova cria a própria senha; se o email já possuir `User`, precisa comprovar a senha da conta e recebe apenas outra membership, sem duplicação. O Owner nunca vê nem envia a senha. Depois, todos entram normalmente por `/login`.

Remover alguém desativa a membership e retira suas participações em projetos daquele workspace, sem apagar o `User`. `current_membership` exige `is_active=True`, e os querysets filtram a organização indicada por `X-Organization-ID`. Assim, mudar o header, usar ID de outro workspace ou conservar um JWT não contorna a revogação. Menus filtrados no React são UX; a segurança real permanece nas permissions e querysets do backend.

Para construir o fluxo do zero: modele User, Organization e Membership; atribua OWNER ao criador em transação; implemente convite com token armazenado como hash, expiração e uso único; aceite criando ou associando o User; valide membership ativa em cada request; limite projetos com ProjectMember; bloqueie mass assignment de role; reflita isso nos menus e teste replay, remoção e IDOR.

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

A suíte de equipe cobre Owner, membership ativa/inativa, login individual, convite para usuário novo e existente, expiração/reutilização, alteração de função, remoção, revogação com JWT ainda válido e isolamento entre workspaces. O frontend verifica que apenas Owner visualiza a gestão.

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

O backend é a fonte de verdade dos preços. A assinatura SaaS usa Stripe Checkout e as faturas de clientes podem usar Pix dinâmico; o DevFlow não armazena dados de cartão.

## Horas, financeiro e relatórios

O Prompt 4 adiciona timer com somente um registro ativo por pessoa/workspace, lançamentos manuais, custos e valores de cobrança, receitas, despesas, faturas de clientes, relatórios agrupados e exportação CSV. Faturas de clientes são independentes da assinatura SaaS do DevFlow.

Principais rotas: `/api/time-entries/`, `/api/expenses/`, `/api/revenues/`, `/api/invoices/`, `/api/finance/dashboard/`, `/api/reports/` e `/api/reports/hours/export/`.

### Cobranças Pix públicas

O pagamento de uma fatura não depende do Portal do Cliente. Apenas OWNER ou ADMIN entra no painel, cria a cobrança em **Financeiro > Cobranças** e gera o Pix. O pagador recebe `/pagar/<uuid>` e abre diretamente, sem User, cadastro, senha ou JWT. `Client` permanece apenas como cadastro comercial interno.

A implementação reutiliza `Invoice`, itens em `Decimal`, `Client`, `Project` opcional e `Revenue`. `InvoicePayment` representa uma tentativa técnica do provedor. Uma tentativa pendente é reutilizada; regenerar explicitamente um Pix expirado cria outra tentativa na mesma `Invoice`, nunca outra fatura. A geração futura usa `payment_release_on`, `auto_generate_payment` e a tarefa Celery Beat `generate_scheduled_invoice_payments`; **Gerar agora** continua disponível.

O UUID público é imprevisível e não enumera IDs. `GET /api/public/payments/<uuid>/` não exige autenticação e retorna apenas descrição, valor, vencimento, status, QR, Pix Copia e Cola e expiração. Não permite editar valor/cliente/status nem expõe custos, workspace, IDs internos ou credenciais.

O Stripe cria um `PaymentIntent` Pix dinâmico no backend. QR e Copia e Cola vêm do provedor e identificam aquela cobrança; não são uma chave fixa. A página faz polling somente para leitura e oculta o Pix quando pago ou expirado. A confirmação confiável ocorre exclusivamente em `POST /api/webhooks/payments/stripe/invoices/`, com assinatura Stripe sobre o corpo bruto. O backend confere PaymentIntent, BRL e valor em centavos, marca a fatura e cria uma única receita. O ID único do evento e o vínculo único `Revenue.invoice` tornam reentregas idempotentes.

O painel permite copiar/abrir o link e gerar novo Pix após expiração. Nenhuma API paga de WhatsApp foi adicionada; o link pode ser enviado manualmente por email ou WhatsApp.

## Portal, notificações e assinatura Pro

O Prompt 5 adiciona portal isolado para clientes, convites com token armazenado como hash, entregas com aprovação ou solicitação de alterações, notificações persistentes, preferências, email assíncrono, Redis, Celery worker/beat e WebSocket autenticado por JWT.

O plano Free permite 3 projetos ativos, 2 membros e 500 MB. O Pro custa R$ 25,00/mês, permite projetos ilimitados, 20 membros, 10 GB, portal do cliente e recursos avançados. Os limites ficam centralizados em `SubscriptionPolicy`; downgrade nunca exclui dados.

Billing usa Stripe Checkout em modo `subscription`. O backend usa exclusivamente o plano Pro de R$ 25 cadastrado e o `STRIPE_PRO_PRICE_ID`; o frontend não informa valor. A assinatura só muda mediante webhook Stripe assinado e idempotente. Eventos tratados: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated` e `customer.subscription.deleted`.

Para ativar checkout sandbox, configure `PAYMENT_PROVIDER=stripe`, `PAYMENT_API_KEY`, `PAYMENT_WEBHOOK_SECRET` e `STRIPE_PRO_PRICE_ID`. Para cobranças Pix, configure `PIX_WEBHOOK_SECRET` com o segredo exclusivo do endpoint de faturas e `PIX_EXPIRATION_SECONDS` (10 a 1.209.600 segundos). Credenciais ficam somente no backend e `.env.example` contém placeholders. Use Stripe CLI/chaves de teste: assinatura SaaS aponta para `/api/webhooks/payments/stripe/`; Pix de clientes, para `/api/webhooks/payments/stripe/invoices/`. Os testes usam mocks e nunca cobram dinheiro real.

Serviços locais:

```powershell
docker compose up --build
docker compose logs -f celery_worker
```

Para validar o fluxo do zero: configure chaves Stripe de teste, suba banco, Redis, backend, worker, beat e frontend; crie cliente/projeto e uma cobrança; copie o link e abra em janela anônima. Ele deve abrir sem login e manter valor, QR e código somente para leitura. Envie um evento sandbox assinado e confirme a mudança para pago. Execute `docker compose run --rm backend python manage.py check`, `docker compose run --rm backend python manage.py test`, `cd frontend`, `npm test`, `npm run lint` e `npm run build`.

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

Desenvolvedor Backend em formação, com foco em Python, Django, Django REST Framework, PostgreSQL, APIs REST e Docker, utilizando React como tecnologia complementar para integração das aplicações.

GitHub: https://github.com/orlandoconceicao

LinkedIn: https://www.linkedin.com/in/orlando-concei%C3%A7%C3%A3o-582234315

Portfólio: https://orlandoconceicao.github.io/
