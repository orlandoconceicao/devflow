# Segurança

Relate vulnerabilidades de forma privada para `orlandoconceicao94@gmail.com`. Não abra uma issue pública com tokens, dados pessoais ou detalhes exploráveis.

O DevFlow aplica isolamento por organização, RBAC, JWT curto com rotação/blacklist, uploads privados, limites de arquivo, webhook Mercado Pago assinado e idempotente, consulta autenticada do recurso financeiro, valores monetários em `Decimal`, throttling, headers HTTPS, tokens de convite armazenados como hash e recuperação de senha não enumerável.

Segredos são fornecidos exclusivamente por variáveis de ambiente. Dados completos de cartão nunca são recebidos ou armazenados.
