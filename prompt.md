# Projeto: Catálogo de Filmes — Tom Hanks (multi-tenant)

## Contexto
Vou construir uma aplicação web que busca filmes com Tom Hanks na API do TMDB e permite que cada usuário favorite e comente filmes, com isolamento total de dados entre usuários (cada usuário só vê seus próprios favoritos/comentários).

Stack definida:
- **Backend:** Python (FastAPI)
- **ORM:** SQLAlchemy
- **Migrações:** Alembic
- **Banco:** MySQL (já tenho host, usuário e senha — vou passar via variáveis de ambiente / .env)
- **Auth:** login/cadastro próprios da aplicação (não relacionados a usuários do MySQL), com senha com hash (bcrypt/passlib) e JWT para sessão
- **Frontend:** simples (pode ser HTML+JS puro ou um framework leve — sugira o mais rápido de entregar)

## Requisitos funcionais

### 1. Consumo da API TMDB
- Buscar `person_id` do Tom Hanks via `GET /search/person?query=Tom+Hanks`
- Listar filmes via `GET /person/{person_id}/movie_credits`
- Montar URL do pôster: `https://image.tmdb.org/t/p/w500{poster_path}`
- **Importante:** pôster, título e sinopse NUNCA são persistidos no banco — sempre vêm ao vivo da API a cada consulta ao catálogo. Cachear em memória/request é aceitável, persistir em tabela não.
- A chave da API do TMDB deve vir de variável de ambiente (`TMDB_API_KEY`), nunca hardcoded.

### 2. Persistência — MySQL via SQLAlchemy + Alembic
Modele as entidades com SQLAlchemy (declarative models) equivalentes a este esquema (pode adaptar tipos/nomes, mas mantenha a lógica):

```sql
usuarios (id, nome, email UNIQUE, senha_hash, criado_em)
favoritos (id, usuario_id FK, tmdb_movie_id, titulo, poster_path, criado_em, UNIQUE(usuario_id, tmdb_movie_id))
comentarios (id, usuario_id FK, tmdb_movie_id, texto, criado_em)
```

Preciso que você:
- Crie os models em `app/models/`
- Configure o Alembic (`alembic init`, `env.py` apontando para os models e para a `DATABASE_URL` do `.env`, usando driver `mysqlclient` ou `pymysql`)
- Gere a migration inicial criando as três tabelas, incluindo a constraint `UNIQUE (usuario_id, tmdb_movie_id)` em favoritos e as foreign keys
- Configure `SQLALCHEMY_DATABASE_URL` para MySQL (formato `mysql+pymysql://user:pass@host:port/db`)

### 3. Segregação de usuário (multi-tenant a nível de aplicação)
- Login/cadastro próprios do app (não confundir com credenciais do MySQL)
- Toda rota de favoritos/comentários exige usuário autenticado (JWT)
- **Toda query de favoritos/comentários deve filtrar obrigatoriamente por `usuario_id` do usuário logado** — nunca por ID recebido do cliente sem essa checagem
- Escreva pelo menos um teste (pytest) que prove que o usuário A não consegue ler/editar/deletar um favorito ou comentário do usuário B mesmo sabendo o ID do recurso (retornar 404, não 403, para não vazar a existência do recurso)

## Endpoints esperados (sugestão — ajuste como achar melhor)
- `POST /auth/register`
- `POST /auth/login` → retorna JWT
- `GET /movies` → lista filmes do Tom Hanks (dados ao vivo da TMDB)
- `POST /favorites` → favoritar filme (usuario_id vem do token, nunca do body)
- `GET /favorites` → lista favoritos do usuário logado
- `DELETE /favorites/{id}`
- `POST /comments`
- `GET /comments?tmdb_movie_id=...` → comentários do próprio usuário sobre um filme
- `DELETE /comments/{id}`

## Como quero que você trabalhe
1. Primeiro, monte a estrutura de pastas do projeto e me mostre o plano antes de gerar código em massa.
2. Configure `.env.example` com as variáveis necessárias (`DATABASE_URL`, `TMDB_API_KEY`, `JWT_SECRET`), sem valores reais.
3. Implemente na ordem: modelos + Alembic → auth → integração TMDB → favoritos/comentários → testes de isolamento entre usuários.
4. A cada etapa, rode os testes/migrations para validar antes de seguir para a próxima.
5. Ao final, me dê um resumo de como rodar localmente (`alembic upgrade head`, como subir o servidor, como rodar os testes).

