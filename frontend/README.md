# DevFlow Frontend

SPA do DevFlow para gestão de workspaces, clientes, projetos, tarefas, horas, finanças, equipe e portal do cliente.

- Produção: <https://devflow-frontend-delta.vercel.app>
- API: <https://devflow-backend-swart.vercel.app/api>
- Repositório: <https://github.com/orlandoconceicao/devflow>

## Tecnologias

- React 19, TypeScript e Vite 7;
- React Router 7, TanStack Query e Axios;
- React Hook Form, Zod e Lucide React;
- Vitest, Testing Library, ESLint e Prettier.

## Funcionalidades

- autenticação, recuperação de senha e onboarding;
- dashboard e seleção de workspace;
- clientes, projetos e atividades;
- tarefas em Kanban, comentários, labels e anexos;
- controle de horas, financeiro, cobranças e relatórios;
- gestão e convites de equipe, aprovação de membros e chat;
- notificações e preferências da conta;
- portal do cliente e entregas;
- assinatura e página pública de pagamento Pix;
- tema, idioma e timezone persistidos.

## Estrutura

```text
frontend/
├── src/
│   ├── components/       # componentes reutilizáveis e UI
│   ├── features/         # contexto e regras por domínio
│   ├── i18n/             # traduções
│   ├── layouts/          # layout autenticado
│   ├── pages/            # páginas e fluxos
│   ├── services/         # cliente HTTP e serviços da API
│   ├── test/             # configuração de testes
│   ├── types/            # tipos compartilhados
│   └── utils/            # utilitários
├── package.json
└── vercel.json           # fallback da SPA
```

As rotas públicas incluem login, cadastro, recuperação de senha, aceite de convite e pagamento em `/pagar/:token`. As áreas autenticadas incluem dashboard, clientes, projetos, tarefas, horas, financeiro, relatórios, equipe, notificações, portal e configurações.

## Instalação e execução local

Pré-requisitos: Node.js 22 e npm.

```bash
cd frontend
npm ci
npm run dev
```

A aplicação fica disponível em <http://localhost:5173>. O backend deve estar acessível pela URL configurada.

## Variáveis de ambiente

Crie `frontend/.env.local` quando precisar sobrescrever os valores locais:

```env
VITE_API_URL=http://localhost:8000/api
VITE_PROXY_TARGET=http://localhost:8000
```

- `VITE_API_URL`: base pública da API. No Compose, o padrão `/api` usa o proxy do Vite.
- `VITE_PROXY_TARGET`: destino do proxy durante o desenvolvimento.
- `VITE_WS_URL`: endpoint WebSocket opcional. Sem ele, notificações continuam por polling HTTP.

Somente variáveis prefixadas com `VITE_` são expostas ao bundle. Nunca coloque segredos ou credenciais do backend nessas variáveis.

## Scripts

```bash
npm run dev            # servidor de desenvolvimento
npm run build          # type-check e build de produção
npm run lint           # ESLint
npm test               # testes Vitest
npm run test:coverage  # testes com cobertura
npm run format         # aplica Prettier
npm run format:check   # valida formatação
```

## Deploy na Vercel

Crie um projeto Vercel com `frontend` como Root Directory. O framework é detectado como Vite.

Configure no ambiente Production:

```env
VITE_API_URL=https://devflow-backend-swart.vercel.app/api
```

O `vercel.json` preserva `/api` e direciona as demais URLs para `index.html`, permitindo abrir diretamente rotas do React Router. Depois de mudar uma variável `VITE_`, faça um novo deploy, pois os valores são incorporados durante o build.

## Integração com a API

O cliente Axios adiciona o JWT e o header `X-Organization-ID` quando a operação depende de um workspace. Respostas `401` passam pelo fluxo de renovação do token. As permissões exibidas na interface melhoram a experiência, mas toda autorização efetiva é aplicada pelo backend.
