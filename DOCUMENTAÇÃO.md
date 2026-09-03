# DOCUMENTAÇÃO

## Como usar este material

Este guia é uma apostila para estudar o DevFlow do navegador até o banco de dados. A melhor ordem é ler primeiro a visão geral, abrir os arquivos indicados e, depois, acompanhar os fluxos completos. Os trechos são pequenos de propósito: o objetivo é aprender a navegar no projeto real, não duplicar o código-fonte.

Quando aparecer “frontend”, pense no programa executado pelo navegador. Quando aparecer “backend”, pense no servidor que valida regras, acessa o banco e responde à interface. As perguntas de revisão ficam ao fim das seções e o gabarito está separado no final.

## Índice navegável

- [Visão geral e arquitetura](#visão-geral-do-projeto)
- [Entrada HTML e montagem React](#html-a-porta-de-entrada-do-navegador)
- [Rotas frontend](#rotas-e-composição-em-apptsx)
- [Autenticação e estado global](#autenticação-e-estado-global)
- [HTTP, services e TanStack Query](#cliente-http-api-e-tanstack-query)
- [Layout, componentes e páginas](#layout-e-componentes-importantes)
- [Tema, CSS e responsividade](#tema-idioma-e-css-real)
- [TypeScript aplicado](#typescript-e-javascript-aplicados)
- [Backend Django](#backend-django-da-url-ao-banco)
- [Referência dos apps Django](#referência-dos-apps-django)
- [API e endpoints](#referência-completa-da-api)
- [Banco, models e migrations](#banco-de-dados-e-models)
- [Multi-tenancy, RBAC e segurança](#multi-tenancy-rbac-e-segurança)
- [Fluxos completos](#fluxos-completos-do-sistema)
- [WebSocket, Redis e Celery](#websocket-redis-e-celery)
- [Docker e infraestrutura](#docker-e-infraestrutura)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Vite e dependências](#vite-scripts-e-dependências)
- [Desenvolvimento, produção e deploy](#build-desenvolvimento-e-produção)
- [Git e `.gitignore`](#git-e-gitignore)
- [Testes, coverage e CI](#testes-e-qualidade)
- [Referência de comandos](#referência-de-comandos)
- [Debug e troubleshooting](#troubleshooting-didático)
- [Exercícios e mapa mental](#exercícios-seguros)
- [Construção do zero](#como-construir-este-projeto-do-zero)
- [Desafio de reconstrução](#desafio-reconstruir-o-projeto)
- [Ordem de estudo](#ordem-recomendada-para-estudar-este-projeto)
- [Glossário](#glossário)
- [Gabaritos](#gabarito-da-trilha-de-construção)

## Visão geral do projeto

O DevFlow é um SaaS multi-tenant para freelancers, agências e equipes pequenas organizarem workspaces, clientes, projetos, tarefas, horas, financeiro, cobranças, equipe e entregas para clientes. “Multi-tenant” significa que a mesma aplicação atende várias organizações, mas os dados de cada uma permanecem isolados.

A stack confirmada pelos arquivos atuais é:

| Camada                 | Tecnologia                       | Responsabilidade                                        |
| ---------------------- | -------------------------------- | ------------------------------------------------------- |
| Interface              | React 19 e TypeScript            | Componentes, páginas, formulários e estado visual       |
| Build frontend         | Vite 7                           | Servidor de desenvolvimento, proxy e bundle de produção |
| Navegação              | React Router 7                   | Decide qual página renderizar para cada URL             |
| Estado remoto          | TanStack Query                   | Cache, carregamento e invalidação de dados da API       |
| Formulários            | React Hook Form e Zod            | Coleta e validação de dados no navegador                |
| HTTP                   | Axios                            | Comunicação JSON com a API e renovação do JWT           |
| API                    | Django 5 e Django REST Framework | Regras de negócio, permissões e serialização            |
| Banco                  | PostgreSQL 16                    | Fonte de verdade dos dados persistentes                 |
| Assíncrono             | Celery                           | Emails, lembretes e geração programada de cobranças     |
| Cache/filas/tempo real | Redis 7, opcional localmente     | Broker Celery, cache e channel layer                    |
| WebSocket              | Django Channels e Daphne         | Notificações em tempo real autenticadas                 |
| Infraestrutura         | Docker Compose e Nginx           | Containers, rede, TLS, proxy e arquivos estáticos       |
| Pagamentos             | Mercado Pago                     | Pix de faturas e assinatura recorrente do DevFlow       |

### Mapa de execução

```text
Navegador
   ↓ GET /
frontend/index.html
   ↓ carrega /src/main.tsx
React monta providers e App.tsx
   ↓ React Router escolhe a rota
Página → componente → hook → service
   ↓ Axios envia HTTP/JSON + JWT + X-Organization-ID
Django config/urls.py
   ↓ URL do app → view → serializer → model
PostgreSQL
   ↓ resposta JSON
TanStack Query atualiza cache → React renderiza novamente
```

### Onde o projeto começa

- Frontend: `frontend/index.html` → `frontend/src/main.tsx` → `frontend/src/App.tsx`.
- Backend: `backend/manage.py` carrega `backend/config/settings.py`; HTTP entra por `backend/config/asgi.py` em produção ou pelo servidor de desenvolvimento.
- Rotas da API: `backend/config/urls.py` inclui os `urls.py` de cada domínio.
- Processos assíncronos: `backend/config/celery.py` descobre os arquivos `tasks.py`.

### Árvore simplificada

```text
devflow/
├── .github/
│   ├── workflows/ci.yml       validação automática de cada push/PR
│   └── dependabot.yml         acompanhamento de dependências
├── frontend/
│   ├── index.html
│   ├── src/
│   │   ├── components/       componentes reutilizáveis
│   │   ├── features/         hooks por domínio e autenticação
│   │   ├── i18n/             idioma e aplicação do tema
│   │   ├── layouts/          estrutura autenticada
│   │   ├── pages/            telas ligadas às rotas
│   │   ├── services/         chamadas HTTP
│   │   ├── types/            contratos TypeScript
│   │   ├── App.tsx           router da SPA
│   │   ├── main.tsx          montagem do React
│   │   └── styles.css        estilos e temas globais
│   ├── package.json
│   ├── vite.config.ts
│   └── vercel.json
├── backend/
│   ├── apps/
│   │   ├── accounts/         usuário e autenticação
│   │   ├── organizations/    workspaces, equipe e RBAC
│   │   ├── subscriptions/    planos e assinatura SaaS
│   │   ├── work/             clientes, projetos e tarefas
│   │   ├── finance/          horas, faturas e pagamentos
│   │   ├── portal/           portal, entregas e notificações
│   │   └── core/             saúde, middleware e erros
│   ├── config/               settings, URLs, ASGI, WSGI e Celery
│   └── manage.py
├── tests/                     testes transversais e smoke
│   ├── backend/               contratos da arquitetura Django
│   ├── frontend/              rotas e configuração da SPA
│   ├── integration/           correspondência frontend/backend
│   ├── security/              isolamento, CORS e segredos
│   ├── smoke/                 verificações remotas somente leitura
│   └── run_all.py             orquestrador local
├── deploy/                    configuração Nginx
├── docs/                      arquitetura e deploy de referência
├── docker-compose.yml         ambiente local
└── docker-compose.prod.yml    ambiente de produção em VPS
```

Pastas geradas como `node_modules`, `dist`, `.venv` e `__pycache__` não fazem parte do mapa conceitual e são ignoradas pelo Git.

### Perguntas para revisar

1. Qual camada é a fonte de verdade das regras de autorização?
2. Qual é a sequência entre uma página React e um model Django?
3. O que “multi-tenant” significa neste projeto?

## HTML: a porta de entrada do navegador

**Arquivo:** `frontend/index.html`

O arquivo atual é mínimo:

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

`<div id="root">` é um recipiente vazio. O React procura esse ID e monta toda a interface dentro dele. `type="module"` permite usar `import` e `export`; no desenvolvimento, o Vite transforma `main.tsx` e seus imports.

O arquivo não contém explicitamente `<!DOCTYPE html>`, `<html>`, `<head>`, meta viewport, favicon, descrição ou Open Graph. Portanto, não foi possível confirmar SEO social, favicon ou metadados avançados pelos arquivos atuais. O Vite aceita esse HTML mínimo, mas esses elementos seriam os locais usuais para título, viewport e metadados.

```text
index.html
   ↓ fornece #root
main.tsx
   ↓ document.getElementById('root')
createRoot(...).render(...)
   ↓
interface React
```

## `main.tsx`: montagem e providers

**Arquivo:** `frontend/src/main.tsx`

`createRoot(document.getElementById('root')!).render(...)` encontra o elemento HTML e inicia a árvore React. O `!` informa ao TypeScript que o programador sabe que o elemento não será `null`.

Os providers envolvem `App` nesta ordem:

```text
StrictMode
└── ErrorBoundary
    └── QueryClientProvider
        └── BrowserRouter
            └── AuthProvider
                └── I18nProvider
                    └── ToastProvider
                        └── App
```

- `StrictMode`: ajuda a detectar efeitos problemáticos no desenvolvimento.
- `ErrorBoundary`: captura erros inesperados de renderização e oferece uma tela de recuperação.
- `QueryClientProvider`: disponibiliza o cache do TanStack Query.
- `BrowserRouter`: sincroniza a interface com a URL do navegador.
- `AuthProvider`: compartilha usuário, login, logout e carregamento da sessão.
- `I18nProvider`: escolhe idioma, timezone e tema a partir do usuário.
- `ToastProvider`: fornece mensagens temporárias sem `alert()`.

Um **Context** é uma forma de compartilhar dados sem repassar props manualmente por toda a árvore. O **Provider** fornece o valor; `useContext` ou um hook como `useAuth` o consome.

### Módulos, imports e exports

`import App from './App'` usa um _default export_. Já `import { AuthProvider } ...` usa um _named export_. O primeiro permite escolher o nome local; o segundo precisa usar o nome exportado. Cada arquivo TypeScript é um módulo.

## Rotas e composição em `App.tsx`

**Arquivo:** `frontend/src/App.tsx`

`App` não desenha cada página diretamente. Ele declara a árvore de rotas. `RootRedirect` envia uma sessão autenticada para `/dashboard` e uma sessão anônima para `/login`. `Protected` espera a restauração da sessão e renderiza `AppLayout` ou redireciona. `ProtectedPage` preserva a URL solicitada em `?next=...` para retornar depois do login.

### Tabela de rotas frontend

| URL                                   | Componente                      | Proteção/finalidade                          |
| ------------------------------------- | ------------------------------- | -------------------------------------------- |
| `/`                                   | `RootRedirect`                  | Decide login ou dashboard                    |
| `/login`                              | `LoginPage`                     | Pública                                      |
| `/register`                           | `RegisterPage`                  | Pública                                      |
| `/password-reset`                     | `PasswordResetPage`             | Solicitação pública                          |
| `/password-reset/confirm`             | `PasswordResetConfirmPage`      | Confirmação pública                          |
| `/pagar/:token`                       | `PublicPaymentPage`             | Pix público por UUID                         |
| `/team-invitations/accept`            | `TeamInvitationPage`            | Aceite de equipe                             |
| `/client-invitations/accept`          | `AcceptClientInvitation`        | Exige login                                  |
| `/onboarding/workspace`               | `WorkspacePage`                 | Criação do workspace                         |
| `/onboarding/plan`                    | `PlanPage`                      | Escolha inicial do plano                     |
| `/dashboard`                          | `Dashboard`                     | Resumo do workspace                          |
| `/clients`, `/clients/:id`            | `ClientsPage`, `ClientDetail`   | Clientes                                     |
| `/projects`, `/projects/:id`          | `ProjectsPage`, `ProjectDetail` | Projetos e Kanban                            |
| `/tasks`                              | `TasksPage`                     | Lista global permitida                       |
| `/time`                               | `TimeTracking`                  | Timer e horas                                |
| `/finance`                            | `FinancePage`                   | Receitas, despesas e faturas                 |
| `/reports`                            | `ReportsPage`                   | Relatórios                                   |
| `/team`, `/team/chat`                 | `TeamPage`, `TeamChatPage`      | Gestão e conversa da equipe                  |
| `/notifications`                      | `NotificationsPage`             | Caixa de notificações                        |
| `/client-portal`                      | `ClientPortal`                  | Visão do cliente                             |
| `/client-portal/projects/:id`         | `ClientProject`                 | Projeto acessível ao cliente                 |
| `/pricing`                            | `PricingPage`                   | Planos                                       |
| `/billing/success`, `/billing/cancel` | `BillingResult`                 | Retorno do checkout                          |
| `/settings/*`                         | páginas de conta                | Perfil, preferências, billing e notificações |
| `/help`                               | `HelpPage`                      | Ajuda                                        |
| `*`                                   | `NotFoundPage`                  | URL desconhecida                             |

As URLs legadas `/client` e `/client/projects/:id` usam `<Navigate>` para preservar links antigos. `Outlet` em `AppLayout` é o ponto onde a página filha protegida aparece.

**Router** associa URL e componente. **Route** declara essa associação. `Link` navega sem recarregar a aplicação; `NavLink` também informa se o link está ativo; `useNavigate` navega dentro de uma função.

### Perguntas para revisar

1. Por que `Protected` precisa conhecer `isLoading` além de `isAuthenticated`?
2. Para que serve `Outlet`?
3. Qual diferença existe entre uma rota pública e `ProtectedPage`?

## Autenticação e estado global

### `AuthProvider` e `useAuth`

**Arquivo:** `frontend/src/features/auth/AuthContext.tsx`

O provider guarda `user` e `isLoading` com `useState`. Estado é informação que pode mudar durante a vida do componente; chamar o setter provoca uma nova renderização.

```ts
const [user, setUser] = useState<User | null>(null);
```

- `user`: valor atual.
- `setUser`: função de alteração.
- `User | null`: união TypeScript; existe um usuário ou não existe.
- `null`: valor inicial.

O `useEffect` inicial procura `access` ou `refresh` no `localStorage`. `localStorage` é armazenamento persistente do navegador: os valores sobrevivem ao recarregamento da página. Se houver token, `refreshUser` chama `GET /auth/me/`; se não houver, encerra o carregamento.

`useEffect(() => {}, [])` executa após a montagem. Um efeito com `[value]` repete quando `value` muda. Neste caso a dependência é `refreshUser`, estabilizada por `useCallback`. Em efeitos assíncronos de outros componentes, uma função de cleanup marca a execução como inativa para evitar atualização depois da desmontagem.

O login:

```text
login(email, senha)
→ normaliza email
→ POST /auth/login/
→ limpa sessão anterior
→ salva access e refresh
→ setUser(data.user)
→ componentes consumidores renderizam novamente
```

O logout copia o refresh necessário para a chamada remota e imediatamente remove `access`, `refresh`, `organization_id`, a requisição de perfil pendente e o usuário do estado global. Em seguida tenta colocar o refresh na blacklist do backend. A limpeza local continua válida se o token estiver expirado ou a rede indisponível; ao terminar, `window.location.replace('/login')` remove a página protegida da posição atual do histórico. `Protected` volta a validar `isAuthenticated`, portanto atualizar, usar “voltar” ou abrir diretamente uma rota protegida não restaura a sessão encerrada. `useAuth()` encapsula `useContext(AuthContext)` e impede uso fora do provider.

### Formulários de autenticação

**Arquivo:** `frontend/src/pages/AuthPages.tsx`

`LoginPage` e `RegisterPage` usam React Hook Form. `register('email')` conecta o input ao formulário; `handleSubmit` só chama a função quando os dados locais são válidos. Zod descreve o formato esperado, e `zodResolver` integra as duas bibliotecas.

O fluxo do login é:

```text
Usuário preenche inputs
→ evento onSubmit do <form>
→ handleSubmit executa loginSchema
→ useAuth.login
→ Axios POST /api/auth/login/
→ LoginView + LoginSerializer
→ Django verifica hash da senha
→ backend emite access + refresh
→ navegador salva tokens
→ Root/Protected libera o AppLayout
```

`isSubmitting ? 'Entrando…' : 'Entrar'` é um operador ternário: escolhe um valor conforme uma condição. `serverError && <div ...>` é renderização condicional: o elemento só aparece quando existe mensagem.

Labels relacionam texto e campo, `type="email"` ajuda teclado/validação e os botões usam elementos semânticos. O projeto também possui `aria-label` em botões de notificação e perfil. Não existem imagens de conteúdo ou `alt` a documentar no frontend atual; ícones vêm de `lucide-react`.

### Autenticação versus autorização

- Autenticação responde: “quem é você?”. JWT e senha participam dessa etapa.
- Autorização responde: “o que você pode fazer?”. Membership, papel e acesso ao projeto participam dessa etapa.

O access token dura 15 minutos e o refresh, 7 dias (`backend/config/settings.py`). A rotação troca refresh tokens e coloca os anteriores na blacklist. A senha não é armazenada em texto puro; o sistema de autenticação do Django compara hashes.

## Cliente HTTP, API e TanStack Query

### Axios e interceptadores

**Arquivo:** `frontend/src/services/api.ts`

`axios.create({ baseURL })` cria um cliente comum. `VITE_API_URL` define a origem; sem ela, usa `/api`. O interceptor de request adiciona `Authorization: Bearer ...` e, somente em endpoints dependentes de workspace, `X-Organization-ID`.

Se uma resposta chega com 401, o interceptor usa o refresh uma única vez, salva o novo access e repete a requisição original. Requisições simultâneas compartilham a promise `refreshing`, evitando várias renovações concorrentes. Se a renovação falhar, limpa a sessão e redireciona para login.

`getApiErrorDetails` transforma respostas variadas do Django em mensagem geral e erros por campo.

### HTTP e JSON neste projeto

| Método | Uso típico                                           |
| ------ | ---------------------------------------------------- |
| GET    | Ler listas ou detalhes sem alterar dados             |
| POST   | Criar recurso ou executar ação como login/start/stop |
| PATCH  | Alterar parte de um recurso                          |
| DELETE | Remover ou desativar um recurso                      |

JSON representa objetos e arrays transmitidos entre frontend e backend. Status 200 indica sucesso de leitura, 201 criação, 400 dados inválidos, 401 falta de identidade válida, 403 identidade sem permissão, 404 recurso não encontrado/visível e 5xx falha do servidor ou integração.

### Services e hooks

- `frontend/src/services/work.ts`: organizações, clientes, projetos e dashboard.
- `frontend/src/services/tasks.ts`: tarefas, movimento no Kanban, comentários e anexos.
- `frontend/src/services/finance.ts`: horas, financeiro, relatórios e Pix público.
- `frontend/src/features/*/hooks.ts`: adaptam services ao TanStack Query.

Queries leem e guardam cache. Mutations alteram dados e invalidam as chaves relacionadas para que a interface busque uma versão atualizada. As chaves de work e finance incluem o `organization_id`; dados obtidos em um workspace não podem ser reaproveitados visualmente ao trocar para outro. `organizationService.ensure()` preserva o ID armazenado quando ele ainda aparece entre as organizações acessíveis e só usa a primeira como fallback para seleção ausente ou obsoleta. Isso separa “como chamar a API” (service) de “como sincronizar a tela” (hook).

Exemplo:

```text
ProjectsPage
→ useProjects()
→ projectService.list()
→ GET /projects/
→ cache ['projects', organization_id, filtros]
→ cards renderizados com projects.map(...)
```

`map` percorre um array e cria elementos React. A `key` identifica cada item entre renderizações.

## Layout e componentes importantes

### `AppLayout`

**Arquivo:** `frontend/src/layouts/AppLayout.tsx`

É a moldura das páginas autenticadas: sidebar, menu mobile, topbar, busca, notificações, perfil e `Outlet`. Ele chama `organizationService.ensure()`, salva a organização selecionada e decide links conforme `OWNER`, `ADMIN`, `MEMBER` ou `CLIENT`.

`open` controla o menu móvel. O clique executa `setOpen(!open)`:

```text
Usuário clica
→ onClick
→ estado open muda
→ React renderiza
→ classe "open" entra ou sai do aside
→ CSS mostra ou esconde a sidebar
```

O efeito de workspace possui cleanup com `active = false`, evitando que uma promise finalizada depois da navegação altere estado antigo.

### Acesso “Chat da equipe”

**Arquivos:** `frontend/src/pages/Team.tsx` e `frontend/src/styles.css`

Na página de equipe, um `Link` leva a `/team/chat` sem alterar a navegação SPA. Ele usa `MessageCircle` da biblioteca Lucide e a classe dedicada `team-chat-button`. A classe é necessária porque ações de tabela também usam `.actions`, mas precisam de botões compactos; o acesso ao chat é uma ação principal do cabeçalho e requer 44 pixels de altura, padding confortável, tipografia firme e superfície própria.

Os estados são progressivos: hover muda borda/superfície e desloca um pixel; `:focus-visible` cria um contorno perceptível para teclado; `:active` remove a elevação e simula pressão. Claro, escuro e `system` reutilizam `--app-surface`, `--app-border`, `--app-text-secondary` e `--app-accent-soft`, com contraste específico no ícone. A rota e o comportamento não dependem do CSS.

### `Kanban` e `TaskDetails`

**Arquivo:** `frontend/src/components/Kanban.tsx`

`Kanban` recebe props `project` e `members`. Props são entradas enviadas pelo componente pai: `ProjectDetail` informa qual projeto e quais pessoas estão disponíveis. O componente agrupa tarefas por status, abre detalhes e usa mutations para criar, mover, editar e excluir.

As colunas reais são `BACKLOG`, `TODO`, `IN_PROGRESS`, `REVIEW` e `DONE`. `TaskCard` é filho reutilizável. `TaskDetails` reúne formulário, labels, responsáveis, comentários, anexos e atividades.

### Componentes de apresentação

- `frontend/src/components/ui.tsx`: `Button`, `Input`, estados loading/error/empty, `Avatar`, `StatusBadge`, modal e diálogo.
- `frontend/src/components/ProjectCard.tsx`: resumo navegável de projeto.
- `frontend/src/components/TaskCard.tsx`: resumo de uma tarefa e evento de abertura.
- `frontend/src/components/PlanCard.tsx`: plano e ação recebidos por props.
- `frontend/src/components/Toast.tsx`: contexto para feedback temporário.
- `frontend/src/components/ErrorBoundary.tsx`: isolamento de falhas de renderização.

Componentes reutilizáveis reduzem repetição e centralizam acessibilidade e aparência. Um botão comum permite que `disabled`, `focus` e classes sigam o mesmo padrão.

### Páginas por domínio

| Arquivo                   | Responsabilidade principal            |
| ------------------------- | ------------------------------------- |
| `pages/Dashboard.tsx`     | métricas e primeiros passos reais     |
| `pages/Clients.tsx`       | CRUD e detalhe de clientes            |
| `pages/Projects.tsx`      | CRUD, membros, atividades e Kanban    |
| `pages/Tasks.tsx`         | tarefas permitidas e filtros          |
| `pages/TimeTracking.tsx`  | timer e lançamentos                   |
| `pages/Finance.tsx`       | despesas, receitas, faturas e Pix     |
| `pages/Reports.tsx`       | agregações e exportação               |
| `pages/Team.tsx`          | membros, convites, papéis e aprovação |
| `pages/ClientPortal.tsx`  | projetos e entregas do cliente        |
| `pages/PublicPayment.tsx` | cobrança pública somente leitura      |
| `pages/Settings.tsx`      | perfil, billing e notificações        |

Em Perfil, o `input type="file"` permanece oculto e é acionado por um botão acessível. A seleção valida tamanho/MIME antes de criar uma URL temporária com `URL.createObjectURL`; o avatar mostra preview imediatamente, permite escolher outro arquivo ou cancelar e libera a URL com `URL.revokeObjectURL`. O upload só ocorre no submit do formulário, preservando a foto anterior enquanto a alteração não for confirmada.

### Perguntas para revisar

1. Quem envia as props de `Kanban`?
2. Por que services e hooks ficam separados?
3. Qual problema o cleanup do efeito em `AppLayout` evita?

## Tema, idioma e CSS real

### Tema e localização

**Arquivo:** `frontend/src/i18n/index.tsx`

`I18nProvider` lê `user.language`, `user.theme` e `user.timezone`. Antes de o perfil ser restaurado, aceita `preferred_language` salvo para evitar voltar visualmente ao português durante o carregamento. Ele expõe `{ locale, t }`, define `document.documentElement.lang`, grava `data-theme` no elemento `<html>` e mantém locale/timezone no `localStorage`. Navegação, busca e estados compartilhados consomem `t()`; nomes e dados cadastrados pelo usuário não são traduzidos.

```text
Usuário salva preferência
→ PATCH /auth/me/
→ refreshUser
→ I18nProvider recebe user atualizado
→ data-theme muda
→ variáveis CSS selecionadas mudam
→ interface recebe novas superfícies e textos
```

O modo `system` usa `@media (prefers-color-scheme: dark)`. Não existe um `ThemeContext` separado: o tema pertence ao perfil do usuário e é aplicado pelo `I18nProvider`.

A preferência é persistida pelo `PATCH /api/auth/me/` e espelhada em `preferred_language`. Assim, ela permanece ao navegar, atualizar e iniciar uma nova sessão. Novos textos de interface devem entrar no catálogo de `frontend/src/i18n/index.tsx` e ser renderizados por `t()`, sem aplicar tradução a nomes de clientes, projetos, pessoas ou descrições.

### Organização do CSS

**Arquivo:** `frontend/src/styles.css`

`:root` define tokens como `--app-bg`, `--app-surface`, `--app-border` e `--app-text`. Variáveis CSS evitam repetir cores e permitem trocar uma família inteira no seletor `[data-theme='dark']`.

Há níveis de superfície distintos: fundo da aplicação, superfície principal, superfície suave e bordas. A autenticação possui tokens próprios (`--auth-panel`, `--auth-card-surface`, `--auth-input`), criando a hierarquia fundo → painel → card → input.

**Flexbox** organiza elementos em um eixo. Propriedades como `justify-content`, `align-items` e `gap` distribuem navegação, cabeçalhos, botões e linhas de formulário.

**CSS Grid** organiza linhas e colunas. O projeto usa, entre outros:

- `.auth-page`: duas colunas no desktop;
- cards de estatística: quatro, duas ou uma coluna conforme largura;
- Kanban: cinco colunas com largura mínima e rolagem;
- configurações: duas colunas, reduzidas para uma no mobile.

As media queries principais aparecem em 1100, 1000, 800 e 650 pixels. O CSS parte de layouts amplos e os simplifica nos breakpoints, portanto é predominantemente desktop-first.

```text
Login desktop:  área institucional | card de autenticação
Login mobile:   card quase na largura inteira; área institucional reduzida/oculta
```

## TypeScript e JavaScript aplicados

**Arquivos:** `frontend/src/types/index.ts` e `frontend/tsconfig.app.json`

O modo `strict` está ativo. Uma `interface` descreve a forma de um objeto, como `User`, `Project` e `Invoice`. Um `type` também cria tipos e é usado para uniões:

```ts
export type TaskStatus = "BACKLOG" | "TODO" | "IN_PROGRESS" | "REVIEW" | "DONE";
```

Isso impede atribuir um status inventado. `PaginatedResponse<T>` é genérico: `T` pode ser `Client`, `Project` ou outro tipo. `field?: string` seria opcional; arrays aparecem como `Task[]`; `boolean`, `number` e `string` tornam os contratos explícitos.

Arrow functions como `const rootPathFor = (...) => ...` são funções armazenadas em constantes. Desestruturação aparece em `const { user } = useAuth()`: extrai uma propriedade. Spread, como `{ ...props }`, repassa propriedades sem enumerá-las. `condition ? A : B` escolhe; `condition && A` renderiza apenas quando verdadeiro.

TypeScript protege o desenvolvimento, mas não valida dados de rede em runtime. Por isso formulários usam Zod e o backend sempre usa serializers.

## Backend Django: da URL ao banco

### Arquivos estruturais

- `backend/manage.py`: utilitário para `runserver`, `migrate`, `test` e commands.
- `backend/config/settings.py`: apps, banco, JWT, CORS, segurança, Redis, Celery e integrações.
- `backend/config/urls.py`: raiz de endpoints HTTP.
- `backend/config/asgi.py`: HTTP e WebSocket assíncrono.
- `backend/config/wsgi.py`: entrada WSGI compatível.
- `backend/config/celery.py`: aplicação Celery e descoberta de tarefas.

Uma API é uma interface de comunicação entre programas. Neste projeto ela segue REST: recursos têm URLs, métodos HTTP e respostas JSON.

### Apps e padrão interno

Em cada domínio, `models.py` representa dados, `serializers.py` valida/converte, `views.py` executa o caso de uso, `urls.py` publica rotas, `permissions.py` decide acesso e `services.py` concentra regras reutilizáveis. Nem todo app precisa de todos esses arquivos.

```text
requisição
→ urls.py encontra a view
→ autenticação identifica user
→ permission valida papel/acesso
→ serializer valida JSON
→ view/service executa regra
→ model consulta/grava PostgreSQL
→ serializer produz JSON de resposta
```

### Endpoints principais confirmados

| Grupo          | Rotas                                                                                    |
| -------------- | ---------------------------------------------------------------------------------------- |
| Conta          | `/api/auth/register/`, `login/`, `refresh/`, `logout/`, `me/`, `password-reset/`         |
| Organizações   | `/api/organizations/`, `:id/members/`, convites e `team-chat/`                           |
| Planos/billing | `/api/plans/`, `/api/subscription/`, `/api/billing/*`, webhook Mercado Pago              |
| Trabalho       | `/api/clients/`, `/api/projects/`, `/api/tasks/`, labels, comentários, anexos, dashboard |
| Financeiro     | `/api/time-entries/`, member rates, despesas, receitas, faturas, relatórios              |
| Público        | `/api/public/payments/:uuid/`                                                            |
| Portal         | notificações, preferências, entregas, convites e `/api/client-portal/*`                  |
| Operação       | `/health/`, `/health/ready/`, `/admin/`                                                  |

Os `DefaultRouter` do DRF geram automaticamente listagem, criação, detalhe, atualização e remoção dos ViewSets, além de ações decoradas como start, stop, move e generate-payment.

## Referência dos apps Django

Esta seção é o mapa para estudar cada domínio sem confundir responsabilidades. Em todos os endpoints autenticados, o JWT identifica o usuário; em muitos recursos operacionais de tenant, `current_membership()` em `backend/apps/work/context.py` também resolve a membership ativa a partir de `X-Organization-ID`. Views que recebem a organização na própria URL aplicam filtros/permissões equivalentes diretamente.

### `accounts`: identidade e sessão

**Arquivos:** `backend/apps/accounts/models.py`, `serializers.py`, `views.py`, `urls.py`, `tasks.py` e `tests.py`.

- `User` troca o login principal de username para email e acrescenta avatar, biografia, idioma, timezone e tema.
- `UserManager.create_user()` normaliza email, exige identidade e chama `set_password`; `create_superuser()` acrescenta flags administrativas.
- `RegisterSerializer.create()` usa o manager, portanto nunca grava a senha recebida diretamente.
- `LoginSerializer.validate()` autentica email/senha e rejeita conta inativa.
- `LoginView` emite access/refresh do SimpleJWT; `LogoutView` coloca o refresh na blacklist; `MeView` lê e atualiza o perfil.
- `UserSerializer` trata campos de identidade e timestamps como somente leitura. Avatar aceita no máximo 10 MB inclusive e apenas MIME JPEG/PNG/WebP cuja assinatura binária corresponda ao formato declarado.
- `PasswordResetView` cria UID/token de uso único e dispara `send_password_reset_email`; a confirmação valida ambos antes de trocar a senha.

### `organizations`: tenant, equipe e chat

**Arquivos:** `backend/apps/organizations/models.py`, `serializers.py`, `views.py`, `permissions.py`, `services.py`, `tasks.py`, `urls.py` e `tests.py`.

- `create_organization()` executa em transação: cria organização, membership `OWNER` e assinatura gratuita.
- `OrganizationListCreateView` lista organizações com membership ativa; fluxos que exigem aprovação consultam esse estado adicional em `current_membership()` ou na regra específica.
- `OrganizationDetailView` permite leitura ao membro e alteração ao owner.
- `OrganizationMemberDetailView` aprova uma membership pendente, altera papel ou desativa/remove acesso sem permitir alterar/remover o owner.
- Convites guardam apenas `token_hash`; o token em claro existe no link enviado, não no banco.
- `TeamMessageListCreateView` restringe leitura e escrita à organização selecionada.

Papéis reais de `OrganizationMembership.Role`:

| Papel    | Significado operacional                                                |
| -------- | ---------------------------------------------------------------------- |
| `OWNER`  | proprietário; administra workspace, equipe e billing                   |
| `ADMIN`  | gestão operacional ampla, sem substituir garantias exclusivas do owner |
| `MEMBER` | trabalha nos projetos aos quais tem acesso                             |
| `CLIENT` | acesso orientado ao portal e aos projetos do cliente                   |

### `subscriptions`: plano e cobrança do SaaS

**Arquivos:** `backend/apps/subscriptions/models.py`, `policy.py`, `providers.py`, `services.py`, `serializers.py`, `views.py`, `urls.py`, `management/commands/seed_plans.py` e `tests.py`.

- `SubscriptionPolicy` centraliza limites Free/Pro; views de projeto e convites consultam essa política antes de criar recursos.
- `MercadoPagoSubscriptionService` cria/cancela a assinatura externa. `get_subscription_service()` mantém a escolha do provider fora da view.
- `checkout()` e `cancel()` exigem owner; as consultas de billing usam a mesma regra.
- `mercado_pago_webhook()` valida a origem, registra `PaymentEvent` idempotente, consulta o recurso no provider e atualiza assinatura/pagamento.
- `seed_plans` cria ou atualiza o catálogo esperado sem duplicar slugs.

### `work`: clientes, projetos, tarefas e Kanban

**Arquivos:** `backend/apps/work/models.py`, `serializers.py`, `views.py`, `permissions.py`, `context.py`, `services.py`, `urls.py` e `tests.py`.

- `ClientViewSet` e `ProjectViewSet` filtram primeiro por organização e depois por acesso do papel.
- `ProjectAccessPermission` permite escrita para `OWNER` e `ADMIN`; `MEMBER` pode consultar somente projetos em que participa e não recebe criação administrativa. O serializer confirma que o cliente pertence ao workspace resolvido pelo header.
- `ProjectMember` implementa a relação N:N explícita entre usuário e projeto.
- `TaskViewSet.base_queryset_for()` é a fonte compartilhada de isolamento de tarefas; lista/detalhe e ações partem dela.
- `TaskSerializer` valida projeto, responsáveis e labels dentro do mesmo tenant.
- `move()` altera status/posição em transação, chama `normalize_positions()` e recalcula progresso.
- Comentários e anexos possuem endpoints aninhados na tarefa e ViewSets próprios para alteração/remoção segura.
- `log_activity()` registra trilha de auditoria de alterações relevantes.

### `finance`: horas, caixa, faturas e Pix

**Arquivos:** `backend/apps/finance/models.py`, `serializers.py`, `views.py`, `payments.py`, `messaging.py`, `tasks.py`, `urls.py` e `tests.py`.

- `TenantViewSet` injeta organização no serializer e restringe o queryset; `FinancePermission` e `WorkspaceStaffPermission` separam leitura financeira e administração.
- `TimeEntryViewSet.start()` impede dois timers ativos por usuário/organização; `stop()` calcula duração e `summary()` agrega horas e valores.
- `InvoiceSerializer` valida cliente/projeto, cria itens e recalcula subtotal/total no backend.
- `finance_dashboard` agrega duração e custo de horas em SQL, em vez de materializar todos os lançamentos em Python. O número de queries permanece limitado mesmo com aumento de registros.
- O frontend habilita somente a query da aba financeira visível. A estrutura e as abas aparecem sem esperar receitas, despesas e faturas que ainda não foram solicitadas.
- `generate_pix()` cria uma tentativa `InvoicePayment`; `process_mercado_pago_payment()` confirma referência, moeda, valor e idempotência antes de marcar a fatura.
- `deliver_invoice_payment` envia cobrança fora da resposta HTTP; falhas externas permanecem observáveis sem falsificar estado pago.

### `portal`: cliente, entregas e notificações

**Arquivos:** `backend/apps/portal/models.py`, `serializers.py`, `views.py`, `services.py`, `tasks.py`, `consumers.py`, `middleware.py`, `urls.py` e `tests.py`.

- `ClientAccess` liga um usuário a um cliente dentro da organização; o portal deriva projetos dessa ligação.
- `DeliverableViewSet` permite à equipe criar entregas e ao cliente aprovar, pedir mudanças, comentar e anexar conforme acesso.
- `NotificationService.create()` persiste antes de publicar no channel layer e antes do email assíncrono.
- `NotificationConsumer` aceita apenas usuário autenticado e entra no grupo `user_<id>`.
- `JwtQueryAuthMiddleware` autentica o token da query string do WebSocket; isso é separado da autenticação HTTP do DRF.
- Beat executa lembretes diários e geração horária de cobranças agendadas, com `ReminderLog`/estado persistido para evitar duplicação.

### `core` e `payments`

`backend/apps/core/` reúne health/readiness, `RequestIdMiddleware`, normalização de exceções e `seed_demo`. `backend/apps/payments/mercado_pago.py` é o cliente HTTP de baixo nível compartilhável: monta headers, timeouts, chave de idempotência e converte resposta externa em `PixPayment`; regras de fatura continuam em `finance/payments.py`.

### Funções e classes centrais para leitura dirigida

| Símbolo                              | Arquivo                                  | Entrada → retorno               | Chamado por / responsabilidade                                 |
| ------------------------------------ | ---------------------------------------- | ------------------------------- | -------------------------------------------------------------- |
| `current_membership(request)`        | `backend/apps/work/context.py`           | request → membership ou erro    | ViewSets tenant; valida header, usuário, atividade e aprovação |
| `create_organization(*, user, name)` | `backend/apps/organizations/services.py` | usuário/nome → organização      | serializer de organização; cria o tenant completo em transação |
| `SubscriptionPolicy`                 | `backend/apps/subscriptions/policy.py`   | organização → limites/booleanos | criação de projetos e convites; aplica plano atual             |
| `TaskViewSet.base_queryset_for()`    | `backend/apps/work/views.py`             | request → QuerySet              | todas as operações de tarefa; evita IDOR                       |
| `normalize_positions()`              | `backend/apps/work/services.py`          | projeto/status → `None`         | movimento/exclusão; recompõe a ordem do Kanban                 |
| `generate_pix()`                     | `backend/apps/finance/payments.py`       | invoice/opções → pagamento      | ação `generate-payment` e rotina agendada                      |
| `process_mercado_pago_payment()`     | `backend/apps/finance/payments.py`       | payload/event id → pagamento    | webhook; confirma e aplica pagamento uma vez                   |
| `NotificationService.create()`       | `backend/apps/portal/services.py`        | dados da notificação → model    | módulos de negócio; persiste, publica e agenda email           |
| `NotificationConsumer`               | `backend/apps/portal/consumers.py`       | conexão/eventos WS              | ASGI; entrega JSON apenas ao usuário do grupo                  |
| `api_exception_handler()`            | `backend/apps/core/exceptions.py`        | exceção/contexto → Response     | DRF global; padroniza erros sem esconder status                |

## Referência completa da API

Prefixos abaixo são relativos ao host do backend. Recursos de ViewSet também aceitam `GET /:id/`, `PATCH /:id/` e `DELETE /:id/` quando o ViewSet não restringe o método.

| Método            | Endpoint                                                  | Auth/contexto                  | View responsável                       | Finalidade                                |
| ----------------- | --------------------------------------------------------- | ------------------------------ | -------------------------------------- | ----------------------------------------- |
| GET               | `/health/`                                                | pública                        | `core.views.health`                    | liveness do processo                      |
| GET               | `/health/ready/`                                          | pública                        | `core.views.ready`                     | readiness incluindo banco                 |
| POST              | `/api/auth/register/`                                     | pública/throttle auth          | `RegisterView`                         | criar usuário                             |
| POST              | `/api/auth/login/`                                        | pública/throttle auth          | `LoginView`                            | emitir JWT e usuário                      |
| POST              | `/api/auth/refresh/`                                      | refresh JWT                    | `TokenRefreshView`                     | rotacionar tokens                         |
| POST              | `/api/auth/logout/`                                       | JWT                            | `LogoutView`                           | invalidar refresh                         |
| GET/PATCH         | `/api/auth/me/`                                           | JWT                            | `MeView` + `UserSerializer`            | perfil e preferências                     |
| POST              | `/api/auth/password-reset/`                               | pública                        | `PasswordResetView`                    | solicitar recuperação                     |
| POST              | `/api/auth/password-reset/confirm/`                       | UID/token                      | `PasswordResetConfirmView`             | definir nova senha                        |
| GET/POST          | `/api/organizations/`                                     | JWT                            | `OrganizationListCreateView`           | listar/criar workspaces                   |
| GET/PATCH         | `/api/organizations/:id/`                                 | membro/owner                   | `OrganizationDetailView`               | consultar/renomear workspace              |
| GET               | `/api/organizations/:id/members/`                         | membro                         | `OrganizationMembersView`              | listar equipe                             |
| POST/PATCH/DELETE | `/api/organizations/:id/members/:membership_id/`          | owner                          | `OrganizationMemberDetailView`         | aprovar, trocar papel ou desativar acesso |
| GET/POST          | `/api/organizations/:id/team-invitations/`                | owner                          | `TeamInvitationCreateView`             | listar/criar convites                     |
| DELETE            | `/api/organizations/:id/team-invitations/:invitation_id/` | owner                          | `TeamInvitationCancelView`             | cancelar convite                          |
| GET               | `/api/organizations/team-invitations/:token/`             | pública por token              | `TeamInvitationDetailView`             | inspecionar convite válido                |
| POST              | `/api/organizations/team-invitations/accept/`             | pública; token e dados no JSON | `TeamInvitationAcceptView`             | aceitar convite e preparar login          |
| GET/POST          | `/api/organizations/team-chat/`                           | JWT + tenant                   | `TeamMessageListCreateView`            | histórico/enviar mensagem                 |
| GET               | `/api/plans/`                                             | pública                        | `PlanListView`                         | catálogo ativo                            |
| GET               | `/api/subscription/`                                      | JWT + tenant                   | `SubscriptionView`                     | assinatura atual                          |
| GET               | `/api/billing/subscription/`, `usage/`, `payments/`       | owner                          | funções de billing                     | visão administrativa                      |
| POST              | `/api/billing/checkout/`, `cancel/`                       | owner                          | `checkout`, `cancel`                   | iniciar/cancelar assinatura               |
| POST              | `/api/webhooks/mercado-pago/`                             | assinatura do provedor         | `mercado_pago_webhook`                 | sincronizar billing SaaS                  |
| GET/POST          | `/api/clients/`                                           | JWT + tenant                   | `ClientViewSet` + `ClientSerializer`   | CRUD de clientes                          |
| POST              | `/api/clients/:id/invite/`                                | gestor                         | `portal.views.invite_client`           | convidar cliente ao portal                |
| GET/POST          | `/api/projects/`                                          | JWT + tenant                   | `ProjectViewSet` + `ProjectSerializer` | CRUD de projetos                          |
| GET/POST          | `/api/projects/:id/members/`                              | acesso ao projeto              | `members_action`                       | listar/adicionar membros                  |
| DELETE            | `/api/projects/:id/members/:membership_id/`               | gestor                         | `remove_member`                        | remover membro                            |
| GET               | `/api/projects/:id/activities/`, `tasks/`                 | acesso ao projeto              | ações de `ProjectViewSet`              | auditoria e tarefas                       |
| GET/POST          | `/api/tasks/`                                             | JWT + tenant/projeto           | `TaskViewSet`                          | CRUD de tarefas                           |
| PATCH             | `/api/tasks/:id/move/`                                    | acesso de edição               | `TaskViewSet.move`                     | status/posição do Kanban                  |
| GET/POST          | `/api/tasks/:id/comments/`, `attachments/`                | acesso à tarefa                | ações de `TaskViewSet`                 | colaboração e arquivos                    |
| GET               | `/api/tasks/:id/activities/`                              | acesso à tarefa                | `TaskViewSet.activities`               | histórico da tarefa                       |
| GET/POST          | `/api/task-labels/`                                       | JWT + tenant                   | `TaskLabelViewSet`                     | labels da organização                     |
| PATCH/DELETE      | `/api/task-comments/:id/`                                 | autor/acesso                   | `TaskCommentViewSet`                   | editar/remover comentário                 |
| GET/DELETE        | `/api/task-attachments/:id/`                              | acesso                         | `TaskAttachmentViewSet`                | baixar/remover anexo                      |
| GET               | `/api/dashboard/`                                         | JWT + tenant                   | `work.views.dashboard`                 | agregados da home                         |
| GET/POST          | `/api/time-entries/`                                      | JWT + tenant                   | `TimeEntryViewSet`                     | lançamentos de horas                      |
| POST/GET          | `/api/time-entries/start/`, `active/`                     | JWT + tenant                   | ações do timer                         | iniciar/consultar timer                   |
| POST/GET          | `/api/time-entries/:id/stop/`, `summary/`                 | JWT + tenant                   | ações do timer                         | parar/agregar horas                       |
| CRUD              | `/api/member-rates/`, `expenses/`, `revenues/`            | staff do workspace             | ViewSets financeiros                   | custo, despesa e receita                  |
| CRUD              | `/api/invoices/`                                          | staff do workspace             | `InvoiceViewSet`                       | faturas e itens                           |
| POST              | `/api/invoices/:id/send/`, `mark-paid/`, `cancel/`        | staff                          | ações da fatura                        | transições administrativas                |
| POST              | `/api/invoices/:id/generate-payment/`                     | staff                          | `generate_payment`                     | criar/regenerar Pix                       |
| GET               | `/api/public/payments/:token/`                            | pública por UUID               | `public_payment`                       | consultar cobrança sem JWT                |
| GET               | `/api/finance/dashboard/`, `/api/reports/`                | JWT + tenant                   | funções financeiras                    | indicadores e relatórios                  |
| GET               | `/api/reports/hours/export/`                              | JWT + tenant                   | `export_hours`                         | exportar CSV                              |
| GET               | `/api/notifications/`                                     | JWT                            | `NotificationViewSet`                  | caixa do usuário                          |
| GET/POST          | `/api/notifications/unread-count/`, `read-all/`           | JWT                            | ações de notificação                   | contagem/marcar todas                     |
| POST              | `/api/notifications/:id/read/`                            | dono                           | `read`                                 | marcar uma como lida                      |
| GET/PATCH         | `/api/notification-preferences/`                          | JWT                            | `NotificationPreferenceView`           | canais habilitados                        |
| CRUD              | `/api/deliverables/`                                      | equipe/cliente autorizado      | `DeliverableViewSet`                   | entregas do projeto                       |
| POST              | `/api/deliverables/:id/approve/`, `request-changes/`      | cliente autorizado             | ações de entrega                       | decisão do cliente                        |
| POST              | `/api/deliverables/:id/comments/`, `attachments/`         | acesso à entrega               | ações de entrega                       | colaboração                               |
| POST              | `/api/client-invitations/accept/`                         | JWT + token                    | `accept_invitation`                    | criar acesso do cliente                   |
| GET               | `/api/client-portal/dashboard/`, `projects/`              | cliente                        | portal views                           | dados isolados do portal                  |

### Como ler um endpoint gerado pelo router

Para `PATCH /api/tasks/42/move/`, `backend/config/urls.py` inclui `backend/apps/work/urls.py`; o `DefaultRouter` encontra a ação `TaskViewSet.move()`. O DRF autentica o JWT, a ação obtém a tarefa por um queryset já filtrado, o serializer/validação confere o payload e a transação atualiza posições. Um ID invisível ao tenant resulta em 404, não em vazamento de detalhes.

### Perguntas para revisar

1. Qual função forma a fronteira de tenant compartilhada pelos módulos de trabalho?
2. Por que o endpoint público de Pix usa UUID e continua sem aceitar alteração de status?
3. Qual diferença existe entre `InvoicePaymentEvent` e `PaymentEvent` de subscriptions?
4. Onde uma ação customizada de ViewSet se transforma em URL?

## Banco de dados e models

PostgreSQL é configurado por `DATABASE_URL` ou variáveis `DB_*`. Em testes locais, a suíte usa SQLite efêmero; isso não muda o banco de produção.

### Mapa de relações

```text
User
├── OrganizationMembership ── Organization ── Subscription ── Plan
├── ProjectMember ── Project ── Client
├── TaskAssignee ── Task ── Project
├── TimeEntry ── Project/Task
├── Notification
└── ClientAccess ── Client ── ProjectDeliverable

Organization
├── Clients, Projects, Tasks e Labels
├── Expenses, Revenues, Invoices e MemberRates
├── TeamInvitations e TeamMessages
└── Notifications e dados do portal

Invoice
├── InvoiceItem
├── InvoicePayment ── InvoicePaymentEvent
└── Revenue (relação única quando paga)
```

Principais models por arquivo:

- `accounts/models.py`: `User`, baseado em `AbstractUser`, com email como identidade.
- `organizations/models.py`: `Organization`, membership, convite e chat.
- `subscriptions/models.py`: plano, assinatura, eventos e pagamentos do SaaS.
- `work/models.py`: cliente, projeto, membros, atividades, tarefas, labels, comentários e anexos.
- `finance/models.py`: valores por membro, horas, receitas, despesas, faturas, itens e pagamentos.
- `portal/models.py`: acesso do cliente, convites, entregas, comentários, notificações e lembretes.

### Catálogo dos models e regras de esquema

As tabelas resumem os campos de domínio; todos os models recebem ainda a chave primária automática `id` quando não declaram outra. `blank=True` afeta validação de formulários/serializers; `null=True` permite `NULL` no banco. Datas `auto_now_add` registram criação e `auto_now` registram atualização.

| Model (arquivo)                            | Campos e relações relevantes                                                                                           | Garantias importantes                                                                  |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `User` (`accounts/models.py`)              | email único, username opcional, avatar opcional, bio, language, timezone, theme, timestamps                            | `USERNAME_FIELD = "email"`; senha herdada é hash                                       |
| `Organization` (`organizations/models.py`) | name, slug único, owner → User, timestamps                                                                             | owner protegido por FK; slug identifica URL logicamente                                |
| `OrganizationMembership`                   | organization, user, role, is_active, approval_status, joined_at                                                        | único `(organization, user)`                                                           |
| `TeamInvitation`                           | organization, email, role, token_hash único, status, expires_at, invited_by, accepted_at                               | convite pendente único por organização/email; token não fica em claro                  |
| `TeamMessage`                              | organization, author, message até 2.000, created_at                                                                    | índice `(organization, created_at)`                                                    |
| `Plan` (`subscriptions/models.py`)         | name, slug único, price Decimal, billing_interval, is_active, timestamps                                               | catálogo estável por slug                                                              |
| `Subscription`                             | organization 1:1, plan protegido, status/provider IDs, período e cancelamento                                          | no máximo uma assinatura por organização                                               |
| `PaymentEvent`                             | organization opcional, provider, provider_event_id único, type, processed, payload_hash, datas                         | deduplicação do webhook de assinatura                                                  |
| `SubscriptionPayment`                      | subscription, provider_payment_id único, amount, BRL, status, paid_at                                                  | histórico financeiro do SaaS separado das faturas do cliente                           |
| `Client` (`work/models.py`)                | organization, contato/empresa/documento/site/notas, status, created_by, timestamps                                     | índices tenant+status e tenant+nome                                                    |
| `Project`                                  | organization, client, name/description, status, priority, datas, progress 0–100, budget opcional, created_by           | índices tenant+status e tenant+due_date                                                |
| `ProjectMember`                            | project, user, role, joined_at                                                                                         | único `(project, user)`                                                                |
| `ActivityLog`                              | organization, user opcional, action, entity_type/id, metadata JSON, created_at                                         | índice por entidade e tempo; referência genérica auditável                             |
| `TaskLabel`                                | organization, name, color                                                                                              | nome único dentro do tenant                                                            |
| `Task`                                     | organization, project, title/description, status, priority, due_date, position, labels N:N, created_by, timestamps     | índices por projeto/status/posição e tenant; posição não negativa                      |
| `TaskAssignee`                             | task, user, assigned_at                                                                                                | único `(task, user)`; tabela intermediária explícita                                   |
| `TaskComment`                              | task, author, message, timestamps                                                                                      | ordenação cronológica e autoria protegida                                              |
| `TaskAttachment`                           | task, uploaded_by, file, original_name, file_size, content_type, created_at                                            | metadados persistidos; arquivo em `task_attachments/%Y/%m/`                            |
| `MemberRate` (`finance/models.py`)         | organization, user, hourly_cost/rate Decimal                                                                           | único `(organization, user)`                                                           |
| `TimeEntry`                                | organization, project, task opcional, user, descrição, início/fim, segundos, rates snapshot, billable                  | constraint impede mais de um timer aberto por tenant/usuário; índices por data/projeto |
| `Expense`                                  | organization, project opcional, descrição, amount Decimal, category, occurred_on, created_by                           | valor financeiro ligado ao tenant                                                      |
| `Revenue`                                  | organization, project/client opcionais, descrição, amount, occurred_on, created_by, invoice 1:1 opcional               | uma receita automática por fatura                                                      |
| `Invoice`                                  | organization, client, project opcional, number, status, datas, agendamento, notes, subtotal/total, paid_at, created_by | número único dentro da organização                                                     |
| `InvoiceItem`                              | invoice, descrição, quantity/unit_price/total Decimal, time_entries N:N                                                | itens pertencem por cascade; total calculado no backend                                |
| `InvoicePayment`                           | invoice, public_token UUID único, provider/id único, amount/currency/status, Pix/QR, expiração/pagamento, timestamps   | índice invoice+status; tentativa externa separada da fatura                            |
| `InvoicePaymentEvent`                      | provider, provider_event_id único, type, payment opcional, processed_at                                                | webhook Pix idempotente                                                                |
| `ClientAccess` (`portal/models.py`)        | organization, client, user, created_at                                                                                 | único `(organization, client, user)`                                                   |
| `ClientInvitation`                         | organization, client, email, token_hash único, expires/accepted, invited_by, created_at                                | acesso só nasce após aceite válido                                                     |
| `ProjectDeliverable`                       | organization, project, title/description, status, due_date opcional, created_by, timestamps                            | estados controlam aprovação/pedido de mudança                                          |
| `DeliverableComment`                       | deliverable, author, message, created_at                                                                               | colaboração vinculada à entrega visível                                                |
| `DeliverableAttachment`                    | deliverable, uploaded_by, arquivo e metadados, created_at                                                              | upload em `deliverables/%Y/%m/`                                                        |
| `Notification`                             | organization, user, type/title/message, data JSON, read_at, created_at                                                 | índice `(user, read_at, created_at)`                                                   |
| `NotificationPreference`                   | user 1:1, email_enabled, in_app_enabled                                                                                | uma preferência por usuário                                                            |
| `ReminderLog`                              | invoice, reminder_date, created_at                                                                                     | único `(invoice, reminder_date)` contra lembrete duplicado                             |

#### Relações e decisões importantes

- FKs de tenant são deliberadamente repetidas em vários models: isso permite filtrar diretamente por organização e torna o isolamento explícito.
- Valores monetários usam `DecimalField`, não `float`, para evitar erros binários de arredondamento.
- Relações N:N com dados próprios (`ProjectMember`, `TaskAssignee`) viram models intermediários; labels e time entries podem usar ManyToMany direto porque a ligação não possui papel adicional relevante.
- `CASCADE` é usado quando o filho perde sentido sem o pai, como itens da fatura; `PROTECT` preserva autoria ou catálogo quando apagar o pai destruiria histórico.
- Índices seguem filtros frequentes de tenant, status, data e ordenação. Eles aceleram leitura, mas acrescentam custo de escrita e espaço.

`ForeignKey` representa muitos registros ligados a um pai; `OneToOneField` limita a um; `ManyToManyField` cria relações muitos-para-muitos. `on_delete=CASCADE` remove filhos com o pai; `PROTECT` impede apagar uma referência necessária.

### Migrations

Migrations são o histórico versionado do esquema. `python manage.py makemigrations` cria propostas a partir dos models; `python manage.py migrate` aplica operações. Nunca se deve apagar migrations válidas apenas por parecerem antigas.

## Multi-tenancy, RBAC e segurança

O frontend seleciona o workspace com `X-Organization-ID`, mas esse header não concede acesso. `backend/apps/work/context.py`, querysets e permissions consultam uma `OrganizationMembership` ativa. OWNER, ADMIN, MEMBER e CLIENT recebem visões diferentes; membros comuns ainda podem depender de `ProjectMember`.

O ID selecionado deve existir na lista devolvida por `/api/organizations/`. Um valor local obsoleto cai para a primeira organização acessível; um header apontando para organização sem membership produz 403. Caches de clientes, projetos, dashboard e financeiro incluem a organização, evitando vazamento visual por reutilização de resposta anterior.

Esse desenho evita IDOR: trocar manualmente um ID na URL ou no header não deve revelar objeto de outra organização. A interface esconder um menu é apenas UX; a proteção real precisa estar no backend.

Outras defesas em `settings.py`:

- validação de senha do Django;
- CORS apenas para origens configuradas;
- CSRF trusted origins;
- throttling anônimo, autenticado e sensível;
- cookies seguros, HSTS e redirecionamento HTTPS em produção;
- `X_FRAME_OPTIONS = DENY`;
- request ID por middleware;
- erros normalizados por `api_exception_handler`.

## Fluxos completos do sistema

### Cadastro e criação do workspace

```text
RegisterPage valida Zod
→ POST /api/auth/register/
→ RegisterView/RegisterSerializer cria User com senha hasheada
→ AuthProvider faz login
→ /onboarding/workspace
→ POST /api/organizations/
→ transação cria Organization + membership OWNER + assinatura Free
→ organization_id salvo no navegador
→ dashboard liberado
```

### Criar projeto e tarefa

```text
ProjectsPage exige cliente
→ useCreateProject mutation
→ POST /api/projects/ + header de organização
→ ProjectViewSet valida RBAC, cliente e limite do plano
→ ProjectSerializer grava Project
→ criador entra como PROJECT_MANAGER
→ caches de projetos e dashboard da organização são invalidados
→ ProjectDetail abre Kanban
→ useCreateTask → POST /api/tasks/
→ TaskSerializer valida projeto, responsáveis e labels
→ tarefa aparece na coluna correspondente
```

Falhas de serializer, permissão ou plano são normalizadas por `getApiErrorDetails` e mostradas no formulário; o frontend não converte um 400/403 em sucesso. Um cliente de outra organização continua retornando erro de validação, e um header de organização sem membership retorna 403.

### Mover uma tarefa

```text
arrastar/ação no Kanban
→ taskService.move(id, status/posição)
→ PATCH /api/tasks/:id/move/
→ backend valida projeto e permissão
→ persiste nova ordem
→ query de tarefas é atualizada
→ colunas renderizam novamente
```

### Gerar e pagar uma cobrança Pix

```text
OWNER abre Financeiro; somente a query da aba ativa é executada
→ abre Nova cobrança e seleciona cliente/projeto compatíveis
→ formulário mostra valor e vencimento no resumo responsivo
→ OWNER cria Invoice e itens
→ POST /api/invoices/:id/generate-payment/
→ backend calcula valor (Decimal)
→ Mercado Pago cria Pix
→ InvoicePayment guarda tentativa, QR e token público
→ link /pagar/:uuid é enviado/copiado
→ pagador consulta GET público sem JWT
→ Mercado Pago envia webhook HMAC
→ backend consulta o pagamento autenticado
→ confere referência, moeda e valor
→ marca pagamento/fatura e cria Revenue uma única vez
```

O frontend nunca decide que uma cobrança foi paga. Polling público melhora a experiência, mas webhook validado é a confirmação confiável.

O formulário mantém cliente, projeto opcional, descrição, valor, vencimento, liberação e opções de geração existentes. O novo layout altera apenas hierarquia visual, mensagens de erro e responsividade; subtotal, total, permissões e geração Pix continuam sendo regras do backend.

### Assinatura Pro

O preço de R$ 25 é definido pelo backend. `backend/apps/subscriptions/policy.py` centraliza limites. Checkout cria a assinatura recorrente e o retorno do navegador não ativa o plano; webhook assinado e consulta ao provedor atualizam a assinatura. Idempotência impede processar o mesmo evento duas vezes.

## WebSocket, Redis e Celery

HTTP segue o modelo requisição/resposta. WebSocket mantém uma conexão aberta para o servidor enviar eventos sem esperar nova requisição.

**Arquivos:** `backend/config/asgi.py`, `backend/apps/portal/middleware.py`, `backend/apps/portal/consumers.py` e `frontend/src/features/notifications/hooks.ts`.

```text
frontend abre /ws/notifications/?token=JWT
→ JwtQueryAuthMiddleware valida access token
→ NotificationConsumer entra no grupo user_<id>
→ serviço publica notification_created
→ Redis Channel Layer distribui o evento
→ frontend invalida queries de notificações
```

Sem `VITE_WS_URL` compatível, o frontend usa polling HTTP. Sem `REDIS_URL`, desenvolvimento usa cache local, channel layer em memória e Celery eager. Isso funciona em um processo, mas não substitui Redis quando há múltiplos processos.

`useNotificationsSocket` só tenta conexão quando há workspace, access token e um destino permitido. Em localhost, monta `ws://` ou `wss://` a partir da página; fora do ambiente local exige `VITE_WS_URL` explícita. A URL efetiva é `/ws/notifications/?token=<JWT>`, mas tokens nunca devem ser registrados em logs ou documentação.

Quando a conexão abre, a tentativa volta a zero. Quando fecha involuntariamente, o hook reconecta com backoff exponencial: aproximadamente 1, 2, 4, 8 segundos, limitado a 30 segundos. Ao receber uma mensagem, ele não confia no payload como única fonte de verdade: invalida as queries `notifications` e `notification-count`, que consultam novamente a API persistida.

O cleanup marca a conexão como encerrada, cancela o timer e fecha o socket. Se ele ainda estiver conectando, registra um listener único para fechá-lo assim que abrir. No backend, `JwtQueryAuthMiddleware` associa o token ao usuário; `NotificationConsumer` rejeita anônimos com código 4401, adiciona autenticados ao grupo `user_<id>` e remove o canal no disconnect.

`localhost:6379` significa Redis na mesma máquina do processo. `redis:6379` é o hostname do serviço dentro da rede Docker Compose; um backend executado diretamente no Windows não resolve esse nome Docker.

Celery worker executa tarefas; Celery Beat agenda lembretes diários e geração programada por hora. PostgreSQL continua sendo a fonte de verdade — Redis não deve guardar o único exemplar de dados de negócio.

## Docker e infraestrutura

Uma imagem é um pacote imutável; um container é uma execução da imagem. `Dockerfile` ensina como construir uma imagem; Compose conecta vários serviços.

### Dockerfiles

**Backend:** `backend/Dockerfile`

- `FROM python:3.13-slim`: imagem base.
- `WORKDIR /app`: diretório dos comandos.
- `COPY requirements.txt` e `RUN pip install`: dependências com cache eficiente.
- `COPY ...`: código.
- `USER devflow`: processo não-root em produção.
- `EXPOSE 8000`: porta documental.
- `CMD daphne ... config.asgi:application`: inicia HTTP e WebSocket ASGI.

**Frontend:** `frontend/Dockerfile`

É multi-stage: Node 22 executa `npm ci` e `npm run build`; depois Nginx recebe apenas `dist`. Assim ferramentas de compilação não aumentam a imagem final.

### Serviços Compose

| Serviço            | Função                          | Comunicação                  |
| ------------------ | ------------------------------- | ---------------------------- |
| `db`               | PostgreSQL                      | backend/worker               |
| `redis`            | cache, broker e Channels        | backend/worker/beat          |
| `backend`          | API Django                      | porta 8000 local             |
| `celery_worker`    | tarefas assíncronas             | banco e Redis                |
| `celery_beat`      | agenda periódica                | Redis                        |
| `frontend`         | Vite local ou Nginx em produção | navegador                    |
| `nginx` (produção) | TLS e proxy                     | frontend, backend, WebSocket |

Volumes preservam PostgreSQL, Redis, media e estáticos. `depends_on` com healthcheck ordena inicialização. Na produção, Nginx encaminha `/api` e `/health` ao backend, `/ws` com upgrade WebSocket e demais URLs ao frontend.

## Variáveis de ambiente

**Referências:** `.env.example`, `.env.production.example` e `backend/config/settings.py`.

`.env` contém configuração local e não deve ser versionado. `.env.example` contém apenas nomes e exemplos seguros. No frontend, apenas variáveis prefixadas por `VITE_` entram no bundle e ficam visíveis ao navegador; nunca coloque um access token do Mercado Pago nelas.

Grupos reais:

- Django: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`.
- Banco: `DATABASE_URL` ou `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
- Origens: `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`.
- Frontend: `VITE_API_URL`, `VITE_PROXY_TARGET` e, quando aplicável, `VITE_WS_URL`.
- Redis/Celery: `REDIS_URL`, broker e result backend derivados.
- Email/WhatsApp: SMTP, `MESSAGE_PROVIDER`, URL e token.
- Mercado Pago: ambiente, base URL, access token e segredo de webhook.

## Vite, scripts e dependências

**Arquivos:** `frontend/package.json` e `frontend/vite.config.ts`.

Vite oferece dev server, HMR (atualização rápida durante edição) e build. O proxy envia `/api` e `/health` para o backend e converte `/ws` para destino WebSocket.

| Comando                 | Efeito                                            |
| ----------------------- | ------------------------------------------------- |
| `npm run dev`           | servidor Vite em desenvolvimento                  |
| `npm run build`         | checagem TypeScript + bundle minificado em `dist` |
| `npm test`              | testes Vitest                                     |
| `npm run test:coverage` | testes e relatório V8                             |
| `npm run lint`          | ESLint no `src`                                   |
| `npm run format:check`  | verifica Prettier sem modificar                   |

ESLint procura problemas de código e padrões inválidos. Prettier padroniza apresentação. Eles se complementam, mas não são a mesma ferramenta.

Dependências diretas importantes foram apresentadas na stack. `lucide-react` fornece ícones; React DOM monta a aplicação; Testing Library testa como um usuário; jsdom simula navegador; Vitest executa testes.

## Build, desenvolvimento e produção

Em desenvolvimento, Vite serve módulos e HMR na porta 5173, Django pode usar 8000, e serviços podem rodar em Docker. Em produção, TypeScript e JSX são convertidos, minificados e escritos em `dist`; Nginx serve arquivos estáticos e Daphne executa Django ASGI.

```text
Desenvolvimento: código fonte → Vite dev server → navegador
Produção: código fonte → npm run build → dist → Nginx/CDN → navegador
```

`frontend/vercel.json` reescreve URLs que não começam com `/api` para `index.html`, permitindo abrir `/dashboard` diretamente e deixar o React Router decidir. `docs/DEPLOYMENT.md` também documenta uma implantação separada Vercel frontend/backend. O deploy não é automático apenas por existir configuração: domínio, conta, secrets e infraestrutura externa precisam ser configurados.

O caminho VPS usa `docker-compose.prod.yml`, certificados em `deploy/certs`, Nginx, Daphne, PostgreSQL e Redis. Não foi possível confirmar pelos arquivos atuais qual desses caminhos é o único ambiente de produção ativo; ambos estão documentados.

## Git e `.gitignore`

- `git status`: mostra alterações.
- `git add`: escolhe mudanças para o próximo commit.
- `git commit`: grava um ponto do histórico local.
- `git push`: envia commits ao repositório remoto.

O `.gitignore` real exclui `.env*` (preservando exemplos), ambientes virtuais, `node_modules`, `dist`, caches, cobertura, bancos locais, logs, media e certificados. Esses arquivos são gerados, específicos da máquina ou sensíveis; versioná-los tornaria o repositório pesado ou inseguro.

## Referência de comandos

Execute os comandos a partir da raiz, salvo quando a linha começa com `cd frontend` ou `cd backend`. Em PowerShell, ative a venv com `.\.venv\Scripts\Activate.ps1`; em Bash, use `source .venv/bin/activate`.

### Ambiente Python e Django

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python backend/manage.py check
python backend/manage.py runserver
```

Os dois primeiros criam o ambiente isolado e instalam dependências de runtime e qualidade. `check` valida configuração sem iniciar o servidor; `runserver` atende normalmente em `http://127.0.0.1:8000`. Use `python backend/manage.py shell` para investigar models de forma controlada e `python backend/manage.py createsuperuser` para acesso local ao admin.

```bash
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py makemigrations
python backend/manage.py migrate
python backend/manage.py showmigrations
```

O primeiro é somente verificação e deve ficar limpo na CI. O segundo cria arquivos de migration depois de uma alteração intencional de model; revise o arquivo antes de `migrate`. `showmigrations` diferencia migration existente de aplicada.

```bash
python backend/manage.py seed_plans
python backend/manage.py seed_demo
```

`seed_plans` sincroniza o catálogo mínimo de planos e é usado pelo Compose local. `seed_demo` cria dados demonstrativos; execute apenas em ambiente de desenvolvimento apropriado.

### Frontend, Vite, lint e build

```bash
cd frontend
npm ci
npm run dev
npm run lint
npm run format:check
npm run build
```

`npm ci` reproduz exatamente `package-lock.json`; prefira-o em CI ou checkout limpo. `dev` inicia Vite/HMR em `0.0.0.0:5173`. `lint` analisa `src`; `format:check` não altera arquivos; `build` roda `tsc -b` e cria `frontend/dist` com Vite.

`npm run format` **altera** arquivos para aplicar Prettier. Use apenas quando quiser essa mudança e sempre revise `git diff`.

### Testes e cobertura

```bash
python backend/manage.py test apps
coverage run backend/manage.py test apps
coverage report --show-missing
cd frontend && npm test
cd frontend && npm run test:coverage
python -m unittest discover -s tests -t . -v
python tests/run_all.py
```

- Django testa os apps com banco temporário; coverage mede somente `backend/apps`, omitindo migrations, testes e admin conforme `pyproject.toml`.
- `npm test` usa `vitest run`, portanto termina após uma execução; `test:coverage` usa provider V8.
- A suíte transversal lê contratos/arquivos e não substitui os testes Django ou React.
- `tests/run_all.py` coordena as verificações locais descritas em `tests/README.md`.

### Docker e operação

```bash
docker compose config
docker compose build
docker compose up
docker compose ps
docker compose logs -f backend
docker compose exec backend python manage.py showmigrations
docker compose down
```

`config` resolve YAML e variáveis sem subir serviços. `up` inicia banco, Redis, API, worker, beat e frontend; acrescente `-d` para segundo plano. `down` remove containers/rede, mas preserva volumes porque não usa `-v`. Para produção, passe explicitamente `-f docker-compose.prod.yml` e use o processo operacional aprovado para secrets, backup, migração e rollback.

### Git para um ciclo seguro

```bash
git status
git branch --show-current
git diff
git diff -- DOCUMENTAÇÃO.md
git log --oneline --decorate -n 10
git pull --ff-only
git add <arquivo-revisado>
git commit -m "tipo: descrição"
git push
```

`status` mostra mudanças; `diff` revisa conteúdo; `log` inspeciona histórico; `pull --ff-only` recusa merge implícito. `add`, `commit` e `push` mudam o estado local/remoto e só devem ser usados depois de revisão consciente. Para criar uma linha de trabalho: `git switch -c nome-da-branch`; para retornar a uma branch existente: `git switch nome`.

### Diagnóstico rápido

```bash
python backend/manage.py check --deploy --settings=config.settings_production
docker compose logs --tail=200 backend
docker compose logs --tail=200 celery_worker
docker compose exec db pg_isready
docker compose exec redis redis-cli ping
```

O check de deploy aponta configurações inseguras, mas precisa das variáveis de produção representativas e não publica nada. Logs devem ser compartilhados somente depois de remover tokens, cookies, payloads pessoais e URLs com credenciais.

## Testes e qualidade

Há três camadas complementares:

1. `backend/apps/*/tests.py`: Django TestCase, TransactionTestCase e DRF APITestCase para autenticação, RBAC, isolamento, models, APIs, billing, pagamentos e WebSocket.
2. `frontend/src/**/*.test.ts(x)`: Vitest, jsdom e Testing Library para rotas, autenticação, hooks, cliente Axios, equipe, pagamentos, formatação e fluxos guiados.
3. `tests/`: `unittest` da biblioteca padrão para contratos transversais, integração estática, segurança, smoke remoto e runner completo.

### Como as suítes se organizam

Os testes backend criam um banco efêmero e exercitam serializers, views, permissions e ORM juntos. `APITestCase` simula HTTP sem chamar um deployment; `TransactionTestCase` é usado quando o comportamento assíncrono do Channels precisa de transações reais. `WebsocketCommunicator` testa conexão JWT válida e rejeição de token inválido.

No frontend, jsdom fornece DOM sem abrir navegador. Testing Library busca elementos como uma pessoa faria, e `user-event` dispara interação. `vi.mock` substitui fronteiras externas: os testes de autenticação controlam respostas da API; os de pagamento não criam Pix; os de equipe simulam services. Um adapter Axios local permite observar headers e uma resposta 401 sem rede real. Regressões específicas verificam limpeza imediata do logout, persistência pt-BR/en, workspace selecionado, ausência de requests financeiras para abas inativas e fronteira de 10 MB do avatar.

No backend, testes adicionais exercitam criação de projeto por admin secundário, header incorreto, isolamento entre tenants, blacklist do refresh, imagem com assinatura falsa, tamanho exato/acima de 10 MB e quantidade limitada de queries no dashboard financeiro. O teste de performance verifica queries, não tempo absoluto, para evitar instabilidade entre máquinas.

`tests/fixtures.py` produz nomes temporários únicos com UUID para evitar colisões em ambientes controlados. O runner remoto permanece somente leitura em produção: `tests/config.py` exige HTTPS, bloqueia escrita e lê URLs/credenciais por variáveis sem imprimi-las. O smoke é opt-in localmente e cobre health, rotas diretas e preflight CORS.

### Unitário versus integração neste projeto

Um teste unitário isola uma decisão pequena, como `rootPathFor`, formatação ou seleção do header de organização. Um teste de integração conecta mais camadas, como request DRF → permission → serializer → banco. Os testes transversais conferem contratos entre arquivos, por exemplo se services frontend têm endpoints backend correspondentes. Nenhum desses substitui smoke em um deployment real.

Comandos principais:

```powershell
.\.venv\Scripts\python.exe backend\manage.py test apps
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
.\.venv\Scripts\python.exe tests\run_all.py
```

Outras execuções úteis:

```powershell
.\.venv\Scripts\python.exe -m coverage run backend\manage.py test apps
.\.venv\Scripts\python.exe -m coverage report
npm --prefix frontend run test:coverage
.\.venv\Scripts\python.exe tests\run_all.py --fast
.\.venv\Scripts\python.exe tests\run_all.py --category security
```

`tests/run_all.py` configura SQLite apenas para a suíte Django local, executa checks, plano de migrations, Vitest, TypeScript, ESLint, build e categorias transversais. Ao final grava `tests/reports/latest-report.txt` e `.json`; esses relatórios são gerados e ignorados pelo Git.

A cobertura mínima configurada é 80% no backend (`pyproject.toml`). O frontend mantém limites globais iniciais em `vite.config.ts`: 10% de statements, 8% de branches, 4% de functions e 12% de lines. Os relatórios V8 usam texto, JSON summary e LCOV; arquivos não testados continuam visíveis, evitando uma métrica artificialmente filtrada.

### CI/CD com GitHub Actions

**Arquivo:** `.github/workflows/ci.yml`

O workflow inicia em push para `main` e em pull requests:

```text
código enviado ao GitHub
→ checkout do repositório
→ jobs backend, frontend, transversal e docker
→ qualquer gate obrigatório que falhar deixa a CI vermelha
→ relatórios de cobertura são preservados como artefatos
```

O job `backend` sobe PostgreSQL 16 e Redis 7 como services, instala `requirements-dev.txt`, executa Ruff, `manage.py check`, verifica migrations não geradas e roda `coverage run backend/manage.py test apps`. O argumento `apps` é importante quando o comando parte da raiz: ele seleciona explicitamente os testes Django dos domínios, enquanto os testes transversais ficam no job próprio. O gate é 80%, o XML é enviado como `backend-coverage`, e `pip-audit` verifica dependências declaradas.

O job `frontend` usa Node 22 e `npm ci`, depois ESLint, Vitest com coverage, build TypeScript/Vite e `npm audit --audit-level=high`. A pasta `frontend/coverage` é publicada como artefato `frontend-coverage` mesmo quando uma etapa falha.

O job `transversal` executa `python -m unittest discover -s tests -t . -v`. O job `docker` reconstrói as imagens com `docker compose build`, detectando Dockerfiles ou dependências quebradas. Os jobs são independentes, portanto podem executar em paralelo.

### O que aprender com essa estratégia

Testar comportamento reduz regressões; medir cobertura revela áreas pouco exercitadas; lint e build detectam classes diferentes de erro; CI prova que tudo nasce de um checkout limpo, sem depender do estado da máquina de um desenvolvedor.

### Perguntas para revisar

1. Por que testes frontend não substituem testes de permission no backend?
2. Qual diferença há entre smoke remoto e teste Django com banco efêmero?
3. Por que cobertura alta não prova ausência de bugs?

## O que acontece quando você abre o site

1. O navegador solicita o domínio.
2. Vite, Nginx ou a plataforma de deploy devolve `index.html`.
3. O navegador baixa o módulo referenciado por `main.tsx` ou seu bundle compilado.
4. React monta providers e `App` em `#root`.
5. `AuthProvider` verifica a sessão armazenada.
6. `BrowserRouter` lê a URL.
7. `RootRedirect` ou uma rota escolhe a página.
8. Em área autenticada, `AppLayout` descobre organização e papel.
9. Hooks consultam endpoints com JWT e organização.
10. Django valida autenticação, tenant e RBAC, consulta PostgreSQL e responde JSON.
11. TanStack Query guarda o resultado; React renderiza componentes.
12. `styles.css` aplica layout, responsividade e tema.
13. Eventos de clique, mudança e submit passam a atualizar estado, navegar ou chamar a API.

## Troubleshooting didático

### Página branca

Confira console do navegador, import quebrado, `#root` e `main.tsx`. `ErrorBoundary` deve capturar erros de renderização, mas falhas anteriores à montagem ainda podem aparecer no console. Rode `npm run build`.

### API 401

O access pode ter expirado. Verifique refresh no `localStorage`, resposta de `/auth/refresh/` e relógio do ambiente. Não imprima tokens.

### API 403

Autenticação ocorreu, mas o papel, membership, projeto ou plano não permite a ação. Verifique `X-Organization-ID` e permissions; não “corrija” apenas exibindo o botão.

### API 404 em objeto existente

Querysets filtrados por tenant podem deliberadamente responder 404 para não revelar objetos externos. Confirme organização e acesso ao projeto.

### CORS

Compare a origem exata do frontend com `CORS_ALLOWED_ORIGINS` e confira se `x-organization-id` está permitido. CORS não é resolvido adicionando `*` indiscriminadamente.

### WebSocket falha

Confira `VITE_WS_URL`, token, suporte da hospedagem, proxy `/ws`, Daphne e Redis. Sem WebSocket, polling deve manter notificações funcionais.

### Redis não conecta

Use `localhost:6379` para processo local e `redis:6379` dentro do Compose. Se Redis for intencionalmente omitido, deixe `REDIS_URL` vazio para ativar fallbacks.

### Migrations pendentes

Rode `python backend/manage.py showmigrations --plan` e, no banco correto, `migrate`. Nunca aplique migrations em produção sem backup e revisão.

### Porta ocupada

Ajuste `BACKEND_PORT`/`FRONTEND_PORT` no ambiente e mantenha URLs/proxies consistentes.

### Django encontra a suíte errada quando executado da raiz

**Sintoma:** `coverage run backend/manage.py test` registra os testes transversais do diretório raiz em vez dos testes dos apps Django, produzindo contagem e cobertura enganosas.

**Causa:** a descoberta padrão parte do diretório corrente e encontra o pacote `tests/` antes da suíte desejada.

**Como investigar:** compare os nomes exibidos com `backend/apps/*/tests.py` e execute o comando a partir de `backend` ou informe o label explicitamente.

**Solução atual:** a CI usa `coverage run backend/manage.py test apps`; o runner local muda o diretório de trabalho para `backend` antes de `manage.py test`.

### Um botão dentro de `.actions` perde seu visual

**Sintoma:** um link com classe `.button` aparece pequeno, transparente ou sem borda.

**Causa:** regras genéricas posteriores para `.actions a` são mais recentes na cascata e podem sobrescrever estilos básicos.

**Como investigar:** use a aba Computed do DevTools para descobrir qual seletor venceu e em qual linha.

**Solução aplicada ao chat:** `.actions .team-chat-button` tem responsabilidade e especificidade próprias, mantendo foco, hover, active e dark mode sem alterar regras das ações compactas de tabela.

## Exercícios seguros

1. Localize a rota `/tasks` em `App.tsx` e siga seus imports até `taskService.list`.
2. Identifique quais tokens CSS mudam entre tema claro e escuro sem alterar o arquivo.
3. Desenhe o fluxo de `useCreateProject` até `ProjectViewSet`.
4. Encontre onde o frontend evita enviar organização para `/auth/login/`.
5. Liste as validações locais do cadastro e compare com o serializer backend.
6. Execute somente os testes de `accounts` em um banco de teste.
7. Descubra qual mutation invalida o cache depois de mover tarefa.
8. Compare `backend/Dockerfile` e `Dockerfile.dev` e explique o usuário não-root.
9. Use `git status` e `git diff -- ESTUDO_DO_PROJETO.md` para revisar esta apostila.
10. Sem modificar dados, consulte `/health/` e explique por que `/health/ready/` é mais exigente.

## Mapa mental final

```text
DEVFLOW
├── HTML
│   └── index.html → #root
├── React + TypeScript
│   ├── main.tsx → providers
│   ├── App.tsx → rotas e proteção
│   ├── layouts → estrutura autenticada
│   ├── pages → casos de uso
│   ├── components → blocos reutilizáveis
│   ├── hooks → estado remoto/mutations
│   ├── services → HTTP Axios
│   └── types → contratos
├── CSS
│   ├── tokens de superfície/tema
│   ├── Flexbox/Grid
│   └── media queries
├── API Django REST
│   ├── URLs → views → serializers
│   ├── permissions/RBAC
│   ├── services/tasks
│   └── models/migrations
├── PostgreSQL → fonte de verdade
├── Redis/Channels/Celery → cache, eventos e tarefas
├── Mercado Pago → Pix e assinatura
├── Docker/Nginx → execução e proxy
├── Vercel/VPS → caminhos de deploy documentados
└── Testes/CI → proteção contra regressões
```

# Como construir este projeto do zero

Esta parte muda a perspectiva. Até aqui estudamos o sistema pronto. Agora vamos pensar como quem ainda tem uma pasta vazia e precisa chegar a uma versão semelhante com segurança.

Um sistema não nasce completo. A ordem saudável é:

```text
entender o problema
→ modelar o menor domínio útil
→ fazer backend funcionar sozinho
→ fazer frontend funcionar sozinho
→ ligar os dois
→ entregar uma funcionalidade vertical
→ testar
→ repetir
→ adicionar infraestrutura somente quando ela resolve um problema real
```

Não tente construir autenticação, Kanban, pagamentos, WebSocket, Docker e deploy ao mesmo tempo. Use o ciclo `criar → testar → confirmar → continuar`.

## Etapa 1. Preparar o repositório e as ferramentas

### Objetivo

Criar as fundações Python/Django e React/TypeScript sem implementar regras de negócio.

### O que vamos criar

```text
devflow/
├── backend/
├── frontend/
├── .gitignore
├── .env.example
└── README.md
```

### Por que começamos por aqui

Ferramentas e diretórios estáveis evitam misturar dependências Python, dependências Node e segredos. Neste ponto ainda não precisamos de Redis, pagamentos ou Docker.

### Passo a passo

Com Python 3.13 e Node 22 instalados:

```powershell
mkdir devflow
cd devflow
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install Django djangorestframework
npm create vite@latest frontend -- --template react-ts
mkdir backend
django-admin startproject config backend
```

`python -m venv` cria um ambiente isolado. `pip install` instala Django e DRF dentro dele. `npm create vite` gera HTML, TypeScript, configuração e scripts básicos. `django-admin startproject config backend` cria `manage.py` e o pacote de configurações.

Depois instalaríamos, conforme o `package.json` e `backend/requirements.txt` atuais, React Router, TanStack Query, Axios, React Hook Form, Zod, SimpleJWT, CORS headers, filters, Channels, Celery e drivers de banco. Use arquivos de requirements/lock; não dependa de instalações globais.

### Como testar

```powershell
python backend\manage.py check
npm --prefix frontend install
npm --prefix frontend run dev
```

### Resultado esperado

Django passa no check e a tela inicial do Vite abre. Não há funcionalidade DevFlow ainda.

### Erros comuns

- instalar pacotes fora da `.venv`;
- versionar `.env`;
- executar npm na raiz quando `package.json` fica em `frontend`;
- escolher versões diferentes sem revisar compatibilidade.

### Princípio de engenharia

Separar ambientes é uma decisão arquitetural pequena que reduz erros durante todo o projeto.

### Checkpoint

Antes de continuar, você deve iniciar frontend e backend separadamente e explicar onde ficam suas dependências.

## Etapa 2. Descobrir o domínio antes de criar telas

### Objetivo

Transformar o problema “gerenciar trabalho de equipes” em entidades e relações.

### Por que esta etapa vem antes da API

Uma API sem domínio claro vira uma coleção de endpoints inconsistentes. Pergunte primeiro:

- uma pessoa pode participar de mais de uma organização? Sim;
- um projeto pertence a qual organização e cliente? A uma organização e a um cliente;
- tarefa pode ter vários responsáveis e labels? Sim;
- uma fatura pode ter vários itens? Sim;
- cliente do portal é igual a membro da equipe? Não.

### Primeira modelagem

Começaríamos pelo núcleo:

```text
User ← OrganizationMembership → Organization
Organization → Client → Project → Task
```

`OrganizationMembership` resolve uma relação N:N entre usuários e organizações e ainda guarda papel e estado. `ProjectMember` faz o mesmo entre usuário e projeto. Campos de identificação pública, dinheiro e datas devem ser pensados antes de codificar: email é único; UUID público de cobrança não deve ser enumerável; dinheiro usa `Decimal`, nunca `float`.

### Arquivos envolvidos

- `backend/apps/accounts/models.py`
- `backend/apps/organizations/models.py`
- `backend/apps/work/models.py`
- depois, `finance/models.py`, `subscriptions/models.py` e `portal/models.py`

### Como chegaríamos aos apps atuais

```powershell
cd backend
mkdir apps
New-Item apps\__init__.py
mkdir apps\accounts, apps\organizations, apps\work
python manage.py startapp accounts apps/accounts
python manage.py startapp organizations apps/organizations
python manage.py startapp work apps/work
```

O comando `startapp` aceita o diretório de destino, mas ele precisa existir; por isso criamos as pastas antes. `apps/__init__.py` torna o agrupador importável, e os apps entram em `INSTALLED_APPS`. Criaríamos finance, subscriptions, portal e core quando os respectivos casos de uso fossem iniciados, não no primeiro minuto.

### Como testar

Escreva primeiro testes simples de criação, unicidade e relações. Rode `makemigrations --check --dry-run` para entender se models e migrations estão sincronizados.

### Checkpoint

Você deve conseguir desenhar as relações 1:N e N:N sem olhar os models e justificar onde o tenant aparece.

## Etapa 3. Configurar banco e construir o primeiro model

### Objetivo

Persistir `User`, `Organization` e membership no PostgreSQL.

### Código importante

Uma versão mínima conceitual de organização começaria assim:

```python
class Organization(models.Model):
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
```

Primeiro garantimos que a entidade existe. Depois adicionamos slug, timestamps, constraints e relações. Isso é evolução controlada, não código incompleto esquecido.

### Ciclo de migration na prática

```text
alterar models.py
→ python manage.py makemigrations
→ revisar apps/.../migrations/000x_*.py
→ python manage.py migrate
→ esquema do banco é atualizado
```

`makemigrations` descreve a mudança; `migrate` a aplica. Em produção, faça backup e revise operações potencialmente destrutivas.

### Por que model primeiro

Serializer, view e frontend precisam saber qual dado existe. Para projetos, a ordem natural é:

```text
Project model
→ migration
→ serializer
→ permission/queryset
→ view
→ URL
→ service frontend
→ página
```

### Como testar

Crie objetos no teste Django e valide constraints, exclusões e isolamento. Não use manualmente o banco de produção.

### Checkpoint

O banco de desenvolvimento deve migrar do zero, e um teste deve criar organização e membership OWNER.

## Etapa 4. Construir uma API vertical de projetos

### Objetivo

Entregar uma funcionalidade pequena de ponta a ponta no backend: listar e criar projetos.

### Arquivos envolvidos

- `backend/apps/work/models.py`: `Project`.
- `backend/apps/work/serializers.py`: `ProjectSerializer`.
- `backend/apps/work/views.py`: `ProjectViewSet`.
- `backend/apps/work/urls.py`: registro no router.
- `backend/config/urls.py`: prefixo `/api/`.

### Evolução

**Versão 1:** model e serializer expõem campos essenciais.

```python
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "name", "status")
```

**Versão 2:** ViewSet permite GET/POST.

**Versão 3:** queryset filtra a organização atual.

**Versão 4:** permissions diferenciam leitura e gerenciamento.

**Versão 5:** serializer valida cliente do mesmo tenant e campos derivados ficam read-only.

### Por que não começar com um ViewSet irrestrito

Porque um CRUD que funciona, mas vaza dados, é pior que um endpoint ainda não publicado. Multi-tenancy entra no primeiro endpoint, não em uma “fase futura de segurança”.

### Como testar

Teste GET vazio, POST válido, dados inválidos, MEMBER proibido, acesso cruzado e alteração de `X-Organization-ID`. Só avance quando IDs externos retornarem 404/403 conforme o contrato.

### Resultado esperado

`GET /api/projects/` entrega apenas projetos permitidos e `POST` respeita papel e plano.

### Checkpoint

Você deve demonstrar a API com um cliente HTTP sem depender do React.

## Etapa 5. Construir autenticação gradualmente

### Objetivo

Identificar o usuário com segurança e proteger a API.

### Ordem de implementação

1. criar o model `User` antes da primeira migration relevante;
2. usar email como identificador;
3. criar cadastro com `set_password`, nunca salvar texto puro;
4. aplicar validadores de senha;
5. criar login com serializer;
6. emitir access e refresh SimpleJWT;
7. configurar tempos de vida;
8. proteger endpoints com `IsAuthenticated`;
9. implementar `/auth/me/`;
10. rotacionar e colocar refresh anterior na blacklist;
11. invalidar refresh no logout;
12. implementar reset com token de uso controlado.

### Como está implementado atualmente

`backend/apps/accounts` contém views e serializers; `settings.py` define access de 15 minutos, refresh de sete dias, rotação e blacklist.

### Como chegaríamos até essa implementação do zero

Primeiro teste cadastro e login no backend. Só então crie `AuthContext`. No frontend, evolua em quatro versões:

```text
V1: formulário chama POST /auth/login/
V2: tokens são persistidos e /auth/me/ restaura sessão
V3: interceptor adiciona Authorization
V4: 401 renova access uma vez; logout limpa tudo
```

### Como testar

Teste senha inválida, email duplicado, token expirado, rotação, replay de refresh, logout e endpoint protegido. No frontend, simule rede offline no logout e renovação depois de 401.

### Checkpoint

Uma pessoa anônima não acessa projetos; uma sessão válida recarrega a página sem perder identidade; logout encerra acesso local.

## Etapa 6. Construir o esqueleto React

### Objetivo

Montar uma SPA navegável antes de preencher páginas complexas.

### Ordem dos arquivos

1. `frontend/index.html`: criar `#root`.
2. `frontend/src/main.tsx`: montar React.
3. `frontend/src/App.tsx`: declarar rotas.
4. `frontend/src/components/ui.tsx`: primitivas pequenas.
5. `frontend/src/layouts/AppLayout.tsx`: moldura autenticada.
6. `frontend/src/pages/*`: páginas progressivas.

### Construindo `main.tsx`

Comece pequeno:

```tsx
createRoot(document.getElementById("root")!).render(<App />);
```

Confirme a renderização. Depois adicione, um por vez, `BrowserRouter`, Query Client, autenticação, idioma/toast e `ErrorBoundary`. Se tudo for adicionado de uma vez, um erro de provider fica difícil de isolar.

### Construindo `AppLayout`

**Versão 1:** estrutura sem comportamento.

```tsx
function AppLayout() {
  return (
    <div className="shell">
      <aside />
      <main>
        <Outlet />
      </main>
    </div>
  );
}
```

**Versão 2:** links com `NavLink`.

**Versão 3:** estado do menu mobile.

```tsx
const [open, setOpen] = useState(false);
```

**Versão 4:** descoberta de workspace e links por papel.

**Versão 5:** notificações, perfil e estados loading/error.

### Por que layout antes das páginas

Porque navegação e área de conteúdo são compartilhadas. Páginas passam a focar no seu caso de uso, sem copiar sidebar e topbar.

### Como saber se deu certo

Abra duas rotas, confirme que o layout permanece, teste `NavLink`, reduza para 650px e abra/feche o menu.

### Checkpoint

Você deve criar uma página vazia, registrá-la em `App.tsx` e vê-la dentro do `Outlet`.

## Etapa 7. CSS, responsividade e tema na ordem certa

### Objetivo

Construir um sistema visual sustentável, não uma sequência de correções locais.

### Ordem recomendada

1. normalização (`box-sizing`, body e elementos básicos);
2. tipografia;
3. tokens de cor, borda, raio e espaçamento;
4. superfícies da aplicação;
5. layout principal;
6. componentes reutilizáveis;
7. páginas;
8. estados hover/focus/disabled/error;
9. breakpoints;
10. tema escuro e `system`;
11. revisão de contraste e teclado.

### Por que tokens vêm antes

Se cada card escrever sua própria cor, dark mode exige caçar dezenas de valores. Com `--app-surface`, uma troca coerente afeta todos os consumidores.

### Construindo tema

1. defina tokens claros em `:root`;
2. substitua-os em `[data-theme='dark']`;
3. crie o valor `system` com `prefers-color-scheme`;
4. salve a preferência no perfil backend;
5. aplique `data-theme` no `<html>`;
6. mantenha locale/timezone no armazenamento para formatadores;
7. teste reload e os três modos.

Neste projeto não há botão global isolado em um `ThemeContext`; a escolha está em Preferências e é aplicada pelo `I18nProvider`. Ao reconstruir, preserve essa fonte única em vez de criar dois estados concorrentes.

### Construindo responsividade

Comece validando desktop, depois tablet e mobile:

```text
auth desktop: institucional | formulário
tablet: colunas e paddings menores
mobile: formulário ocupa a largura útil
```

Use uma media query apenas quando o conteúdo realmente deixa de caber. Teste 1100, 1000, 800 e 650px, além de valores entre eles.

### Checkpoint

Claro, escuro e system devem distinguir fundo, painel, card e inputs; teclado deve mostrar foco; nenhuma página deve produzir rolagem horizontal acidental, exceto o Kanban projetado para isso.

# Ligando frontend e backend

## Etapa 8. Criar a primeira request real

### Objetivo

Buscar projetos e transformar JSON em interface com loading, erro e sucesso.

### Passo a passo

**1. Backend funciona sozinho**

Confirme `GET /api/projects/` autenticado.

**2. Configure a origem**

`VITE_API_URL` aponta para a API; no desenvolvimento, o proxy Vite permite usar `/api`.

**3. Crie o cliente**

```ts
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api",
});
```

**4. Crie o service tipado**

```ts
list: () =>
  api.get<PaginatedResponse<Project>>("/projects/").then((r) => r.data);
```

**5. Encapsule em hook**

`useProjects` usa `useQuery`, escolhe uma query key e chama `projectService.list`.

**6. Renderize estados**

```text
isPending → LoadingState
isError   → ErrorState
lista vazia → EmptyState
data → projects.map(project => <ProjectCard ... />)
```

**7. Acrescente sessão e tenant**

Interceptors adicionam Bearer e `X-Organization-ID`; endpoints livres são excluídos explicitamente.

### Por que service + hook + página

O service pode ser usado/testado sem React. O hook coordena cache. A página decide aparência. Essa separação só vale porque cada camada tem responsabilidade diferente.

### Como testar

Simule 200, 401, 403, 500 e lista vazia. Confirme a URL real na aba Network, sem expor tokens em logs.

### Checkpoint

O backend pode parar e a página mostra erro controlado; ao voltar, a query pode ser refeita sem recarregar toda a SPA.

## Etapa 9. Crescer por fatias verticais

Depois da primeira request, repita o padrão, uma funcionalidade por vez:

```text
Clientes
→ Projetos e ProjectMember
→ Tarefas/Kanban
→ comentários/anexos
→ horas
→ receitas/despesas
→ faturas
→ portal do cliente
→ notificações
→ assinatura
```

Para cada fatia:

1. escreva regra e permission;
2. modele dados;
3. crie migration;
4. escreva teste backend;
5. publique serializer/view/URL;
6. crie tipos e service frontend;
7. crie hook e interface;
8. teste loading, vazio, erro e sucesso;
9. rode a suíte anterior.

### Exemplo: evolução de tarefas

V1 cria `Task` com título, projeto e status. V2 adiciona responsáveis por tabela intermediária. V3 adiciona labels N:N. V4 adiciona movimento/posição. V5 adiciona comentários/anexos privados. V6 registra atividades. Cada versão continua testável.

### Checkpoint

Uma fatia só está pronta quando segurança, API, interface, estados e testes concordam sobre o mesmo comportamento.

## Etapa 10. Adicionar processos assíncronos e tempo real

### Por que não começar por Redis

Redis resolve comunicação entre processos; ele não deve ser adicionado apenas por moda. Primeiro persista notificações no PostgreSQL e ofereça GET. Depois adicione polling. Só então WebSocket melhora latência, e Celery tira tarefas demoradas da resposta HTTP.

### Construção gradual

```text
Notification model + endpoint
→ polling frontend
→ Celery envia email
→ Redis como broker
→ ASGI + Consumer
→ middleware JWT do socket
→ group user_<id>
→ frontend invalida cache ao receber evento
```

Celery Beat entra apenas quando existem tarefas periódicas reais, como lembretes e cobranças agendadas.

### Como testar

Teste consumidor com JWT válido/inválido, isolamento por grupo, fallback sem Redis e idempotência das tarefas. Derrube o socket e confirme que polling continua funcionando.

### Checkpoint

Perder Redis não pode apagar notificações persistidas nem inventar sucesso de envio.

## Etapa 11. Integrar pagamentos por último

### Por que depois do financeiro interno

Antes de chamar um provedor, Invoice, itens, total, vencimento e estados precisam funcionar localmente. O provedor é uma integração técnica, não o dono da regra de negócio.

### Construção segura

1. modele `Invoice` e `InvoiceItem` com Decimal;
2. calcule total no backend;
3. teste criação e RBAC sem Mercado Pago;
4. crie uma interface de provider;
5. implemente Mercado Pago no backend;
6. grave cada tentativa em `InvoicePayment`;
7. gere UUID público restrito;
8. crie página pública somente leitura;
9. valide assinatura HMAC do webhook;
10. consulte o recurso no provedor;
11. confira referência, BRL e valor;
12. aplique idempotência antes de criar Revenue.

### Como testar

Use mocks. Nunca gere Pix real na suíte. Teste webhook repetido, valor divergente, assinatura inválida, pagamento desconhecido e expiração.

### Checkpoint

Retorno do navegador e polling nunca ativam pagamento ou Pro. Apenas confirmação backend confiável altera o estado.

## Etapa 12. Dockerizar quando o projeto já roda localmente

### Objetivo

Padronizar ambiente depois de entender como cada processo funciona fora de containers.

### Construindo o Dockerfile backend

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
```

- sem `FROM`, não há sistema/base Python;
- sem `WORKDIR`, caminhos ficam ambíguos;
- copiar requirements antes aproveita cache;
- sem `RUN`, dependências não existem;
- sem código copiado, não há aplicação;
- sem `CMD`, container não sabe qual processo iniciar.

Depois endureça produção com usuário não-root, ownership, diretórios de static/media e imagem slim, como no arquivo atual.

### Compose gradual

1. comece com `db` e volume;
2. adicione backend com `DB_HOST=db`;
3. adicione Redis e `REDIS_URL=redis://redis:6379/0`;
4. adicione worker e beat usando a mesma imagem backend;
5. adicione frontend;
6. adicione healthchecks e dependências;
7. crie compose de produção com Nginx e volumes persistentes.

Dentro da rede Compose, `postgres`/`db` e `redis` são DNS de serviços. `localhost` dentro do container aponta para o próprio container, não para o computador nem para outro serviço.

### Como testar

```powershell
docker compose build
docker compose up
docker compose ps
docker compose logs backend
```

Abra frontend, `/health/` e `/health/ready/`; crie dados temporários e confirme persistência após reiniciar containers.

### Checkpoint

O projeto deve funcionar tanto segundo o modo local documentado quanto no Compose, sem trocar URLs dentro do código.

## Etapa 13. Testar durante toda a construção

Não deixe testes para o fim. Use uma pirâmide prática:

```text
muitos testes rápidos de regra/serializer/helper
→ testes de API e componentes
→ poucos fluxos integrados
→ smoke somente leitura em deployment
```

Após cada model, teste constraint. Após cada endpoint, teste sucesso, validação e permission. Após cada componente, teste o comportamento visível. Após cada integração, teste falha do serviço externo. Antes de integrar uma fatia, rode lint, check, migrations e testes anteriores.

Um fluxo de trabalho possível:

```text
escrever teste que descreve a regra
→ ver falhar pela razão correta
→ implementar o mínimo
→ ver passar
→ refatorar sem mudar comportamento
→ rodar suíte completa
```

### Como chegaríamos à estrutura atual

1. comece com um teste Django do primeiro model e endpoint;
2. adicione Vitest/jsdom ao nascer o primeiro helper ou componente interativo;
3. use Testing Library para comportamento visível, não detalhes internos;
4. crie mocks somente nas fronteiras de rede/provedor;
5. adicione contratos transversais quando frontend e backend passam a evoluir separadamente;
6. configure coverage e registre uma linha de base honesta;
7. crie `tests/run_all.py` quando repetir manualmente todos os comandos se tornar propenso a erro;
8. leve os mesmos gates para `.github/workflows/ci.yml`;
9. publique relatórios como artefatos e aumente thresholds progressivamente.

### Primeiro workflow conceitual

Comece pequeno, com checkout, setup da linguagem, instalação e testes. Depois separe jobs porque backend, frontend e Docker possuem dependências diferentes:

```text
backend: PostgreSQL/Redis → Ruff/check/migrations → Django/coverage → audit
frontend: npm ci → ESLint → Vitest/coverage → build → audit
transversal: unittest discover
docker: compose build
```

Não use CI para esconder um comando que não funciona localmente. Primeiro documente e valide o comando na máquina; depois automatize-o em um checkout limpo.

### Checkpoint

A CI deve reconstruir o ambiente a partir do repositório limpo e falhar se cobertura, migrations, lint, build ou testes regredirem.

## Etapa 14. Preparar e publicar em produção

### Objetivo

Transformar o ambiente de desenvolvimento em uma entrega reproduzível e segura.

### Mudanças reais de contexto

| Desenvolvimento                | Produção                                           |
| ------------------------------ | -------------------------------------------------- |
| `DEBUG=True`                   | `DEBUG=False`                                      |
| localhost                      | domínio HTTPS                                      |
| Vite dev/HMR                   | bundle `dist` servido por Nginx/CDN                |
| HTTP/`ws://` local             | HTTPS/`wss://` quando WebSocket existir            |
| console email                  | SMTP configurado                                   |
| fallbacks em memória possíveis | PostgreSQL/Redis compartilhados conforme topologia |
| secrets no `.env` local        | secret manager ou `.env.production` fora do Git    |

### Caminho Git

```text
git status
→ revisar git diff
→ git add somente arquivos desejados
→ git commit com mudança coerente
→ git push
→ CI instala e valida
→ plataforma constrói
→ variáveis são injetadas
→ migrations controladas
→ deploy
→ health/readiness/smoke
```

Na VPS, use `docker-compose.prod.yml`, DNS, TLS, backups e Nginx. Na arquitetura Vercel documentada, configure frontend/backend separados, rewrite SPA e origens exatas. Não foi possível confirmar qual caminho é o único ativo; valide a infraestrutura antes de publicar.

### Como saber se deu certo

Health retorna 200, readiness confirma dependências, rotas diretas da SPA abrem, CORS aceita apenas o frontend, login/refresh funcionam e logs não expõem secrets.

### Checkpoint

Você deve conseguir fazer rollback e restaurar backup antes de considerar produção pronta.

# Como investigar quando algo dá errado

Debug não é “tentar mudanças até funcionar”. Use um funil:

```text
observar sintoma
→ copiar mensagem/status sem secrets
→ reproduzir de forma mínima
→ decidir frontend, rede, backend, banco ou serviço externo
→ verificar logs e aba Network
→ formular hipótese
→ mudar uma variável
→ repetir teste
→ adicionar teste de regressão
```

### Isolando as camadas

- Se `npm run build` falha, resolva TypeScript/import antes de investigar Django.
- Se página abre e request falha, examine URL, método, payload, status e headers.
- Se API falha no cliente e no teste direto, investigue URL/view/serializer/permission.
- Se só um tenant falha, verifique membership e `X-Organization-ID`.
- Se tarefa assíncrona falha, teste a função de domínio diretamente antes de Redis/Celery.
- Se pagamento falha, preserve IDs técnicos, use ambiente sandbox e nunca “force” status pago no banco.

### Problemas reais úteis para treino

- 401 seguido de refresh: observe se a request é repetida somente uma vez.
- 403 de billing para MEMBER: é regra, não indisponibilidade.
- 404 entre tenants: pode ser proteção contra enumeração.
- `redis:6379` fora do Docker: hostname incorreto para processo local.
- rota SPA 404 no refresh: rewrite de `vercel.json`/Nginx ausente.
- tela desatualizada após mutation: query key não invalidada.

## Decisões que guiam a reconstrução

| Decisão              | Por que faz sentido no DevFlow                                 |
| -------------------- | -------------------------------------------------------------- |
| Componente           | reutiliza aparência/comportamento como cards e inputs          |
| Hook customizado     | reúne Query, mutation e invalidação de um domínio              |
| Service              | isola detalhes HTTP da interface                               |
| Context              | compartilha sessão, idioma e toast por toda a árvore           |
| API                  | permite frontend e tarefas externas consumirem regras centrais |
| Banco                | preserva relações e transações entre acessos/processos         |
| Redis                | coordena processos e reduz latência; não substitui PostgreSQL  |
| Docker               | torna dependências e execução reproduzíveis                    |
| Variável de ambiente | separa configuração/segredo do código                          |
| Build                | converte TypeScript/JSX e otimiza assets para navegador        |

# Desafio: reconstruir o projeto

Não copie arquivos inteiros. Use os contratos e checkpoints.

### Fase 1 — Fundação

Crie repositório, venv, Django, Vite React TypeScript, checks e Git ignore.

### Fase 2 — Identidade e tenant

Modele User, Organization e Membership. Implemente cadastro, login JWT e criação atômica do workspace.

### Fase 3 — Primeira fatia vertical

Crie Client e Project do model ao card React, incluindo isolamento e estados visuais.

### Fase 4 — Gestão do trabalho

Adicione ProjectMember, Task, responsáveis, labels e Kanban incrementalmente.

### Fase 5 — Operação

Implemente horas, financeiro e relatórios antes de qualquer provedor de pagamento.

### Fase 6 — Clientes e comunicação

Crie acesso separado do cliente, entregas e notificações persistidas; depois polling, Celery e WebSocket.

### Fase 7 — Billing

Implemente política Free/Pro e faturas; integre Mercado Pago com sandbox, webhook e idempotência.

### Fase 8 — Qualidade e entrega

Complete testes, cobertura, CI, Docker local, produção, health/readiness, backups e smoke.

### Critério final

Feche o projeto original e explique: qual é a próxima entidade, qual regra precisa de teste, qual endpoint nasce dela, qual componente a consome e como provar isolamento.

# Ordem recomendada para estudar este projeto

1. Leia a visão geral e desenhe o mapa navegador → banco.
2. Estude `index.html`, `main.tsx` e módulos TypeScript.
3. Estude componentes, props, estado, eventos e CSS.
4. Estude `App.tsx`, Router e `AppLayout`.
5. Estude Context, autenticação e formulários.
6. Estude types, services, hooks e TanStack Query.
7. Estude settings, URLs, views e serializers Django.
8. Estude models, relações, migrations e PostgreSQL.
9. Estude multi-tenancy, RBAC e segurança.
10. Acompanhe uma fatia completa: Projects.
11. Acompanhe tarefas, horas e financeiro.
12. Estude portal, notificações, Redis, Celery e WebSocket.
13. Estude pagamentos e idempotência.
14. Estude Docker, ambientes, build e deploy.
15. Execute testes e tente o desafio de reconstrução.

## Glossário

| Termo              | Significado no DevFlow                                                               |
| ------------------ | ------------------------------------------------------------------------------------ |
| API                | contrato HTTP publicado pelo Django para frontend e integrações                      |
| REST               | organização da API em recursos, URLs, métodos e representações JSON                  |
| HTTP               | protocolo de request/response usado pelas páginas para operações comuns              |
| WebSocket          | conexão persistente usada para avisar notificações em tempo real                     |
| JWT                | token assinado que identifica a sessão; access é curto e refresh renova              |
| header             | metadado HTTP; `Authorization` leva JWT e `X-Organization-ID` seleciona tenant       |
| CORS               | política do navegador que limita quais origens podem chamar a API                    |
| CSRF               | ataque de requisição forjada; origens confiáveis e configuração Django reduzem risco |
| ORM                | API Python do Django que traduz models/querysets em SQL                              |
| model              | classe que descreve entidade, campos, relações e constraints persistentes            |
| QuerySet           | consulta preguiçosa e combinável do ORM; é a principal fronteira de isolamento       |
| migration          | arquivo versionado que transforma o esquema do banco                                 |
| serializer         | valida JSON, converte tipos e representa models na resposta                          |
| view/ViewSet       | ponto que recebe request, aplica caso de uso e devolve Response                      |
| permission         | regra DRF que autoriza a operação antes ou durante acesso ao objeto                  |
| middleware         | camada ao redor da request; request ID e autenticação WS são exemplos distintos      |
| tenant             | organização cujos dados devem permanecer isolados das demais                         |
| membership         | vínculo User–Organization com papel, atividade e aprovação                           |
| RBAC               | autorização baseada em papéis como OWNER, ADMIN, MEMBER e CLIENT                     |
| IDOR               | acesso indevido ao trocar IDs; querysets filtrados impedem enumeração entre tenants  |
| component          | função React que produz interface a partir de props, estado e contexts               |
| prop               | entrada tipada enviada pelo componente pai                                           |
| state              | valor mutável do componente que provoca nova renderização                            |
| hook               | função React; hooks customizados do projeto encapsulam queries e mutations           |
| context            | valor compartilhado pela árvore, usado para auth, idioma e toasts                    |
| query/mutation     | leitura em cache / alteração de dados no TanStack Query                              |
| interceptor        | função Axios que acrescenta headers ou trata 401 antes/depois da request             |
| HMR                | atualização de módulos pelo Vite durante desenvolvimento sem reload completo         |
| build              | checagem TypeScript e geração otimizada do `dist` frontend                           |
| PostgreSQL         | banco relacional e fonte de verdade persistente                                      |
| Redis              | armazenamento em memória usado como cache, broker e channel layer compartilhado      |
| Celery             | executor de tarefas assíncronas; worker consome e beat agenda                        |
| broker             | transporte de mensagens entre Django/beat e workers Celery                           |
| channel layer      | transporte de eventos entre processos Channels e grupos WebSocket                    |
| idempotência       | repetir evento/operação sem duplicar efeito; essencial em webhooks e pagamentos      |
| webhook            | request enviada pelo Mercado Pago para informar alteração externa                    |
| image/container    | molde imutável / processo isolado criado a partir desse molde no Docker              |
| volume             | armazenamento Docker que sobrevive à recriação do container                          |
| CI                 | validações automáticas do GitHub Actions a cada push/PR configurado                  |
| deploy             | publicação do build e serviços com configuração de produção                          |
| liveness/readiness | processo está vivo / está pronto para atender com dependências disponíveis           |

## Perguntas da trilha de construção

1. Por que modelar tenant antes do primeiro CRUD?
2. Em qual momento Redis passa a resolver um problema real?
3. Por que uma interface de pagamento deve vir depois da fatura interna?
4. Qual vantagem há em provar o endpoint antes de criar a página?
5. Por que providers devem ser adicionados gradualmente?
6. O que caracteriza uma fatia vertical pronta?
7. Qual é a diferença entre migration gerada e migration aplicada?
8. Por que `localhost` não aponta para outro container?

## Gabarito da trilha de construção

1. Porque tenant faz parte da identidade e de todo queryset; adicioná-lo depois cria risco de vazamento.
2. Quando há filas, cache compartilhado ou eventos entre múltiplos processos.
3. Para que regras, valores e estados existam independentemente do provedor externo.
4. Separa erro da API de erro de React e estabiliza o contrato.
5. Facilita localizar qual contexto introduziu uma falha e evita complexidade precoce.
6. Regra, persistência, API, segurança, interface, estados e testes concordam.
7. A gerada descreve operações em arquivo; a aplicada modifica o esquema do banco.
8. Cada container possui sua própria interface de rede; serviços usam DNS do Compose.

## Gabarito das perguntas de revisão

### Visão geral

1. O backend Django, por meio de permissions, querysets e regras de domínio.
2. Página → hook → service Axios → URL/view → serializer → model → banco.
3. Várias organizações usam o sistema com isolamento de dados e autorização por membership.

### Rotas

1. Para não redirecionar enquanto a sessão ainda está sendo restaurada.
2. Renderizar a rota filha dentro do layout pai.
3. A pública não exige sessão; `ProtectedPage` exige e preserva a URL de retorno.

### Componentes e dados

1. `ProjectDetail`, em `frontend/src/pages/Projects.tsx`.
2. Services conhecem HTTP; hooks conhecem cache, estados e invalidação da interface.
3. Atualizações de estado depois que o componente já desmontou ou mudou de rota.

### Testes

1. Segurança precisa ser garantida no servidor, que recebe clientes potencialmente maliciosos.
2. Smoke consulta um deployment real de forma segura; Django cria um ambiente controlado e pode testar escrita.
3. Cobertura mede código executado, não todas as combinações, requisitos ou assertivas corretas.

## Checklist de domínio do projeto

Ao concluir o estudo, verifique se consegue explicar sem consultar o guia:

- como HTML, `main.tsx`, providers e router se conectam;
- diferença entre prop, state, hook, context, query e mutation;
- como tema, idioma e timezone chegam ao documento;
- como access/refresh funcionam e onde ficam;
- por que `X-Organization-ID` não é autorização;
- como models, serializers, views e URLs colaboram;
- relações entre organização, projeto, tarefa, fatura e portal;
- diferença entre HTTP, WebSocket, Celery e Redis;
- como Docker local difere da produção;
- como build, deploy, Git, testes e CI protegem a entrega.

- FIM
