# Apresentação

## Versão curta

Desenvolvi o DevFlow, uma plataforma SaaS multi-tenant para gestão de clientes, projetos, tarefas, horas e faturamento, usando Django REST Framework, React/TypeScript, PostgreSQL, Redis, Celery, WebSockets, RBAC, Mercado Pago e Docker.

## Versão detalhada

O projeto demonstra desenho de APIs seguras, isolamento multi-tenant, autorização por papéis, Kanban persistente, controle financeiro com valores decimais, portal de aprovação para clientes, processamento assíncrono e notificações em tempo real. O fluxo de assinatura não confia no frontend: checkout e webhooks são validados no backend com idempotência. A entrega inclui CI, health checks, containers de produção e documentação operacional.

Topics sugeridos: `python`, `django`, `django-rest-framework`, `react`, `typescript`, `postgresql`, `redis`, `celery`, `docker`, `saas`, `kanban`, `websocket`.
