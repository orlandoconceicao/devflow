# DevFlow — informações necessárias para rodar localmente

## Já definido

- Nome do remetente: Orlando Conceição
- Email de suporte e remetente: orlandoconceicao94@gmail.com
- Banco local: `devflow`
- Usuário local do banco: `devflow_user`

O telefone, a senha informada, documentos pessoais, dados bancários e chaves não ficam registrados neste arquivo nem no repositório.

## Para rodar os Prompts 1 a 4 localmente

Você precisa somente de Docker Desktop em execução. Copie o ambiente de exemplo e suba os containers:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Não é necessário domínio, banco de produção, deploy, Stripe, SMTP real ou dados bancários para os Prompts 1 a 4.

## Ainda necessário nos próximos prompts

- Prompt 5: Redis, Celery, notificações, portal e emails no console funcionam localmente. Checkout real em sandbox exige uma conta Stripe de teste, `PAYMENT_API_KEY`, `PAYMENT_WEBHOOK_SECRET` e `STRIPE_PRO_PRICE_ID`.
- Prompt 6: domínio, URLs públicas, servidor, PostgreSQL de produção, backup e secrets apenas para deploy real.

Nunca coloque senhas, tokens, chave PIX, documentos ou chave SSH privada em arquivos versionados.
