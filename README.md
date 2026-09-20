# AgendaSaaS

API backend de um SaaS de agendamento multi-tenant. Cada negócio (salão, clínica, prestador de serviço) cadastra sua conta, define os serviços que oferece, e os clientes finais agendam horário sem precisar criar login.

Projeto feito como peça de portfólio para demonstrar arquitetura de backend, não só CRUD — separação de camadas, regra de negócio isolada e testável, autenticação com JWT, migrações versionadas e testes automatizados cobrindo os casos que realmente importam (conflito de horário, limite de plano).

## Stack

- **FastAPI** — API, validação de request/response, docs automáticas (Swagger/Redoc)
- **SQLAlchemy 2.0** (estilo `Mapped`/`mapped_column`) — ORM
- **Alembic** — migrações de schema versionadas
- **JWT** (`python-jose`) + **bcrypt** — autenticação
- **SQLite** por padrão (troca pra Postgres só mudando `DATABASE_URL`, o código não depende do dialeto)
- **pytest** + **httpx** — testes de API ponta a ponta contra banco SQLite em memória

## Modelo de domínio

```
Tenant (negócio)
  ├── User (dono/staff, autenticado)
  └── Service (serviço oferecido: nome, duração, preço)
        └── Appointment (agendamento: cliente final, horário, status)
```

- **Multi-tenant por coluna** (`tenant_id` em cada tabela), não banco-por-cliente. É o padrão mais comum em SaaS real nesse estágio — mais simples de operar, migra fácil pra isolamento mais forte depois se o volume justificar.
- **Plano `free` limita a 3 serviços ativos, `pro` é ilimitado** — a regra que faz esse ser "um SaaS" de verdade, não só um cadastro. Fica isolada em `app/services/plan_limits.py`, testável sem precisar subir a API.
- **`duration_minutes` é copiado pro `Appointment` no momento do agendamento**, não lido do `Service` toda vez — assim, se o dono mudar a duração do serviço depois, agendamentos antigos não mudam retroativamente.

## Arquitetura

```
app/
  core/       # config, sessão de banco, segurança (hash/JWT), dependência de auth
  models/     # SQLAlchemy — schema do banco
  schemas/    # Pydantic — contrato de entrada/saída da API
  services/   # regra de negócio (conflito de horário, limite de plano)
  routers/    # endpoints HTTP — chamam services/, não reimplementam regra
  main.py
alembic/      # migrações versionadas
tests/        # pytest, um arquivo por área
```

A regra de negócio fica em `app/services/`, separada dos `routers/`. Isso significa que "não deixar agendar em horário conflitante" e "bloquear 4º serviço no plano free" são testados direto, sem precisar simular requisição HTTP — ver `tests/test_booking_conflict.py` e `tests/test_plan_limits.py`.

## Rodando local

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
cp .env.example .env          # opcional, valores default já funcionam

alembic upgrade head          # cria o banco SQLite com o schema
uvicorn app.main:app --reload
```

Abre `http://localhost:8000/docs` — Swagger interativo.

Rodar os testes:

```bash
pytest -v
```

## Fluxo de uso (exemplo via curl)

```bash
# 1. Negócio se cadastra
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"tenant_name":"Salão da Ana","tenant_slug":"salao-da-ana","email":"ana@salao.com","password":"senha1234"}'
# -> retorna access_token

# 2. Cadastra um serviço (usa o token acima)
curl -X POST http://localhost:8000/services \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Corte","duration_minutes":30,"price_cents":5000}'

# 3. Cliente final vê os serviços (sem login)
curl http://localhost:8000/public/salao-da-ana/services

# 4. Cliente final agenda (sem login)
curl -X POST http://localhost:8000/public/salao-da-ana/book \
  -H "Content-Type: application/json" \
  -d '{"service_id":1,"client_name":"Maria","client_contact":"11999990000","starts_at":"2027-01-10T14:00:00"}'

# 5. Tentar agendar no mesmo horário -> 409 Conflict
```

No Swagger, o botão "Authorize" espera usuário/senha em form (padrão OAuth2); como o login aqui é JSON puro (mais realista pra front-end/mobile consumirem), testa via `POST /auth/login` no "Try it out", copia o `access_token`, e cola em "Authorize" como `Bearer <token>`.

## Decisões de escopo (e o que faltaria pra produção)

- **Sem front-end** — API pura, o Swagger serve como demo visual.
- **Sem envio de e-mail/SMS de confirmação** — próximo passo natural, não implementado aqui pra manter o escopo focado em arquitetura de backend.
- **Conflito de horário é por serviço, não por "recurso/profissional"** — o schema não modela múltiplos atendentes. Um sistema real pra salão com 3 cabeleireiras precisaria de uma entidade `Staff`/`Resource` e checar conflito por recurso, não por serviço.
- **Sem Docker/deploy** — roda local, é o suficiente pra revisão de código.
