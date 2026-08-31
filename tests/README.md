# Testes do DevFlow

Esta pasta complementa, sem substituir, os testes Django mantidos em `backend/apps/*/tests.py` e os testes Vitest em `frontend/src/**/*.test.ts(x)`.

## Estrutura

- `run_all.py`: orquestra validação, Django, frontend, integração, segurança, smoke e build.
- `config.py`: configuração exclusivamente por variáveis de ambiente.
- `utils.py`: execução de comandos, cliente HTTP read-only e relatórios.
- `fixtures.py`: nomes únicos para dados temporários de ambientes controlados.
- `backend/`: contratos estáticos da arquitetura Django; a cobertura funcional fica nos apps.
- `frontend/`: router, imports, configuração da API e deploy SPA.
- `integration/`: correspondência entre chamadas frontend e endpoints backend.
- `security/`: CORS/CSRF, isolamento, segredos, env e exposição de tokens.
- `smoke/`: verificações remotas estritamente read-only.
- `reports/`: relatórios gerados localmente e ignorados pelo Git.

## Pré-requisitos

Instale as dependências existentes do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt -r requirements-dev.txt
cd frontend
npm install
```

A suíte transversal usa `unittest`, que já faz parte do Python. Pytest não é necessário. Os testes de ORM/API continuam usando o runner oficial do Django.

## Execução completa

```powershell
python tests/run_all.py
```

O runner detecta `package-lock.json` e usa npm. Ele retorna `0` quando todas as etapas críticas passam e `1` quando alguma falha.

Execução rápida, sem build e sem a suíte Django completa:

```powershell
python tests/run_all.py --fast
```

## Execução por categoria

```powershell
python tests/run_all.py --category backend
python tests/run_all.py --category frontend
python tests/run_all.py --category integration
python tests/run_all.py --category security
python tests/run_all.py --category smoke
```

Também é possível executar diretamente:

```powershell
.\.venv\Scripts\python.exe backend\manage.py test
npm --prefix frontend test -- --run
python -m unittest discover -s tests/security -t . -v
```

## Configuração

Variáveis reconhecidas:

```text
DEVFLOW_TEST_MODE=local|production
DEVFLOW_BACKEND_URL=https://backend.example.test
DEVFLOW_FRONTEND_URL=https://frontend.example.test
DEVFLOW_TEST_EMAIL=
DEVFLOW_TEST_PASSWORD=
DEVFLOW_TEST_USER_2_EMAIL=
DEVFLOW_TEST_USER_2_PASSWORD=
DEVFLOW_TEST_ORGANIZATION_ID=
DEVFLOW_HTTP_TIMEOUT=15
DEVFLOW_RUN_SMOKE=0|1
```

Não versione os valores. O runner não imprime senhas, tokens ou conteúdos identificados como segredos.

## Smoke de produção

O smoke remoto é desabilitado por padrão. Para executar contra os deployments padrão do DevFlow:

```powershell
$env:DEVFLOW_TEST_MODE='production'
python tests/run_all.py --category smoke
```

Esses testes usam somente `GET`, `HEAD` e `OPTIONS`. O cliente bloqueia `POST`, `PUT`, `PATCH` e `DELETE` em produção. A suíte nunca cria organizações, clientes, projetos, tarefas, cobranças ou PIX em produção.

Para smoke em staging, informe URLs próprias por variáveis de ambiente. Testes destrutivos devem continuar nos bancos efêmeros criados pelo Django.

## Banco e pagamentos

O runner local força SQLite de teste e o Django cria/destrói sua própria base. Ele não executa `migrate` automaticamente sobre bancos persistentes. `check` e `showmigrations --plan` são somente leitura.

Mercado Pago é exercitado exclusivamente com mocks existentes nas suítes de `finance` e `subscriptions`. Nenhum pagamento ou PIX real é emitido.

## Relatórios

Após cada execução:

```text
tests/reports/latest-report.txt
tests/reports/latest-report.json
```

Os arquivos são temporários e ignorados pelo Git. O JSON contém totais, status e resultado por etapa, adequado para futura integração com CI/CD.
