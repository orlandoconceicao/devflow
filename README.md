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

Requer Python 3.12+, Node 22+ e PostgreSQL 16+. Redis 7+ é opcional: quando
`REDIS_URL` fica vazio, o backend usa LocMemCache, InMemoryChannelLayer, broker
Celery em memória e execução eager. O Compose pode
executar apenas as dependências de infraestrutura, enquanto backend e frontend
rodam diretamente no Windows:

```powershell
Copy-Item .env.example .env  # somente se o arquivo ainda não existir
docker compose up -d db redis
docker compose exec redis redis-cli ping  # deve responder PONG

.\.venv\Scripts\Activate.ps1
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_plans
python manage.py runserver
```

Nesse modo, use `DB_HOST=localhost` e
`REDIS_URL=redis://localhost:6379/0` no `.env`. Quando o backend roda pelo
Compose, o arquivo `docker-compose.yml` troca esses hosts internamente para
`db` e `redis`; não use `redis://redis:6379/0` no processo executado diretamente
no Windows. Antes de iniciar o backend, `docker compose ps redis` deve mostrar o
serviço como `healthy`.

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

## Variáveis de ambiente

Copie `.env.example`. São necessárias `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`,
configuração do PostgreSQL ou `DATABASE_URL`, `FRONTEND_URL` e `VITE_API_URL`.
`REDIS_URL` é opcional. Quando configurado, Redis atende cache, Channels e
Celery; quando vazio, os fallbacks locais mantêm as páginas e tarefas síncronas
funcionando. As variáveis de pagamento só devem ser preenchidas no backend e
podem permanecer vazias quando checkout e cobranças Pix não forem usados.

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

As rotas principais são `/login`, `/register`, `/password-reset`, `/onboarding`,
`/dashboard`, `/clients`, `/projects`, `/tasks`, `/time`, `/finance`, `/reports`,
`/team`, `/team/chat`, `/notifications`, `/client-portal`, `/pricing`, `/settings`
e suas páginas filhas. O fallback SPA de produção entrega `index.html` para
essas URLs e deixa o React Router resolver a página. URLs históricas `/client`
e `/client/projects/:id` redirecionam para o portal atual.

Requisições dependentes do workspace enviam `X-Organization-ID`. O backend
valida o ID contra a membership ativa do usuário; autenticação, planos e a
descoberta inicial de organizações não dependem desse header.

## Autenticação, workspace e equipe

Todo mundo usa o mesmo `/login`, mas ninguém compartilha credenciais. `User` é a identidade global da pessoa — email, senha individual com hash e sessão JWT. `Organization` é o workspace da empresa. `OrganizationMembership` liga uma pessoa a um workspace e guarda a função atual (`OWNER`, `ADMIN`, `MEMBER`; `CLIENT` permanece separado para o portal). A autorização consulta a membership ativa no banco em cada requisição, portanto uma mudança de função ou remoção passa a valer mesmo para um JWT emitido anteriormente.

Quem cria o workspace recebe automaticamente a membership `OWNER`. Somente esse Owner abre `/team`, lista a equipe, muda entre ADMIN/MEMBER e remove acesso. O Owner não pode remover a si mesmo nem ser rebaixado. Admin atua nas operações já permitidas, mas não gerencia propriedade ou equipe. Member visualiza somente projetos dos quais é `ProjectMember`; pertencer à empresa não concede automaticamente acesso a todos os projetos, financeiro ou configurações administrativas.

O backend de convites permanece disponível, embora a página Equipe não exponha uma ação para criar novos convites. Ele aceita somente ADMIN ou MEMBER, normaliza o email, cria um token aleatório e armazena apenas seu SHA-256. `/team-invitations/accept?token=...` expira em sete dias e é de uso único. Uma pessoa nova cria a própria senha; se o email já possuir `User`, precisa comprovar a senha da conta e recebe apenas outra membership, sem duplicação. O Owner nunca vê nem envia a senha. Depois, todos entram normalmente por `/login`.

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

O backend é a fonte de verdade dos preços. A assinatura SaaS e as faturas de clientes usam Mercado Pago; o DevFlow não armazena dados de cartão nem credenciais do pagador.

## Horas, financeiro e relatórios

O Prompt 4 adiciona timer com somente um registro ativo por pessoa/workspace, lançamentos manuais, custos e valores de cobrança, receitas, despesas, faturas de clientes, relatórios agrupados e exportação CSV. Faturas de clientes são independentes da assinatura SaaS do DevFlow.

Principais rotas: `/api/time-entries/`, `/api/expenses/`, `/api/revenues/`, `/api/invoices/`, `/api/finance/dashboard/`, `/api/reports/` e `/api/reports/hours/export/`.

### Cobranças Pix públicas

O pagamento de uma fatura não depende do Portal do Cliente. Apenas OWNER ou ADMIN entra no painel, cria a cobrança em **Financeiro > Cobranças** e gera o Pix. O pagador recebe `/pagar/<uuid>` e abre diretamente, sem User, cadastro, senha ou JWT. `Client` permanece apenas como cadastro comercial interno.

A implementação reutiliza `Invoice`, itens em `Decimal`, `Client`, `Project` opcional e `Revenue`. `InvoicePayment` representa uma tentativa técnica do provedor. Uma tentativa pendente é reutilizada; regenerar explicitamente um Pix expirado cria outra tentativa na mesma `Invoice`, nunca outra fatura. A geração futura usa `payment_release_on`, `auto_generate_payment` e a tarefa Celery Beat `generate_scheduled_invoice_payments`; **Gerar agora** continua disponível.

O UUID público é imprevisível e não enumera IDs. `GET /api/public/payments/<uuid>/` não exige autenticação e retorna apenas descrição, valor, vencimento, status, QR, Pix Copia e Cola e expiração. Não permite editar valor/cliente/status nem expõe custos, workspace, IDs internos ou credenciais.

O Mercado Pago cria o pagamento Pix dinâmico no backend. QR e Copia e Cola vêm da API e identificam aquela cobrança; não são uma chave fixa. A página faz polling somente para leitura e oculta o Pix quando pago ou expirado. A confirmação confiável ocorre exclusivamente em `POST /api/webhooks/mercado-pago/`, com validação HMAC de `x-signature` e consulta autenticada do pagamento. O backend confere referência externa, BRL e valor, marca a fatura e cria uma única receita. A chave determinística do evento e o vínculo único `Revenue.invoice` tornam reentregas idempotentes.

O painel permite copiar/abrir o link e gerar novo Pix após expiração. Nenhuma API paga de WhatsApp foi adicionada; o link pode ser enviado manualmente por email ou WhatsApp.

## Portal, notificações e assinatura Pro

O Prompt 5 adiciona portal isolado para clientes, convites com token armazenado como hash, entregas com aprovação ou solicitação de alterações, notificações persistentes, preferências, email assíncrono, Redis, Celery worker/beat e WebSocket autenticado por JWT.

## Fluxos guiados, conta e equipe

O frontend trata os pré-requisitos reais sem transformar relações opcionais em
obrigatórias: projeto exige cliente; tarefa e lançamento de horas exigem projeto;
cobrança exige cliente, mas projeto é opcional. Estados vazios oferecem a próxima
ação permitida. Ao cadastrar um cliente durante a criação de projeto, `returnTo`
leva de volta ao formulário e seleciona o cliente criado. Os Primeiros Passos do
dashboard consultam dados reais de perfil, clientes e projetos.

Configurações reúne Perfil, Preferências, Notificações, Equipe, Cobranças e Ajuda.
O perfil aceita biografia e avatar JPG/PNG/WEBP de até 2 MB. Idioma (`pt-BR` ou
`en`), timezone IANA e tema (`system`, `light`, `dark`) são persistidos na conta.
A estrutura de traduções fica centralizada em `frontend/src/i18n`; português
continua sendo o padrão.

O papel OWNER existente é apresentado como **Primário**, responsável principal
do workspace. ADMIN e MEMBER são **Secundários**; não existe autopromoção pela UI
ou API. Quando um Secundário muda o email, a mesma conta e seus relacionamentos
são preservados, mas as memberships secundárias ficam aguardando aprovação. O
Primário recebe uma notificação e reativa o acesso pela página Equipe. O chat da
equipe é cronológico, aceita somente memberships ativas e sempre filtra pelo
workspace indicado.

A página Ajuda contém FAQ alinhada aos fluxos implementados e contato por
`orlandoconceicao94@gmail.com`. Feedbacks de perfil, preferências e cópia usam o
toast compartilhado; nenhum fluxo novo usa `alert()`.

## Entrega de cobranças

Ao escolher **Gerar cobrança Pix agora**, o backend reutiliza a integração Mercado Pago,
gera um pagamento real e abre imediatamente a página pública com cliente, valor,
descrição, vencimento, status, QR Code e Pix Copia e Cola. Nenhum QR ou código é
fabricado localmente. Depois da geração, uma tarefa Celery envia os dados e o link
ao email cadastrado do cliente.

Para Gmail, use `EMAIL_HOST=smtp.gmail.com`, porta 587, TLS,
`EMAIL_HOST_USER=orlandoconceicao94@gmail.com` e uma App Password em
`EMAIL_HOST_PASSWORD`. A App Password nunca deve ser versionada. O backend de
console permanece apropriado para desenvolvimento e não representa entrega real.

Telefone não é simulado. A arquitetura suporta a WhatsApp Cloud API da Meta com
`MESSAGE_PROVIDER=meta_whatsapp`, `WHATSAPP_API_URL` (endpoint `/messages` do
número configurado) e `WHATSAPP_ACCESS_TOKEN`. Sem essas variáveis, o sistema
registra que o canal foi ignorado e não informa ao usuário que houve envio.

O plano Free permite 3 projetos ativos, 2 membros e 500 MB. O Pro custa R$ 25,00/mês, permite projetos ilimitados, 20 membros, 10 GB, portal do cliente e recursos avançados. Os limites ficam centralizados em `SubscriptionPolicy`; downgrade nunca exclui dados.

Billing usa a API de assinaturas recorrentes do Mercado Pago. O backend define exclusivamente o plano Pro de R$ 25; o frontend não informa valor. A assinatura só muda mediante webhook assinado e idempotente, após consulta autenticada de preapproval ou pagamento autorizado.

Para ativar o ambiente de teste, configure `MERCADO_PAGO_ENVIRONMENT=test`, `MERCADO_PAGO_ACCESS_TOKEN`, `MERCADO_PAGO_WEBHOOK_SECRET` e `MERCADO_PAGO_BASE_URL`. `MERCADO_PAGO_PUBLIC_KEY` só é necessária para recursos client-side futuros; o Access Token permanece exclusivamente no backend. Configure no painel do Mercado Pago o endpoint HTTPS `/api/webhooks/mercado-pago/` para pagamentos e assinaturas. Os testes usam mocks e nunca movimentam dinheiro real.

Serviços locais:

```powershell
docker compose up --build
docker compose logs -f celery_worker
```

Para validar o fluxo do zero: configure credenciais Mercado Pago de teste, suba banco, Redis, backend, worker, beat e frontend; crie cliente/projeto e uma cobrança; copie o link e abra em janela anônima. Ele deve abrir sem login e manter valor, QR e código somente para leitura. Envie um evento sandbox assinado e confirme a mudança para pago. Execute `docker compose run --rm backend python manage.py check`, `docker compose run --rm backend python manage.py test`, `cd frontend`, `npm test`, `npm run lint` e `npm run build`.

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

O deploy público não é executado automaticamente: domínio, VPS, DNS, certificados, conta Mercado Pago de teste/produção e credenciais SMTP continuam sendo decisões externas do proprietário.

## Autor

**Orlando Conceição Vilhalba de Almeida**

Desenvolvedor Backend em formação, com foco em Python, Django, Django REST Framework, PostgreSQL, APIs REST e Docker, utilizando React como tecnologia complementar para integração das aplicações.

GitHub: https://github.com/orlandoconceicao

LinkedIn: https://www.linkedin.com/in/orlando-concei%C3%A7%C3%A3o-582234315

Portfólio: https://orlandoconceicao.github.io/
