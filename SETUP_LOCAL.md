# DevFlow — informações necessárias para rodar localmente

## Já definido

- Nome do remetente: Orlando Conceição
- Email de suporte e remetente: orlandoconceicao94@gmail.com
- Banco local: `devflow`
- Usuário local do banco: `devflow_user`

O telefone, a senha informada, documentos pessoais, dados bancários e chaves não ficam registrados neste arquivo nem no repositório.

## Ambiente local

Você precisa somente de Docker Desktop em execução. Copie o ambiente de exemplo e suba os containers:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Não é necessário domínio, banco de produção, deploy, Mercado Pago, SMTP real ou dados bancários para executar os módulos principais localmente.

## Backend local com Redis

O login e os demais endpoints passam pelo throttling do Django REST Framework,
cujo cache usa Redis. Para executar o backend diretamente no Windows, mantenha
`REDIS_URL=redis://localhost:6379/0` no `.env` e inicie primeiro os serviços:

```powershell
docker compose up -d db redis
docker compose ps redis
docker compose exec redis redis-cli ping
.\.venv\Scripts\Activate.ps1
Set-Location backend
python manage.py check
python manage.py migrate
python manage.py runserver
```

O `ping` deve responder `PONG` e o Redis deve aparecer como `healthy`. Para
encerrar as dependências, use `docker compose stop db redis`. Se todo o projeto
for executado em containers, use `docker compose up --build`; o Compose fornece
automaticamente `redis://redis:6379/0` ao backend e aos processos Celery.

## Recursos externos para integrações e produção

- Redis, Celery, notificações, portal e emails no console funcionam localmente. Pagamentos reais no ambiente de teste exigem uma conta Mercado Pago, `MERCADO_PAGO_ACCESS_TOKEN` e `MERCADO_PAGO_WEBHOOK_SECRET`.
- O ambiente de produção exige domínio, URLs públicas, servidor, PostgreSQL, política de backup e secrets configurados exclusivamente na plataforma de deploy.

Nunca coloque senhas, tokens, chave PIX, documentos ou chave SSH privada em arquivos versionados.

## Email e WhatsApp para cobranças

O email local usa o backend de console. Para entrega real pelo Gmail, altere
`EMAIL_BACKEND` para `django.core.mail.backends.smtp.EmailBackend`, configure
`EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`,
`EMAIL_HOST_USER=orlandoconceicao94@gmail.com` e forneça uma App Password somente
no `.env` local/secret do deploy.

O envio para telefone exige WhatsApp Cloud API real. Configure
`MESSAGE_PROVIDER=meta_whatsapp`, `WHATSAPP_API_URL` e `WHATSAPP_ACCESS_TOKEN`.
Sem provider, nenhuma mensagem é simulada ou apresentada como enviada.
