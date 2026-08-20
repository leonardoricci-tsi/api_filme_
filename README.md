# Catálogo de Filmes — Tom Hanks (multi-tenant)

> Atividade da disciplina, proposta pelo professor [@siriani].

API FastAPI que lista filmes do Tom Hanks (dados sempre ao vivo da TMDB, nunca persistidos) e permite que cada usuário cadastrado no app favorite e comente filmes, com isolamento total de dados entre usuários.

## Stack
- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Banco:** MySQL (driver `pymysql`)
- **Auth:** cadastro/login próprios do app, senha com hash `bcrypt`, sessão via JWT
- **Frontend:** Angular (standalone components), build servido como estático pelo próprio FastAPI em produção

## Como rodar localmente

### 1. Pré-requisitos
- Python 3.11+
- Node.js 20+ (Angular CLI 21 exige Node `^20.19 || ^22.12 || >=24.0`)
- Um MySQL acessível (host, usuário, senha e um banco já criados)
- Uma chave de API do TMDB (https://www.themoviedb.org/settings/api)

### 2. Ambiente virtual e dependências
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente
Copie `.env.example` para `.env` e preencha com valores reais:
```bash
cp .env.example .env
```
```
DATABASE_URL=mysql+pymysql://usuario:senha@host:3306/nome_do_banco
TMDB_API_KEY=sua_chave_do_tmdb
JWT_SECRET=um_valor_aleatorio_forte
JWT_EXPIRE_MINUTES=60
```

### 4. Rodar as migrations
```bash
.venv/bin/alembic upgrade head
```
Isso cria as tabelas `usuarios`, `favoritos` e `comentarios` (com a FK e a constraint `UNIQUE(usuario_id, tmdb_movie_id)` em `favoritos`).

### 5. Instalar as dependências do frontend
```bash
cd frontend && npm install
```

### 6. Subir em desenvolvimento (2 terminais)
```bash
# Terminal 1 — API
.venv/bin/uvicorn app.main:app --reload --reload-exclude "$(pwd)/.venv"

# Terminal 2 — Angular (proxy configurado pra encaminhar /auth,/movies,/favorites,/comments pra :8000)
cd frontend && npm start
```
> O `--reload-exclude "$(pwd)/.venv"` é necessário porque o uvicorn sempre observa o diretório atual além do código do app — sem isso, qualquer instalação/atualização de pacote no `.venv` dispara reloads em loop e trava as requisições.
- Abrir **http://localhost:4200** (Angular com hot-reload, chamando a API via proxy)
- API sozinha: http://127.0.0.1:8000 — Docs interativas (Swagger): http://127.0.0.1:8000/docs

### 7. Build de produção (um único servidor)
```bash
cd frontend && npm run build   # gera os arquivos em app/static
cd .. && .venv/bin/uvicorn app.main:app
```
- Tudo servido em **http://127.0.0.1:8000** (API + frontend juntos, como o `angular.json` já aponta `outputPath` pra `app/static`)

### 8. Alternativa: rodar tudo com Docker (sem precisar instalar Python/Node local)
O `Dockerfile` faz build multi-stage: compila o Angular (Node) e depois monta a imagem final só com o backend Python + o build do frontend já pronto — um único container, sem precisar de MySQL local (usa o mesmo `.env` com o MySQL remoto).
```bash
docker build -t api-filmes .
docker run -p 8000:8000 --env-file .env api-filmes
```
- Tudo em **http://127.0.0.1:8000**
- Migrations rodam à parte (não são automáticas no start do container):
  ```bash
  docker run --rm --env-file .env api-filmes alembic upgrade head
  ```
- A porta interna do container é sempre 8000; se a plataforma de deploy injetar uma variável `PORT`, o `CMD` do Dockerfile já usa ela automaticamente (`${PORT:-8000}`).

### 9. Rodar os testes
```bash
.venv/bin/pytest -v
```
Os testes usam SQLite em memória (não tocam no MySQL configurado em `.env`) e mockam as chamadas à TMDB — rodam offline. Incluem os testes críticos de isolamento entre usuários: um usuário A não consegue ler, editar ou deletar um favorito/comentário do usuário B mesmo sabendo o ID do recurso (a API responde `404`, nunca `403`, para não vazar a existência do recurso).

## Endpoints

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/auth/register` | não | Cadastra usuário, retorna JWT |
| POST | `/auth/login` | não | Login, retorna JWT |
| GET | `/auth/me` | sim | Dados do usuário logado (nome/email) |
| GET | `/movies` | não | Lista filmes do Tom Hanks (dados ao vivo da TMDB, com sinopse; cache em memória de 5 min) |
| POST | `/favorites` | sim | Favorita um filme |
| GET | `/favorites` | sim | Lista favoritos do usuário logado |
| DELETE | `/favorites/{id}` | sim | Remove um favorito do usuário logado |
| POST | `/comments` | sim | Comenta um filme (envia `titulo` do filme junto) |
| GET | `/comments` | sim | Lista **todos** os comentários do usuário logado |
| GET | `/comments?tmdb_movie_id=` | sim | Lista comentários do usuário logado sobre um filme específico |
| DELETE | `/comments/{id}` | sim | Remove um comentário do usuário logado |

Autenticação via header `Authorization: Bearer <token>`.

## Estrutura do projeto
```
app/
  models/       # SQLAlchemy declarative models
  schemas/      # Pydantic (request/response)
  auth/         # hash de senha, JWT, dependência get_current_user
  routers/      # rotas da API
  services/     # cliente da TMDB (dados sempre ao vivo, client HTTP persistente + cache)
  static/       # build de produção do Angular (gerado por `npm run build`, não editar à mão)
alembic/        # migrations
tests/          # pytest (SQLite em memória + mocks da TMDB)
frontend/       # projeto Angular (standalone components)
  src/app/
    core/       # services (auth/movies/favorites/comments), interceptor de JWT, guards de rota
    layout/     # header (avatar + navegação) e app-shell (layout das rotas privadas)
    shared/     # movie-card (usado no catálogo e nos favoritos, com diálogo de comentários)
    features/   # telas: auth/login, auth/register, catalog, favorites, comments
```

## Notas de segurança / design
- `poster_path` e sinopse dos filmes nunca são persistidos — sempre vêm ao vivo da TMDB a cada chamada a `/movies`. O único dado de filme salvo no banco é o `tmdb_movie_id` (e, em `favoritos`/`comentarios`, uma cópia do título escolhida pelo usuário no momento de favoritar/comentar — só pra exibição, não é cache do catálogo).
- `usuario_id` nunca vem do corpo da requisição — é sempre extraído do JWT.
- Toda query de favoritos/comentários filtra obrigatoriamente por `usuario_id` do usuário logado (`app/routers/_ownership.py`).
- `npm run build` copia `index.html` para `404.html` em `app/static` (truque padrão do Starlette pra SPA): assim, um refresh direto numa rota do Angular (ex: `/favoritos`) ainda carrega o app em vez de um 404 vazio.
