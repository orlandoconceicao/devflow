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

## 3. Stripe

O backend já possui integração com Stripe para checkout, portal de cobrança, assinatura e validação de webhook.

### Decisões necessárias

- [ ] Tipo de cobrança: **assinatura recorrente mensal** ou pagamento avulso.
- [ ] Ambiente inicial: **teste/sandbox** ou produção.
- [ ] O produto **DevFlow Pro** já foi criado no Stripe? `SIM/NÃO`
- [ ] O preço recorrente mensal de **R$ 25,00** já foi criado? `SIM/NÃO`
- [ ] Price ID do preço recorrente, normalmente iniciado por `price_`: `PENDENTE`
- [ ] URL para retornar após pagamento aprovado: `PENDENTE — depende do domínio`
- [ ] URL para retornar após pagamento recusado/cancelado: `PENDENTE`
- [ ] URL pública do webhook: `PENDENTE — depende da API em produção`

### Credenciais necessárias

Obtenha no **Stripe Dashboard → Developers**:

- [ ] Chave publicável de teste, iniciada por `pk_test_`.
- [ ] Chave secreta de teste, iniciada por `sk_test_`.
- [ ] Segredo do webhook de teste, iniciado por `whsec_`.
- [ ] Price ID de teste do DevFlow Pro, iniciado por `price_`.
- [ ] Chave publicável de produção, iniciada por `pk_live_`.
- [ ] Chave secreta de produção, iniciada por `sk_live_`.
- [ ] Segredo do webhook de produção, iniciado por `whsec_`.
- [ ] Price ID de produção do DevFlow Pro.

Esses valores devem ser colocados somente no `.env` local ou no gerenciador de segredos do servidor:

```env
PAYMENT_PROVIDER=stripe
PAYMENT_API_KEY=
PAYMENT_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=
```

Não enviar chave secreta ou segredo do webhook por captura de tela, documento público ou commit no GitHub.

### Webhook a configurar

Quando a integração estiver implementada e a API tiver endereço público HTTPS, o endereço previsto será semelhante a:

```text
https://api.seudominio.com/api/webhooks/payments/stripe/
```

Eventos necessários:

- `checkout.session.completed`;
- atualizações relevantes de assinatura;
- cancelamento da assinatura;
- falha ou atualização de pagamento, conforme habilitado no backend.

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
2. Informar se a conta Stripe está criada e ativada.
3. Criar o produto **DevFlow Pro** no modo de teste.
4. Criar o preço recorrente mensal de R$ 25,00 e informar apenas o `price_...`.
5. Configurar as credenciais de **teste** diretamente no `.env`; não colá-las neste arquivo.
6. Avisar quando as variáveis estiverem preenchidas para que a integração seja implementada e testada.

Para colocar em produção, também serão necessários domínio, provedor de deploy, PostgreSQL, HTTPS, credenciais de produção e webhook público.
