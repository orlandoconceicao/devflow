# Arquitetura do DevFlow

## Visão geral

O frontend React/TypeScript consome uma API Django REST Framework. PostgreSQL mantém o estado transacional; Redis atende Celery, cache/readiness e Channels. Daphne executa HTTP e WebSocket pelo mesmo ASGI.

## Multi-tenancy e RBAC

Toda entidade de negócio carrega ou deriva `organization`. O header `X-Organization-ID` apenas seleciona um workspace: o backend sempre valida `OrganizationMembership`. OWNER, ADMIN, MEMBER e CLIENT recebem políticas diferentes; consultas são filtradas antes da resolução do objeto para reduzir IDOR.

## Billing

O preço Pro de R$ 25/mês é definido pelo backend e enviado à API de preapproval do Mercado Pago. O retorno do navegador não ativa recursos: somente webhooks HMAC validados, seguidos de consulta autenticada do recurso, atualizam a assinatura. `PaymentEvent.provider_event_id` garante idempotência e o pagamento exige R$ 25 em BRL.

## Assíncrono e tempo real

Celery envia emails e processa lembretes idempotentes. Redis é broker/result backend. Notifications persistem no PostgreSQL e são também publicadas somente ao grupo `user_<id>` autenticado por JWT; a API é o fallback confiável.

## Operação

`/health/` verifica o processo e `/health/ready/` verifica PostgreSQL e Redis. Produção usa Daphne, containers não-root, Nginx com HTTPS/WebSocket e volumes persistentes. Upload em volume local serve uma VPS única; crescimento horizontal requer storage S3/R2.
