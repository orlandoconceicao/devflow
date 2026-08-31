# Deploy em VPS

1. Configure DNS do domínio para o IP da VPS.
2. Instale Docker Engine e Compose Plugin.
3. Clone o repositório e crie `.env.production` fora do controle de versão.
4. Coloque certificados em `deploy/certs/fullchain.pem` e `privkey.pem` ou adapte Nginx para Certbot.
5. Execute `docker compose -f docker-compose.prod.yml up -d --build`.
6. Verifique `/health/` e `/health/ready/`.
7. Configure as credenciais Mercado Pago no gerenciador de segredos; teste e produção devem apontar o webhook HTTPS para `/api/webhooks/mercado-pago/`.

Backup diário sugerido: `pg_dump` criptografado, retenção de 7 diários e 4 semanais em local externo. Faça teste mensal de restauração. Redis não é fonte de verdade; volumes de media exigem backup ou migração para S3/R2.

Rollback: mantenha a imagem anterior, restaure-a e aplique somente migrations compatíveis. Faça backup antes de migrations destrutivas.

## Vercel

O deployment atual separa frontend e backend:

- frontend: `https://devflow-frontend-delta.vercel.app`;
- backend: `https://devflow-backend-swart.vercel.app`;
- API: `https://devflow-backend-swart.vercel.app/api`.

Configure `VITE_API_URL` somente no frontend, apontando para a API acima. No
backend, configure `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS` e
`CSRF_TRUSTED_ORIGINS` com a origem exata do frontend. O CORS estende os headers
padrão com `x-organization-id`; não habilite `CORS_ALLOW_ALL_ORIGINS`.

`frontend/vercel.json` mantém o fallback SPA para `index.html`. Não transforme
esse fallback em proxy de API. URLs como `/dashboard` e `/settings/billing`
devem chegar ao React Router ao serem abertas diretamente.

Redis não é obrigatório na Vercel. Com `REDIS_URL` vazio, o backend usa os
fallbacks em memória definidos em `settings.py`. WebSocket só deve ser ativado
no frontend quando `VITE_WS_URL` apontar explicitamente para infraestrutura
compatível; caso contrário, notificações usam polling HTTP.
