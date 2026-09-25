# Catálogo de Filmes — Tom Hanks (multi-tenant)

> Atividade da disciplina, proposta pelo professor [@siriani](https://github.com/siriani).

API FastAPI que lista filmes do Tom Hanks (dados sempre ao vivo da TMDB, nunca persistidos) e permite que cada usuário cadastrado no app favorite e comente filmes, com isolamento total de dados entre usuários proposto pelo professor @siriani.

**Atividade 3 — serviços desacoplados:** a autenticação (login, cadastro, papéis de usuário e recuperação de senha) foi extraída do catálogo para um microsserviço próprio, o `auth-service/`, que só é alcançável pela rede interna do Docker. O catálogo continua sendo o único ponto de entrada público. Veja a seção [Arquitetura](#arquitetura) e as [evidências](#evidências) mais abaixo.

## Stack
- **Backend:** FastAPI + SQLAlchemy + Alembic (catálogo e `auth-service`, cada um com sua própria migration history)
- **Banco:** MySQL (driver `pymysql`) — a mesma instância remota, compartilhada entre os dois serviços
- **Auth:** microsserviço próprio (`auth-service/`), cadastro/login com senha em hash `bcrypt`, sessão via JWT (assinatura verificada localmente pelo catálogo), papéis `usuario`/`admin`, recuperação de senha por e-mail com token de expiração de 30 minutos
- **E-mail:** SMTP — Mailtrap em desenvolvimento (sandbox, não entrega de verdade), Brevo em produção
- **Frontend:** Angular (standalone components), build servido como estático pelo próprio FastAPI em produção

## Arquitetura

Quatro containers, uma rede interna, um único ponto de entrada público:

```
Navegador ──HTTPS──▶ Catálogo (api)                MySQL
                      único container com porta      (usuarios, favoritos,
                      publicada pro host              comentarios, reset_tokens)
                          │         │
                          │         │ POST /logs (login, logout, favoritar,
                          │         │ comentar, apagar, 403 negado)
                          │         ▼
                          │     log-service ──XADD──▶ Redis (Stream audit_log)
                          │     SEM porta publicada    SEM porta publicada
                          │     GET /logs = só admin
                          │         ▲
                          │         │ POST /logs (login, 403 negado)
                          │ rede interna do Docker (catalog-net)
                          ▼         │
                      auth-service ─┘
                      login, cadastro, role,
                      esqueci-senha
                      SEM porta publicada ──SMTP──▶ Mailtrap (dev) / Brevo (prod) ──▶ e-mail do usuário
```

- O `auth-service` não tem `ports:` no `docker-compose.yml` — só `expose: "8001"`, acessível apenas de dentro da rede `catalog-net`, pelo nome do serviço (`http://auth-service:8001`). O `log-service` (atividade 5) e o `redis` seguem o mesmo princípio: `expose: "8002"` e `expose: "6379"`, nenhum dos dois alcançável de fora.
- O catálogo é o único container com porta publicada pro host. Toda rota `/auth/*` (registro, login, perfil, esqueci-senha, redefinir senha) é recebida pelo catálogo e repassada internamente pro `auth-service` (`app/services/auth_client.py`).
- Fora de `/auth/*`, o catálogo **não** chama o `auth-service` a cada request: o JWT é assinado pelo `auth-service` mas verificado localmente pelo catálogo (mesmo `JWT_SECRET` nos dois), o que evita um round-trip de rede em toda chamada autenticada.
- Catálogo e `auth-service` são os únicos que decidem o que auditar — nenhum dos dois escreve log de auditoria no próprio banco (MySQL); os dois mandam um evento HTTP (`POST /logs`) pro `log-service`, que é quem sabe gravar num Redis Stream. Detalhes na seção [Auditoria (logs)](#auditoria-logs-atividade-5).
- O JWT carrega um claim `role`; toda rota sensível decide o que aceitar olhando só pra esse claim — nunca por nada que o cliente mande. Veja a seção [Autorização (RBAC)](#autorização-rbac-atividade-4) logo abaixo pros papéis e permissões de verdade.
- O catálogo não é mais dono da tabela `usuarios` — as FKs de `favoritos`/`comentarios` pra `usuarios` foram removidas; o isolamento entre usuários continua garantido, só que via `usuario_id` extraído do JWT, não mais por FK no banco.

## Autorização (RBAC, atividade 4)

**Atividade 4 — controle de acesso por papel:** o campo `role` existia desde a atividade 3, mas não decidia nada — qualquer papel conseguia fazer qualquer coisa. Agora ele decide de verdade, e quem decide é sempre o servidor, nunca a tela: esconder um botão no Angular não é segurança, é só interface. Toda ação sensível é recusada com `403` no backend pra quem não tem o papel certo, mesmo chamando o endpoint direto pelo Postman/curl.

**Atividade 5 — logs e auditoria:** o sistema fazia coisas, mas não lembrava o que fez. Agora todo login, logout, favoritar, comentar, apagar comentário (moderação) e toda tentativa de ação negada por permissão (o `403` da atividade 4) deixa um rastro — quem fez o quê, e quando. Isso é log de auditoria, diferente de log de aplicação (erro/debug): ajuda a entender comportamento de gente, não bugs. Fica num microsserviço próprio, o `log-service/`, gravando em Redis Streams — nem o catálogo nem o `auth-service` escrevem log de auditoria no próprio banco. Veja a seção [Auditoria (logs)](#auditoria-logs-atividade-5) mais abaixo.

### Papéis e permissões

Quatro papéis, empilhados — cada um inclui a permissão do anterior, `admin` é o topo: consome tudo que `stalker_do_tomhanks` consome **e** ainda modera.

| Papel | Pode fazer |
|---|---|
| `cinefilo` (papel padrão no cadastro) | Ver o catálogo de filmes (`GET /movies`, `GET /movies/{id}/detalhes`) |
| `nerd` | Tudo de `cinefilo` **+** comentar e favoritar filmes (`/comments/*`, `/favorites/*`) |
| `stalker_do_tomhanks` | Tudo de `nerd` **+** jogar o quiz do pôster pixelado (`/quiz/pixelado`, exclusivo desse papel pra cima) |
| `admin` | Tudo de `stalker_do_tomhanks` **+** exclusivo dele: apagar comentário/favorito de **qualquer** usuário (`/admin/comments/*`, `/admin/favorites/*`) e listar/promover/rebaixar o papel de qualquer usuário (`GET /auth/admin/users`, `PATCH /auth/admin/users/{id}/role`) |

A escada de nível fica em `app/auth/dependencies.py` (`NIVEL_PAPEL`, `require_papel_minimo`) — `admin` tem o nível mais alto (4), então qualquer rota que exija `nerd`+ ou `stalker_do_tomhanks`+ já libera admin de graça, sem precisar listar o papel em cada rota. As ações **exclusivas** de admin (moderação, promoção) usam uma segunda dependência, `require_admin`, que exige o papel exato — não é "nível mínimo", é "só esse papel mesmo".

### Ação exclusiva de admin

Duas frentes, ambas só admin:
- **Moderação:** `DELETE /admin/comments/{id}` e `DELETE /admin/favorites/{id}` apagam o comentário/favorito de qualquer usuário (não só o próprio); `GET /admin/comments` e `GET /admin/favorites` listam de todo mundo. Tudo dentro do catálogo, checado localmente (`app/routers/admin.py`, `require_admin`).
- **Gestão de usuário:** `GET /auth/admin/users` + `PATCH /auth/admin/users/{id}/role` lista usuários e muda o papel de qualquer um. Como a tabela `usuarios` pertence ao `auth-service` (não ao catálogo, desde a atividade 3), a checagem de `role == "admin"` acontece lá (`auth-service/app/auth/dependencies.py::require_admin`) — o catálogo só repassa a chamada (`app/routers/auth.py`), do mesmo jeito que já repassa `/auth/register` e `/auth/login`.

### Quiz do pôster pixelado (exclusivo de `stalker_do_tomhanks`)

`GET /quiz/pixelado` sorteia um filme do Tom Hanks, baixa o pôster de verdade da TMDB (ao vivo, nunca persistido) e devolve ele pixelado + 4 opções de título. `POST /quiz/pixelado/resposta` confere o palpite — **sempre no servidor**: o cliente nunca recebe a resposta certa antes de enviar a tentativa, só um `round_id` assinado (JWT com o `id` do filme, mesmo `JWT_SECRET` do login) que ele não consegue forjar nem decodificar sem a chave. É o mesmo princípio do RBAC aplicado a outra coisa: nunca confiar em nada que o cliente diga sobre si mesmo.

### Padrão A (centralizado) ou Padrão B (claims no JWT)?

**Padrão B.** O catálogo nunca faz uma chamada de rede pro `auth-service` pra decidir uma permissão em `/comments`, `/favorites` ou `/quiz/*` — o `role` já vem dentro do JWT, assinado, e `require_papel_minimo`/`require_admin` só leem o claim localmente (`app/auth/dependencies.py`). É a exceção de propósito: `/admin/users*` (listar/promover usuário) *é* uma chamada de rede ao `auth-service`, mas não pra checar permissão — é porque a tabela `usuarios` mora lá, não no catálogo; a checagem de `role == "admin"` em si acontece toda dentro do `auth-service`, sem round-trip nenhum.

**Se fosse pro Padrão A:** cada rota de `/comments`, `/favorites` e `/quiz/*` deixaria de ler `usuario_atual.role` do dataclass `UsuarioAutenticado` (que hoje só decodifica o JWT) e passaria a chamar um endpoint novo tipo `POST /auth/pode?acao=comentar` no `auth-service` a cada requisição, esperar a resposta, e só então seguir. Ganharia revogação imediata (rebaixar um `stalker_do_tomhanks` pra `cinefilo` valeria na próxima requisição dele, não só quando o token expirar); perderia velocidade (round-trip de rede extra em toda ação, não só nas de admin) e adicionaria uma dependência de disponibilidade — se o `auth-service` cair, `/comments` e `/favorites` param de funcionar até pra quem já tinha token válido, porque não teria mais como confirmar o papel.

## Auditoria (logs, atividade 5)

Log de auditoria é diferente de log de aplicação (erro, debug, stack trace) — aquele ajuda a entender bugs, este ajuda a entender comportamento de gente: quem fez o quê, e quando. Se um comentário sumir ou um usuário virar admin do nada, é aqui que dá pra responder "o que aconteceu".

### Por que um microsserviço próprio, e por que Redis
Catálogo e `auth-service` já têm banco relacional (MySQL) — poderiam escrever log ali. Mas log de auditoria tem um padrão de uso bem diferente de dado de negócio: escreve muito, lê pouco, quase nunca precisa de transação, e não pode ficar misturado com a tabela que ele audita (se um bug no código do catálogo apagar registros à toa, o rastro do que aconteceu não pode estar no mesmo lugar). Por isso vira um serviço à parte, o `log-service/`, e por isso o MySQL não é a ferramenta certa: **Redis Streams** (`XADD` pra gravar, `XREVRANGE` pra consultar) é pensado exatamente pra log de eventos ordenado no tempo, rápido pra escrita em alto volume — foi a opção escolhida (não a lista simples com `LPUSH`, que perderia a ordenação/timestamp nativos que o Streams já resolve de graça).

### Como o evento chega no log-service
Catálogo e `auth-service` nunca escrevem direto no Redis — mantém a centralização: cada um manda um `POST /logs` pro `log-service` (`app/services/log_client.py` e `auth-service/app/services/log_client.py`), que é quem grava no Stream. A chamada é **fire-and-forget**: se o `log-service` cair, a ação real do usuário (favoritar, comentar, logar) não pode virar erro por causa de um serviço que só observa — a falha é engolida, com timeout curto.

### Eventos auditados
| Evento | `acao` gravada | Onde é decidido |
|---|---|---|
| Login | `login` | `auth-service`, após senha validada |
| Logout | `logout` | Catálogo, `POST /auth/logout` (JWT é stateless — não existe sessão pra invalidar; essa rota só existe pra deixar o rastro) |
| Favoritar filme | `favoritar_filme:{tmdb_movie_id}` | Catálogo, `POST /favorites` |
| Comentar | `comentar:{tmdb_movie_id}` | Catálogo, `POST /comments` |
| Apagar comentário (moderação) | `apagar_comentario_moderacao:{comentario_id}` | Catálogo, `DELETE /admin/comments/{id}` |
| Tentativa negada por permissão (403) | `acesso_negado:{papel}` (ex.: `acesso_negado:admin`, `acesso_negado:nerd`) | Dentro de `require_admin`/`require_papel_minimo`, nos dois serviços — cobre **toda** rota protegida de uma vez, sem precisar logar em cada endpoint separadamente |

Estrutura mínima de cada evento: `usuario_id`, `acao`, `timestamp` (gerado pelo `log-service`, não pelo chamador) e, como bônus, `ip` (`request.client.host` de quem chamou).

### Consultar o log — só admin
`GET /logs` no `log-service` exige `role == "admin"` (decodifica o mesmo JWT localmente, sem round-trip — mesmo princípio do resto do RBAC). Como o `log-service` não tem porta publicada pro host, quem quiser consultar de fora usa `GET /admin/logs` no catálogo: barra com `403` quem não for admin **antes** de sequer tentar o proxy (`app/routers/admin.py`), e repassa o header `Authorization` original pro `log-service`, que confere de novo — defesa em profundidade, não round-trip redundante à toa.

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
- Um Redis acessível (só se for rodar o `log-service` fora do Docker — pela alternativa do Docker Compose, no passo 8, já vem incluso)
- Uma chave de API do TMDB (https://www.themoviedb.org/settings/api)
- Uma conta no [Mailtrap](https://mailtrap.io) (grátis) — Email Testing → Inboxes → sua inbox → aba **SMTP Settings**, pra pegar `SMTP_USER`/`SMTP_PASSWORD`

### 2. Ambiente virtual e dependências
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -r auth-service/requirements.txt

# log-service é um projeto Python à parte (dependências próprias — fakeredis
# nos testes, sem SQLAlchemy/Alembic), por isso tem seu próprio .venv:
python3 -m venv log-service/.venv
log-service/.venv/bin/pip install -r log-service/requirements.txt
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
LOG_SERVICE_URL=http://localhost:8002    # idem
REDIS_URL=redis://localhost:6379/0       # idem
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

### 6. Subir em desenvolvimento (5 terminais)
```bash
# Terminal 1 — Redis (só o log-service precisa)
docker run --rm -p 6379:6379 redis:7-alpine

# Terminal 2 — log-service (venv próprio, ver passo 2)
cd log-service
set -a && source ../.env && set +a
.venv/bin/uvicorn app.main:app --reload --port 8002

# Terminal 3 — catálogo
.venv/bin/uvicorn app.main:app --reload --reload-exclude "$(pwd)/.venv"

# Terminal 4 — auth-service (as variáveis do .env da raiz precisam estar no ambiente)
cd auth-service
set -a && source ../.env && set +a
../.venv/bin/uvicorn app.main:app --reload --port 8001

# Terminal 5 — Angular (proxy encaminha /auth,/movies,/favorites,/comments pra :8000)
cd frontend && npm start
```
> O `--reload-exclude "$(pwd)/.venv"` é necessário porque o uvicorn sempre observa o diretório atual além do código do app — sem isso, qualquer instalação/atualização de pacote no `.venv` dispara reloads em loop e trava as requisições.
> Rodando assim (sem Docker), catálogo e `auth-service` precisam de `AUTH_SERVICE_URL=http://localhost:8001` e `LOG_SERVICE_URL=http://localhost:8002` no `.env` — os padrões `http://auth-service:8001`/`http://log-service:8002` só resolvem dentro da rede do Docker.
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
docker compose up --build
```
- Sobe os quatro containers na mesma rede (`catalog-net`): `api`, `auth-service`, `log-service` e `redis`. Só o `api` publica porta pro host (`:8000`).
- Rodar as migrations do catálogo e do `auth-service` (perfil `tools`, não sobe com o `up` normal — o `log-service` não tem migration, não guarda nada em SQL):
  ```bash
  docker compose run --rm migrate
  docker compose run --rm migrate-auth
  ```
- Confirmar que `auth-service`, `log-service` e `redis` não têm porta publicada:
  ```bash
  docker compose ps   # a coluna PORTS só deve vir preenchida pro serviço api
  ```

### 9. Rodar os testes
```bash
.venv/bin/pytest -v                              # catálogo (raiz)
cd log-service && .venv/bin/python -m pytest -v  # log-service — .venv próprio (passo 2)
```
Os testes do catálogo usam SQLite em memória (não tocam no MySQL configurado em `.env`), mockam as chamadas à TMDB e mockam as respostas do `auth-service`/`log-service` (`respx`) — rodam offline. Incluem os testes críticos de isolamento entre usuários: um usuário A não consegue ler, editar ou deletar um favorito/comentário do usuário B mesmo sabendo o ID do recurso (a API responde `404`, nunca `403`, para não vazar a existência do recurso).

Os testes do `log-service` usam `fakeredis` (Redis em memória, sem precisar de um Redis de verdade rodando) — têm seu próprio `.venv` e `pytest.ini`, por isso rodam à parte (cada serviço é um projeto Python independente).

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
| POST | `/favorites` | sim (nerd+) | Favorita um filme |
| GET | `/favorites` | sim (nerd+) | Lista favoritos do usuário logado |
| DELETE | `/favorites/{id}` | sim (nerd+) | Remove um favorito do usuário logado |
| POST | `/comments` | sim (nerd+) | Comenta um filme (envia `titulo` do filme junto) |
| GET | `/comments` | sim (nerd+) | Lista **todos** os comentários do usuário logado |
| GET | `/comments?tmdb_movie_id=` | sim (nerd+) | Lista comentários do usuário logado sobre um filme específico |
| DELETE | `/comments/{id}` | sim (nerd+) | Remove um comentário do usuário logado |
| GET | `/quiz/pixelado` | sim (stalker+) | Sorteia um filme, devolve o pôster pixelado + 4 opções de título |
| POST | `/quiz/pixelado/resposta` | sim (stalker+) | Confere o palpite — checagem sempre no servidor |
| GET | `/admin/comments` | sim (admin) | Lista comentários de **todos** os usuários (moderação) |
| DELETE | `/admin/comments/{id}` | sim (admin) | Remove o comentário de qualquer usuário |
| GET | `/admin/favorites` | sim (admin) | Lista favoritos de **todos** os usuários (moderação) |
| DELETE | `/admin/favorites/{id}` | sim (admin) | Remove o favorito de qualquer usuário |
| GET | `/auth/admin/users` | sim (admin) | Proxy pro `auth-service` — lista todos os usuários cadastrados |
| PATCH | `/auth/admin/users/{id}/role` | sim (admin) | Proxy pro `auth-service` — promove/rebaixa o papel de um usuário |
| POST | `/auth/logout` | sim | Não invalida nada no servidor (JWT é stateless) — só registra o evento de auditoria |
| GET | `/admin/logs` | sim (admin) | Proxy pro `log-service` — últimos N eventos de auditoria (atividade 5), mais recente primeiro |

Autenticação via header `Authorization: Bearer <token>`. "nerd+" = `nerd`, `stalker_do_tomhanks` ou `admin`; "stalker+" = `stalker_do_tomhanks` ou `admin` — a escada é cumulativa (veja [Autorização (RBAC)](#autorização-rbac-atividade-4)).

### auth-service (interno, sem acesso externo)
Só respondem pra chamadas vindas do catálogo, dentro da rede `catalog-net`: `/auth/register`, `/auth/login`, `/auth/me`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/admin/users`, `/auth/admin/users/{id}/role`.

### log-service (interno, sem acesso externo)
Só respondem pra chamadas vindas do catálogo ou do `auth-service`, dentro da rede `catalog-net`:
| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/logs` | não (interno) | Grava um evento no Redis Stream — sem autenticação própria porque só é alcançável de dentro da rede, chamado depois que o catálogo/auth-service já identificaram o usuário |
| GET | `/logs?limit=` | sim (admin) | Últimos N eventos, mais recente primeiro — é essa rota que o catálogo repassa em `GET /admin/logs` |

## Estrutura do projeto
```
app/                    # catálogo
  models/       # SQLAlchemy declarative models (favoritos, comentarios)
  schemas/      # Pydantic (request/response)
  auth/         # verificação local do JWT (get_current_user, require_papel_minimo, require_admin)
  routers/      # rotas da API: quiz.py (pixelado, stalker+), admin.py (moderação de comentários e favoritos),
                #   auth.py (proxy de /auth/* e /auth/admin/* pro auth-service), comments/favorites (nerd+)
  services/     # cliente HTTP do auth-service (auth_client.py), do log-service (log_client.py) + cliente da TMDB
  static/       # build de produção do Angular (gerado por `npm run build`, não editar à mão)
alembic/        # migrations do catálogo
tests/          # pytest (SQLite em memória + mocks da TMDB, do auth-service e do log-service via respx),
                #   test_roles.py cobre o RBAC, test_audit_log.py cobre a auditoria (atividade 5)
auth-service/           # microsserviço de autenticação
  app/
    models/     # Usuario (com role: cinefilo/nerd/stalker_do_tomhanks/admin), ResetToken
    auth/       # hash de senha, emissão/validação de JWT, geração e validação de reset tokens, require_admin
    routers/    # /auth/* (register, login, me), /auth/forgot-password, /auth/reset-password,
                #   /auth/admin/users e /auth/admin/users/{id}/role (admin.py, atividade 4)
    services/   # mailer.py (e-mail de redefinição via SMTP), log_client.py (evento de login/403 pro log-service)
  alembic/      # migrations do auth-service (histórico próprio, alembic_version_auth)
log-service/            # microsserviço de auditoria (atividade 5) — SEM alembic/SQL, só Redis
  app/
    schemas.py  # LogEventIn/LogEventOut (usuario_id, acao, timestamp, ip)
    auth.py     # require_admin — decodifica o mesmo JWT localmente, sem tabela de usuários própria
    redis_client.py  # dependência do FastAPI (troca por fakeredis nos testes)
    routers/logs.py  # POST /logs (XADD) e GET /logs (XREVRANGE, só admin)
  tests/        # pytest com fakeredis — .venv e pytest.ini próprios (projeto Python à parte)
frontend/       # projeto Angular (standalone components)
  src/app/
    core/       # services (auth/movies/favorites/comments), interceptor de JWT, guards de rota
    layout/     # header (avatar + navegação) e app-shell (layout das rotas privadas)
    shared/     # movie-card (usado no catálogo e nos favoritos, com diálogo de comentários)
    features/   # telas: auth/login, auth/register, auth/forgot-password, auth/reset-password, catalog, favorites, comments
docker-compose.yml      # os quatro serviços (api, auth-service, log-service, redis) + rede catalog-net
```

## Notas de segurança / design
- `poster_path` e sinopse dos filmes nunca são persistidos — sempre vêm ao vivo da TMDB a cada chamada a `/movies`. O único dado de filme salvo no banco é o `tmdb_movie_id` (e, em `favoritos`/`comentarios`, uma cópia do título escolhida pelo usuário no momento de favoritar/comentar — só pra exibição, não é cache do catálogo).
- `usuario_id` nunca vem do corpo da requisição — é sempre extraído do JWT.
- Toda query de favoritos/comentários filtra obrigatoriamente por `usuario_id` do usuário logado (`app/routers/_ownership.py`).
- O JWT é assinado só pelo `auth-service`; o catálogo apenas verifica a assinatura com o `JWT_SECRET` compartilhado — não existe endpoint que aceite `role` ou `usuario_id` vindos do cliente.
- Token de redefinição de senha: aleatório e criptograficamente seguro (`secrets.token_urlsafe`, não um UUID sequencial), expira em 30 minutos, é de uso único, e a mensagem de "esqueci minha senha" nunca revela se o e-mail existe ou não.
- Promover/rebaixar o papel de um usuário é `PATCH /auth/admin/users/{id}/role` — só admin (atividade 4). O **primeiro** admin do sistema, esse sim, precisa ser promovido manualmente no banco (`UPDATE usuarios SET role='admin' WHERE id=...`), já que ninguém nasce admin — é o único bootstrap que não tem endpoint de propósito.
- `npm run build` copia `index.html` para `404.html` em `app/static` (truque padrão do Starlette pra SPA): assim, um refresh direto numa rota do Angular (ex: `/favoritos`) ainda carrega o app em vez de um 404 vazio.
- Auditoria (atividade 5) é fire-and-forget: uma falha no `log-service` (fora do ar, rede interna com problema) nunca derruba a ação real do usuário — favoritar/comentar/logar não podem virar `500` por causa de um serviço que só observa. O custo é a possibilidade (rara) de perder um evento se o `log-service` cair bem na hora; pra essa atividade, não justifica trocar por fila/retry.
- `log-service` não tem tabela de usuários própria — decodifica o mesmo JWT localmente (mesmo `JWT_SECRET`) pra saber quem é admin, igual o catálogo faz pro resto do RBAC.

## Evidências

### Atividade 5 — Auditoria: login, favoritar, comentar, ação negada e consulta como admin

Roteiro da demonstração pedida pelo professor: login → favoritar um filme → comentar → tentar uma ação de admin sem ser admin (403) → logout → consultar o log como admin (`GET /admin/logs`) e ver todos os eventos, na ordem certa. As ações de login/favoritar/comentar/logout foram executadas por `curl` contra os containers reais (`docker compose up`) e o MySQL de verdade antes dos prints abaixo — os prints em si (Swagger UI) capturam as duas pontas que precisam de prova visual: a tentativa negada e a consulta do log.

**1. Usuário `nerd` (não-admin) tentando uma ação exclusiva de admin — recusado com 403:**

![Usuário nerd recebe 403 ao tentar GET /admin/comments](docs/evidencias/auditoria-403-negado.png)

**2. Consulta do log como admin — `login`, `favoritar_filme`, `comentar`, `logout` e `acesso_negado:admin` capturados, mais recente primeiro:**

![Consulta de GET /admin/logs como admin, mostrando os eventos na ordem certa](docs/evidencias/auditoria-consulta-admin.png)

**3. Usuário comum tentando consultar o log — recusado com 403 (o catálogo nem chega a repassar pro log-service):**

![Usuário comum recebe 403 ao tentar GET /admin/logs](docs/evidencias/auditoria-403-consulta.png)

### Atividade 4 — RBAC: mesma ação, dois papéis

Mesma chamada (`PATCH /auth/admin/users/{id}/role`, promover um usuário), dois tokens diferentes — o `cinefilo` é recusado, o `admin` executa. Validado por curl direto no `auth-service` local antes do print (respostas reais, não simuladas): `cinefilo` → `403 {"detail":"Acesso restrito a admins"}`, `admin` → `200` com o `role` do usuário-alvo atualizado.

**1. Usuário comum (`cinefilo`) tentando promover alguém — recusado com 403:**

![Usuário comum recebe 403 ao tentar ação de admin](docs/evidencias/rbac-403-comum.png)

**2. Admin de verdade fazendo a mesma chamada — sucesso:**

![Admin executa a promoção com sucesso](docs/evidencias/rbac-200-admin.png)

Evidências pedidas pelo professor pra atividade 3 — fluxo completo de recuperação de senha e confirmação de que o `auth-service` não é acessível de fora.

**1. Pedido de redefinição enviado:**

![Pedido de redefinição enviado](docs/evidencias/pedido-enviado.png)

**2. E-mail recebido no Mailtrap, com o link e o token:**

![E-mail de redefinição recebido no Mailtrap](docs/evidencias/email-recebido.png)

**3. Link usado → senha redefinida com sucesso:**

![Senha redefinida com sucesso](docs/evidencias/redefinicao-sucesso.png)

**4. Tentativa de reusar o mesmo link → recusada:**

![Tentativa de reuso do link recusada](docs/evidencias/link-reutilizado-recusado.png)
