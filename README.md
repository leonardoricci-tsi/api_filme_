# Catálogo de Filmes — Tom Hanks (multi-tenant)

> Atividade da disciplina, proposta pelo professor [@siriani].

API FastAPI que lista filmes do Tom Hanks (dados sempre ao vivo da TMDB, nunca persistidos) e permite que cada usuário cadastrado no app favorite e comente filmes, com isolamento total de dados entre usuários proposto pelo professor @siriani.

**Atividade 3 — serviços desacoplados:** a autenticação (login, cadastro, papéis de usuário e recuperação de senha) foi extraída do catálogo para um microsserviço próprio, o `auth-service/`, que só é alcançável pela rede interna do Docker. O catálogo continua sendo o único ponto de entrada público. Veja a seção [Arquitetura](#arquitetura) e as [evidências](#evidências) mais abaixo.

## Stack
- **Backend:** FastAPI + SQLAlchemy + Alembic (catálogo e `auth-service`, cada um com sua própria migration history)
- **Banco:** MySQL (driver `pymysql`) — a mesma instância remota, compartilhada entre os dois serviços
- **Auth:** microsserviço próprio (`auth-service/`), cadastro/login com senha em hash `bcrypt`, sessão via JWT (assinatura verificada localmente pelo catálogo), papéis `usuario`/`admin`, recuperação de senha por e-mail com token de expiração de 30 minutos
- **E-mail:** SMTP — Mailtrap em desenvolvimento (sandbox, não entrega de verdade), Brevo em produção
- **Frontend:** Angular (standalone components), build servido como estático pelo próprio FastAPI em produção

## Arquitetura

Dois containers, uma rede interna, um único ponto de entrada público:

```
Navegador ──HTTPS──▶ Catálogo (api)                MySQL
                      único container com porta      (usuarios, favoritos,
                      publicada pro host              comentarios, reset_tokens)
                          │
                          │ rede interna do Docker (catalog-net)
                          ▼
                      auth-service
                      login, cadastro, role,
                      esqueci-senha
                      SEM porta publicada ──SMTP──▶ Mailtrap (dev) / Brevo (prod) ──▶ e-mail do usuário
```

- O `auth-service` não tem `ports:` no `docker-compose.yml` — só `expose: "8001"`, acessível apenas de dentro da rede `catalog-net`, pelo nome do serviço (`http://auth-service:8001`).
- O catálogo é o único container com porta publicada pro host. Toda rota `/auth/*` (registro, login, perfil, esqueci-senha, redefinir senha) é recebida pelo catálogo e repassada internamente pro `auth-service` (`app/services/auth_client.py`).
- Fora de `/auth/*`, o catálogo **não** chama o `auth-service` a cada request: o JWT é assinado pelo `auth-service` mas verificado localmente pelo catálogo (mesmo `JWT_SECRET` nos dois), o que evita um round-trip de rede em toda chamada autenticada.
- O JWT carrega um claim `role` (`usuario` ou `admin`); rotas de moderação (`/admin/*`) exigem `role=admin`.
- O catálogo não é mais dono da tabela `usuarios` — as FKs de `favoritos`/`comentarios` pra `usuarios` foram removidas; o isolamento entre usuários continua garantido, só que via `usuario_id` extraído do JWT, não mais por FK no banco.

## Recuperação de senha (esqueci minha senha)

1. `POST /auth/forgot-password` com o e-mail — sempre responde a mesma mensagem genérica, exista ou não o e-mail cadastrado (evita que alguém descubra quais e-mails têm conta testando um por um).
2. Se o e-mail existir, o `auth-service` gera um token aleatório (`secrets.token_urlsafe(32)`), grava na tabela `reset_tokens` com `expira_em = agora + 30 minutos` e `usado = false`, e envia por e-mail um link `.../redefinir-senha?token=...`.
3. `POST /auth/reset-password` com o token e a nova senha — o `auth-service` só troca a senha se o token existir, não estiver expirado e não tiver sido usado ainda; qualquer uma dessas falhas recusa a troca com `400`, sem dizer qual delas falhou.
4. Um token só pode ser usado uma vez: depois de trocar a senha, ele é marcado `usado = true` e uma segunda tentativa com o mesmo token é recusada.

Telas no frontend: `/esqueci-senha` (pedir o link) e `/redefinir-senha?token=...` (definir a nova senha, é a rota pra onde aponta o link do e-mail).

## Como rodar localmente

### 1. Pré-requisitos
- Python 3.11+
- Node.js 20+ (Angular CLI 21 exige Node `^20.19 || ^22.12 || >=24.0`)
- Um MySQL acessível (host, usuário, senha e um banco já criados)
- Uma chave de API do TMDB (https://www.themoviedb.org/settings/api)
- Uma conta no [Mailtrap](https://mailtrap.io) (grátis) — Email Testing → Inboxes → sua inbox → aba **SMTP Settings**, pra pegar `SMTP_USER`/`SMTP_PASSWORD`

### 2. Ambiente virtual e dependências
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -r auth-service/requirements.txt
```

### 3. Configurar variáveis de ambiente
Copie `.env.example` para `.env` e preencha com valores reais (o catálogo e o `auth-service` compartilham o mesmo `.env`):
```bash
cp .env.example .env
```
```
DATABASE_URL=mysql+pymysql://usuario:senha@host:3306/nome_do_banco
TMDB_API_KEY=sua_chave_do_tmdb
JWT_SECRET=um_valor_aleatorio_forte
JWT_EXPIRE_MINUTES=60
AUTH_SERVICE_URL=http://localhost:8001   # só pra rodar fora do Docker
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=usuario_do_mailtrap
SMTP_PASSWORD=senha_do_mailtrap
```

### 4. Rodar as migrations (catálogo e auth-service)
```bash
.venv/bin/alembic upgrade head
cd auth-service && ../.venv/bin/alembic upgrade head && cd ..
```
O catálogo cria `favoritos` e `comentarios`; o `auth-service` cria/altera `usuarios` (`role`) e `reset_tokens` — cada um com sua própria tabela de versão do Alembic (`alembic_version` e `alembic_version_auth`), já que dividem o mesmo schema MySQL.

### 5. Instalar as dependências do frontend
```bash
cd frontend && npm install
```

### 6. Subir em desenvolvimento (3 terminais)
```bash
# Terminal 1 — catálogo
.venv/bin/uvicorn app.main:app --reload --reload-exclude "$(pwd)/.venv"

# Terminal 2 — auth-service (as variáveis do .env da raiz precisam estar no ambiente)
cd auth-service
set -a && source ../.env && set +a
../.venv/bin/uvicorn app.main:app --reload --port 8001

# Terminal 3 — Angular (proxy encaminha /auth,/movies,/favorites,/comments pra :8000)
cd frontend && npm start
```
> O `--reload-exclude "$(pwd)/.venv"` é necessário porque o uvicorn sempre observa o diretório atual além do código do app — sem isso, qualquer instalação/atualização de pacote no `.venv` dispara reloads em loop e trava as requisições.
> Rodando assim (sem Docker), o catálogo precisa de `AUTH_SERVICE_URL=http://localhost:8001` no `.env` — o padrão `http://auth-service:8001` só resolve dentro da rede do Docker.
- Abrir **http://localhost:4200** (Angular com hot-reload, chamando a API via proxy)
- Catálogo sozinho: http://127.0.0.1:8000 — Docs interativas (Swagger): http://127.0.0.1:8000/docs
- `auth-service` nunca é chamado direto pelo navegador — só o catálogo fala com ele.

### 7. Build de produção (um único servidor pro catálogo)
```bash
cd frontend && npm run build   # gera os arquivos em app/static
cd .. && .venv/bin/uvicorn app.main:app
```
- Tudo servido em **http://127.0.0.1:8000** (API + frontend juntos, como o `angular.json` já aponta `outputPath` pra `app/static`)

### 8. Alternativa: rodar tudo com Docker Compose (recomendado)
```bash
docker compose up --build api auth-service
```
- Sobe os dois containers na mesma rede (`catalog-net`); só o `api` publica porta pro host (`:8000`).
- Rodar as migrations dos dois serviços (perfil `tools`, não sobe com o `up` normal):
  ```bash
  docker compose run --rm migrate
  docker compose run --rm migrate-auth
  ```
- Confirmar que o `auth-service` não tem porta publicada:
  ```bash
  docker compose ps auth-service   # a coluna PORTS deve vir vazia
  ```

### 9. Rodar os testes
```bash
.venv/bin/pytest -v
```
Os testes usam SQLite em memória (não tocam no MySQL configurado em `.env`), mockam as chamadas à TMDB e mockam as respostas do `auth-service` (`respx`) — rodam offline. Incluem os testes críticos de isolamento entre usuários: um usuário A não consegue ler, editar ou deletar um favorito/comentário do usuário B mesmo sabendo o ID do recurso (a API responde `404`, nunca `403`, para não vazar a existência do recurso).

## Endpoints

### Catálogo (público, `http://localhost:8000`)
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/auth/register` | não | Proxy pro `auth-service` — cadastra usuário, retorna JWT |
| POST | `/auth/login` | não | Proxy pro `auth-service` — login, retorna JWT |
| GET | `/auth/me` | sim | Proxy pro `auth-service` — dados do usuário logado |
| POST | `/auth/forgot-password` | não | Proxy pro `auth-service` — pede o link de redefinição por e-mail |
| POST | `/auth/reset-password` | não | Proxy pro `auth-service` — troca a senha usando o token do e-mail |
| GET | `/movies` | não | Lista filmes do Tom Hanks (dados ao vivo da TMDB, com sinopse; cache em memória de 5 min) |
| POST | `/favorites` | sim | Favorita um filme |
| GET | `/favorites` | sim | Lista favoritos do usuário logado |
| DELETE | `/favorites/{id}` | sim | Remove um favorito do usuário logado |
| POST | `/comments` | sim | Comenta um filme (envia `titulo` do filme junto) |
| GET | `/comments` | sim | Lista **todos** os comentários do usuário logado |
| GET | `/comments?tmdb_movie_id=` | sim | Lista comentários do usuário logado sobre um filme específico |
| DELETE | `/comments/{id}` | sim | Remove um comentário do usuário logado |
| GET | `/admin/comments` | sim (admin) | Lista comentários de **todos** os usuários (moderação) |
| DELETE | `/admin/comments/{id}` | sim (admin) | Remove o comentário de qualquer usuário |

Autenticação via header `Authorization: Bearer <token>`.

### auth-service (interno, sem acesso externo)
Só respondem pra chamadas vindas do catálogo, dentro da rede `catalog-net`: `/auth/register`, `/auth/login`, `/auth/me`, `/auth/forgot-password`, `/auth/reset-password`.

## Estrutura do projeto
```
app/                    # catálogo
  models/       # SQLAlchemy declarative models (favoritos, comentarios)
  schemas/      # Pydantic (request/response)
  auth/         # verificação local do JWT (dependência get_current_user, require_admin)
  routers/      # rotas da API, incluindo o proxy de /auth/* pro auth-service
  services/     # cliente HTTP do auth-service (auth_client.py) + cliente da TMDB (dados ao vivo, com cache)
  static/       # build de produção do Angular (gerado por `npm run build`, não editar à mão)
alembic/        # migrations do catálogo
tests/          # pytest (SQLite em memória + mocks da TMDB e do auth-service)
auth-service/           # microsserviço de autenticação
  app/
    models/     # Usuario (com role), ResetToken
    auth/       # hash de senha, emissão/validação de JWT, geração e validação de reset tokens
    routers/    # /auth/* (register, login, me) e /auth/forgot-password, /auth/reset-password
    services/   # mailer.py — envio do e-mail de redefinição via SMTP
  alembic/      # migrations do auth-service (histórico próprio, alembic_version_auth)
frontend/       # projeto Angular (standalone components)
  src/app/
    core/       # services (auth/movies/favorites/comments), interceptor de JWT, guards de rota
    layout/     # header (avatar + navegação) e app-shell (layout das rotas privadas)
    shared/     # movie-card (usado no catálogo e nos favoritos, com diálogo de comentários)
    features/   # telas: auth/login, auth/register, auth/forgot-password, auth/reset-password, catalog, favorites, comments
docker-compose.yml      # os dois serviços (api, auth-service) + rede compartilhada catalog-net
```

## Notas de segurança / design
- `poster_path` e sinopse dos filmes nunca são persistidos — sempre vêm ao vivo da TMDB a cada chamada a `/movies`. O único dado de filme salvo no banco é o `tmdb_movie_id` (e, em `favoritos`/`comentarios`, uma cópia do título escolhida pelo usuário no momento de favoritar/comentar — só pra exibição, não é cache do catálogo).
- `usuario_id` nunca vem do corpo da requisição — é sempre extraído do JWT.
- Toda query de favoritos/comentários filtra obrigatoriamente por `usuario_id` do usuário logado (`app/routers/_ownership.py`).
- O JWT é assinado só pelo `auth-service`; o catálogo apenas verifica a assinatura com o `JWT_SECRET` compartilhado — não existe endpoint que aceite `role` ou `usuario_id` vindos do cliente.
- Token de redefinição de senha: aleatório e criptograficamente seguro (`secrets.token_urlsafe`, não um UUID sequencial), expira em 30 minutos, é de uso único, e a mensagem de "esqueci minha senha" nunca revela se o e-mail existe ou não.
- Promoção de usuário pra `admin` é feita manualmente no banco (não existe endpoint nem script commitado pra isso) — é uma ação pontual de quem administra o sistema, não uma feature da aplicação.
- `npm run build` copia `index.html` para `404.html` em `app/static` (truque padrão do Starlette pra SPA): assim, um refresh direto numa rota do Angular (ex: `/favoritos`) ainda carrega o app em vez de um 404 vazio.

## Evidências

Evidências pedidas pelo professor pra atividade 3 — fluxo completo de recuperação de senha e confirmação de que o `auth-service` não é acessível de fora.

**1. Pedido de redefinição enviado:**

![Pedido de redefinição enviado](docs/evidencias/pedido-enviado.png)

**2. E-mail recebido no Mailtrap, com o link e o token:**

![E-mail de redefinição recebido no Mailtrap](docs/evidencias/email-recebido.png)

**3. Link usado → senha redefinida com sucesso:**

![Senha redefinida com sucesso](docs/evidencias/redefinicao-sucesso.png)

**4. Tentativa de reusar o mesmo link → recusada:**

![Tentativa de reuso do link recusada](docs/evidencias/link-reutilizado-recusado.png)
