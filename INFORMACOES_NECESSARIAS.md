# DevFlow — informações necessárias do proprietário

Este documento reúne somente informações que dependem do proprietário do DevFlow. Não coloque senhas, tokens ou dados bancários diretamente neste arquivo se ele for enviado ao GitHub.

## 1. Dados pessoais e comerciais

- [x] Nome do responsável: **Orlando Conceição**
- [x] Email de suporte: **orlandoconceicao94@gmail.com**
- [x] Nome exibido nos emails: **Orlando Conceição**
- [ ] Nome comercial que aparecerá para os clientes: `PENDENTE`
- [ ] Email público de pagamentos: `PENDENTE — confirmar se será o email de suporte`
- [ ] Telefone público de suporte: `PENDENTE — opcional`
- [ ] CPF ou CNPJ usado na conta empresarial: `PENDENTE — não colocar no GitHub`
- [ ] Razão social ou nome completo do recebedor: `PENDENTE`
- [ ] Endereço comercial exigido pelos documentos legais: `PENDENTE`

## 2. Produto e cobrança

- [x] Nome do produto: **DevFlow Pro**
- [x] Preço previsto: **R$ 25,00 por mês**
- [ ] Período gratuito ou teste grátis: `PENDENTE — decidir`
- [ ] Política de cancelamento: `PENDENTE — definir`
- [ ] Política de reembolso: `PENDENTE — definir`
- [ ] Texto que aparecerá na cobrança/fatura: `PENDENTE`

## 3. Mercado Pago

O backend centraliza no Mercado Pago as assinaturas, cobranças Pix e validação de webhook.

### Decisões necessárias

- [ ] Tipo de cobrança: **assinatura recorrente mensal** ou pagamento avulso.
- [ ] Ambiente inicial: **teste/sandbox** ou produção.
- [ ] A aplicação DevFlow já foi criada no Mercado Pago? `SIM/NÃO`
- [ ] A conta está habilitada para Pix e assinaturas recorrentes? `SIM/NÃO`
- [ ] URL para retornar após a autorização: `PENDENTE — depende do domínio`
- [ ] URL pública do webhook: `PENDENTE — depende da API em produção`

### Credenciais necessárias

Obtenha no painel de desenvolvedores do Mercado Pago:

- [ ] Public Key de teste.
- [ ] Access Token de teste.
- [ ] Segredo do webhook de teste.
- [ ] Public Key de produção.
- [ ] Access Token de produção.
- [ ] Segredo do webhook de produção.

Esses valores devem ser colocados somente no `.env` local ou no gerenciador de segredos do servidor:

```env
MERCADO_PAGO_ENVIRONMENT=test
MERCADO_PAGO_PUBLIC_KEY=
MERCADO_PAGO_ACCESS_TOKEN=
MERCADO_PAGO_WEBHOOK_SECRET=
MERCADO_PAGO_BASE_URL=https://api.mercadopago.com
```

Não enviar chave secreta ou segredo do webhook por captura de tela, documento público ou commit no GitHub.

### Webhook a configurar

Quando a integração estiver implementada e a API tiver endereço público HTTPS, o endereço previsto será semelhante a:

```text
https://api.seudominio.com/api/webhooks/mercado-pago/
```

Eventos necessários:

- pagamentos;
- atualizações de assinatura (`subscription_preapproval`);
- pagamentos recorrentes (`subscription_authorized_payment`).

## 4. Domínio e deploy

- [ ] Domínio principal: `PENDENTE`
- [ ] URL pública do frontend: `PENDENTE — exemplo: https://app.seudominio.com`
- [ ] URL pública da API: `PENDENTE — exemplo: https://api.seudominio.com`
- [ ] Provedor do deploy: `PENDENTE`
- [ ] Deploy será em VPS, Render, Railway, Fly.io ou outro: `PENDENTE`
- [ ] Conta/projeto do provedor já criado: `SIM/NÃO`
- [ ] HTTPS/SSL configurado: `SIM/NÃO`
- [ ] Serviço de email transacional escolhido: `PENDENTE`
- [ ] Email/domínio remetente verificado: `PENDENTE`

## 5. Banco de dados de produção

- [x] Nome desejado do banco: **devflow**
- [x] Usuário desejado: **devflow_user**
- [ ] Provedor PostgreSQL: `PENDENTE`
- [ ] Host privado: `PENDENTE — guardar no ambiente de produção`
- [ ] Porta: `PENDENTE — normalmente 5432`
- [ ] Senha exclusiva de produção: `PENDENTE — gerar e guardar como segredo`
- [ ] Frequência de backup: `PENDENTE`
- [ ] Retenção dos backups: `PENDENTE`
- [ ] Teste de restauração realizado: `SIM/NÃO`

Não reutilize a senha do banco local em produção.

## 6. Documentos e páginas públicas

- [ ] Termos de Uso.
- [ ] Política de Privacidade.
- [ ] Política de Cancelamento e Reembolso.
- [ ] Canal de atendimento ao cliente.
- [ ] Nome/CPF ou razão social/CNPJ exigidos no rodapé e documentos.

## 7. O que você precisa enviar para continuar

Para desenvolver e testar primeiro no ambiente local:

1. Confirmar que deseja **assinatura recorrente mensal de R$ 25,00**.
2. Informar se a conta Mercado Pago está criada e habilitada para Pix e assinaturas.
3. Criar o produto **DevFlow Pro** no modo de teste.
4. Criar o preço recorrente mensal de R$ 25,00 e informar apenas o `price_...`.
5. Configurar as credenciais de **teste** diretamente no `.env`; não colá-las neste arquivo.
6. Avisar quando as variáveis estiverem preenchidas para que a integração seja implementada e testada.

Para colocar em produção, também serão necessários domínio, provedor de deploy, PostgreSQL, HTTPS, credenciais de produção e webhook público.
