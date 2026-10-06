// ============================================================
//  P1 — Relatório bimestral de atividades (entrega INDIVIDUAL)
//  ISW055 · Introdução à Computação em Nuvem · Fatec Pompeia · 2026.2
//
//  Compilar: typst compile P1_ISW055_Leonardo_Oliveira.typ
//  (os caminhos das imagens são relativos a esta pasta, docs/)
// ============================================================

#import "@preview/fletcher:0.5.8" as fletcher: diagram, node, edge

// ---------- DADOS DO ALUNO (edite aqui) ----------
#let aluno = "Leonardo Ricci Santos Oliveira"
#let turma = "Sistemas Inteligentes"
#let data-relatorio = "06/10/2026"

// ---------- daqui pra baixo, só mexa nas fichas de atividade ----------
#let disciplina = "Introdução à Computação em Nuvem"
#let codigo = "ISW055"
#let professor = "Prof. Allan Lincoln Rodrigues Siriani"
#let accent = rgb("#b96f1f")

#set document(title: "P1 — " + codigo + " — " + aluno, author: aluno)
#set page(paper: "a4", margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2cm))
#set text(size: 11pt, lang: "pt", region: "BR")
#set par(justify: true, leading: 0.7em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => { v(0.6em); text(size: 16pt, it); v(0.2em) }
#show heading.where(level: 2): it => { v(0.5em); text(size: 13pt, it); v(0.1em) }
#show link: set text(fill: accent)
#show figure.caption: set text(size: 9pt, fill: luma(90))
#set table(stroke: 0.5pt + luma(200), inset: 6pt)
#show table: set text(hyphenate: false)
#show table: set par(justify: false)

// ---------- ajudantes ----------
#let orientacao(body) = block(
  width: 100%, fill: luma(245), inset: 9pt, radius: 4pt,
  stroke: (left: 2pt + luma(180)),
  text(size: 9.5pt, fill: luma(90), body),
)

#let evidencia(legenda, arquivo: none) = figure(
  if arquivo == none {
    rect(width: 100%, height: 5.5cm, radius: 4pt, stroke: (paint: luma(170), dash: "dashed"))[
      #align(center + horizon)[
        #text(fill: luma(130), size: 9.5pt)[
          cole o print aqui \
          troque `arquivo: none` por `arquivo: "prints/nome.png"`
        ]
      ]
    ]
  } else {
    image(arquivo, width: 100%)
  },
  kind: image,
  supplement: [Figura],
  caption: legenda,
)

#let registro = state("registro", ())

#let atividade(
  numero, titulo,
  descricao: "",
  planejada: "",
  realizada: "—",
  situacao: "entregue",   // entregue · entregue com atraso · não entregue
  evidencia: "",
  url: "",
  corpo,
) = {
  registro.update(l => l + ((
    numero: numero, titulo: titulo, descricao: descricao,
    planejada: planejada, realizada: realizada, situacao: situacao,
  ),))
  heading(level: 2, [Atividade #numero — #titulo])
  table(
    columns: (3.4cm, 1fr),
    fill: (x, y) => if x == 0 { luma(245) } else { none },
    [*Descrição*], [#descricao],
    [*Data planejada*], [#planejada],
    [*Data realizada*], [#realizada],
    [*Situação*], [#situacao],
    [*Evidência*], [#evidencia],
    [*Link*], [#if url == "" [—] else [#link(url)]],
  )
  corpo
}

// ============================================================
//  CAPA
// ============================================================
#align(center)[
  #v(2.5cm)
  #text(size: 12pt, tracking: 0.12em)[FATEC POMPEIA]
  #v(0.4em)
  #text(size: 10.5pt, fill: luma(110))[#disciplina · #codigo · #turma]
  #v(4.5cm)
  #text(size: 26pt, weight: "bold")[P1]
  #v(0.3em)
  #text(size: 18pt, weight: "bold")[Relatório bimestral de atividades]
  #v(0.8em)
  #text(size: 11pt, fill: luma(110))[Avaliação individual · 2026.2]
  #v(5cm)
  #text(size: 14pt)[#aluno]
  #v(1fr)
  #text(size: 10.5pt)[#professor \ Pompeia, #data-relatorio]
]

#set page(
  numbering: "1",
  number-align: right,
  header: context {
    set text(size: 8pt, fill: luma(120))
    [#codigo · P1 — Relatório bimestral #h(1fr) #aluno]
    line(length: 100%, stroke: 0.4pt + luma(200))
  },
)
#counter(page).update(1)

#outline(title: "Sumário", indent: 1.2em, depth: 2)
#pagebreak()

// ============================================================
= Introdução
// ============================================================

A disciplina Introdução à Computação em Nuvem (ISW055) trata de como uma aplicação deixa de ser um programa que roda na máquina de quem o escreveu e passa a ser um sistema publicado, composto por várias partes independentes que conversam pela rede. Os temas vão do empacotamento em containers (Docker) à separação em serviços, controle de acesso, registro de auditoria, armazenamento de objetos e automação de deploy. A ideia é que cada conceito apareça aplicado num sistema que já existe, e não como exercício isolado.

O fio condutor do bimestre foi um único projeto: um catálogo de filmes do Tom Hanks. Depois de uma atividade de nivelamento em sala (uma agenda telefônica simples em Flask), o catálogo nasceu como uma API FastAPI com frontend Angular, que busca os filmes ao vivo na API pública da TMDB e permite que cada usuário favorite e comente filmes sem enxergar os dados dos outros. A cada atividade o mesmo sistema cresceu: a autenticação virou um microsserviço próprio, os papéis de usuário passaram a decidir permissões no servidor, as ações sensíveis passaram a ser auditadas num serviço de logs com Redis e os usuários ganharam um perfil com foto guardada em object storage. Por fim, nas atividades extras (opcionais e sem prazo), entraram documentação OpenAPI, um pipeline de CI/CD e observabilidade.

Este relatório reúne essas entregas. A Metodologia explica como o trabalho foi feito e de onde saíram as datas. O Quadro de entregas resume, numa tabela, data planejada, data realizada e situação de cada atividade. Em seguida vem uma ficha por atividade, com o que foi construído, as evidências (link do commit e prints) e as dificuldades encontradas. Depois das fichas, uma seção compara as telas do sistema antes e depois das melhorias de interface. O relatório termina com as considerações finais, que trazem um diagrama da arquitetura atual, e a declaração de autoria.

// ============================================================
= Metodologia
// ============================================================

A atividade 1 foi feita em sala e versionada depois no repositório `study_infraestructure`. As atividades 2 a 6 e as extras foram desenvolvidas no mesmo repositório público do GitHub (`leonardoricci-tsi/api_filme_`), como evolução contínua de um único projeto. O ambiente foi o de desenvolvimento local com Docker Compose (catálogo, `auth-service`, `log-service`, Redis e Garage na mesma rede interna) e, a partir da atividade 3, também o servidor da disciplina, gerenciado pelo Portainer (`docker-compose.portainer.yml`). O banco relacional é uma instância MySQL remota fornecida pela disciplina, compartilhada pelo catálogo e pelo `auth-service`. Cada etapa foi feita em commits pequenos, acompanhados de testes automatizados com `pytest`.

As datas e horas de entrega foram extraídas do histórico de commits com `git log -1 --date=format:"%d/%m/%Y %H:%M" --format="%h %ad %s" <hash>` e conferidas na página do commit no GitHub e no arquivo `.patch` que o próprio GitHub serve para cada commit, que mostra a data com fuso horário. Todos os commits usados já estão no fuso de Brasília (-03:00), então não houve conversão; em todos eles a data de autoria coincide com a data do commit. O critério para escolher o commit de cada atividade foi o momento em que a funcionalidade pedida passou a funcionar completa. Commits anteriores (partes da implementação) e posteriores (correções, documentação e evidências) são citados na ficha de cada atividade. A situação compara essa data com a data planejada pelo professor, considerando o prazo até as 23:59 do dia.

As evidências são de dois tipos. O print da entrega mostra a página do commit no GitHub (repositório e hash) junto com o cabeçalho do `.patch` do mesmo commit (hash completo, data e hora). Esse cabeçalho foi incluído porque a página do commit só mostra o dia, e a hora aparece apenas ao passar o mouse sobre a data. O print do resultado mostra o sistema funcionando. Nas atividades 3 a 6 e nas extras, são as capturas feitas na época de cada entrega, já versionadas na pasta `docs/evidencias/` do repositório e copiadas para a pasta `prints/` deste relatório. Os prints de resultado das atividades 1 e 2 e as comparações da seção de UX/UI foram feitos durante a elaboração deste relatório, executando o código de cada versão.

// ============================================================
= Quadro de entregas
// ============================================================

#context {
  let l = registro.final()
  table(
    columns: (auto, 1.4fr, 2fr, 2.6cm, 2.9cm, 2.3cm),
    align: (center, left, left, center, center, center),
    fill: (x, y) => if y == 0 { luma(235) } else { none },
    table.header([*Nº*], [*Atividade*], [*Descrição*], [*Data \ planejada*], [*Data \ realizada*], [*Situação*]),
    ..l.map(a => (
      [#a.numero], [#a.titulo], [#text(size: 9pt)[#a.descricao]],
      [#a.planejada], [#a.realizada], [#a.situacao],
    )).flatten()
  )
}

// ============================================================
= Atividades realizadas
// ============================================================

#atividade(
  "1", "Agenda telefônica em Flask",
  descricao: "Nivelamento em sala: sistema monolítico Flask + Jinja com persistência em JSON.",
  planejada: "07/08/2026",
  realizada: "Em sala (versionada em 14/08/2026 19:59)",
  situacao: "entregue",
  evidencia: "Realizada em sala — print do sistema rodando localmente; código versionado depois no GitHub (commit 527ebdb)",
  url: "https://github.com/leonardoricci-tsi/study_infraestructure/commit/527ebdb",
)[
  *O que foi feito.* Uma agenda monolítica em Flask, num único arquivo (`app.py`). A rota `/` mostra um formulário (nome, telefone e valor) e a lista de cadastros, renderizada com um template Jinja embutido no código (`render_template_string`). Os registros são gravados num arquivo `dados.json`, sem banco de dados. Há também duas rotas JSON, `POST /salvar` e `GET /listar`, que fazem o mesmo trabalho para um cliente que não seja o navegador. A rota `/` aceita tanto formulário HTML quanto JSON, e a listagem acrescenta um campo `enderecos` aos registros antigos que ainda não o tinham.

  A atividade foi feita em sala. O código foi enviado ao GitHub depois, em 14/08/2026 às 19:59 (commit `527ebdb`, único do repositório), numa época em que versionar a atividade ainda não era obrigatório. A evidência da entrega é o sistema rodando.

  #evidencia([Atividade 1 — commit 527ebdb no GitHub (repositório, hash, data e hora)], arquivo: "prints/a1-commit.png")
  #evidencia([Atividade 1 — agenda rodando localmente (formulário e lista de cadastros)], arquivo: "prints/a1-resultado.png")

  *Dificuldades e como foram resolvidas.* A maior dificuldade foi juntar back-end, front-end e banco de dados ao mesmo tempo num código monolítico e fazer as três partes funcionarem de forma coordenada. Resolvi isso concentrando tudo em `app.py` e separando as responsabilidades em funções pequenas. `carregar_dados()` e `salvar_dados()` são a única porta de entrada para o arquivo `dados.json`, que faz o papel de banco. O HTML é um template Jinja dentro do próprio código, renderizado com `render_template_string`. A mesma rota `/` atende tanto o formulário do navegador quanto requisições JSON (`request.is_json`), e as rotas `/salvar` e `/listar` reaproveitam as mesmas funções de leitura e gravação. Assim, todas as partes passam pelo mesmo caminho até os dados.
]

#atividade(
  "2", "Catálogo de filmes — Tom Hanks",
  descricao: "Consumo da API TMDB, persistência em MariaDB e segregação por usuário.",
  planejada: "20/08/2026",
  realizada: "16/08/2026 19:09",
  situacao: "entregue",
  evidencia: "GitHub — commit + README mencionando github.com/siriani (desde b1bdb48) + print do catálogo",
  url: "https://github.com/leonardoricci-tsi/api_filme_/commit/4999e4e",
)[
  *O que foi feito.* Uma API em FastAPI com SQLAlchemy e Alembic e um frontend Angular (componentes standalone), empacotados num Dockerfile multi-stage: o build do Angular é servido como arquivo estático pelo próprio FastAPI. Os filmes do Tom Hanks vêm sempre ao vivo da TMDB e nunca são gravados no banco. O banco guarda só o que é do usuário: conta, favoritos e comentários. O cadastro e o login usam senha com hash `bcrypt` e sessão por JWT. O isolamento entre usuários é feito no backend: toda consulta de favoritos e comentários é filtrada pelo `usuario_id` extraído do token, e tentar mexer num registro de outra pessoa é recusado (`app/routers/_ownership.py`). O crédito ao professor (github.com/siriani) foi adicionado ao README no commit `b1bdb48`, às 19:14 do mesmo dia.

  Em vez de MariaDB, o projeto usa a instância MySQL remota que a disciplina fornece a cada aluno (driver `pymysql`, `DATABASE_URL=mysql+pymysql://...`). Os dois bancos são compatíveis no SQL usado pelo SQLAlchemy e pelas migrations, e o `docker-compose.yml` não sobe nenhum container de banco. O `/health` público de produção mostra a checagem do MySQL (última figura desta ficha).

  #evidencia([Atividade 2 — commit 4999e4e no GitHub (repositório, hash, data e hora)], arquivo: "prints/a2-commit.png")
  #evidencia([Atividade 2 — resultado: catálogo de filmes do Tom Hanks com usuário logado (filme favoritado em destaque)], arquivo: "prints/a2-resultado.png")
  #evidencia([Atividade 2 — `GET /health` em produção: checagem do MySQL remoto (crítica) com status ok], arquivo: "prints/a2-mysql-health.png")
  #evidencia([README do repositório com a menção ao professor (github.com/siriani), presente desde o commit b1bdb48 (16/08/2026 19:14)], arquivo: "prints/readme-siriani.png")

  *Dificuldades e como foram resolvidas.* A atividade juntou integração com a TMDB, autenticação com JWT, migrations e deploy. O mais difícil foram as migrations com Alembic: eu não conhecia a biblioteca e precisei estudar o essencial para criar e aplicar as migrations. Configurei o `alembic/env.py` para ler a `DATABASE_URL` das mesmas configurações da aplicação (`get_settings()`) e para usar os modelos do SQLAlchemy como referência (`target_metadata = Base.metadata`). Assim, o esquema do banco nasce dos modelos, sem SQL escrito à mão. A primeira migration (`6c7cac7f3161_initial_schema.py`) cria `usuarios`, `favoritos` e `comentarios`, com a restrição `UNIQUE(usuario_id, tmdb_movie_id)` em `favoritos`. Depois vieram duas migrations incrementais (`9286b70fe465` e `ac04bc85ee9c`, que adicionam `poster_path` e `titulo` em `comentarios`), o que mostra o fluxo de evoluir o banco sem recriá-lo. Para o deploy, as migrations não rodam sozinhas na subida do container: são aplicadas com `alembic upgrade head`, localmente ou com `docker run --rm --env-file .env api-filmes alembic upgrade head`, como documentado no README. A partir da atividade 3, esse passo virou o serviço `migrate` do `docker-compose.yml`.
]

#atividade(
  "3", "Desacoplando o login — microsserviço de autenticação",
  descricao: "Login, cadastro e esqueci-minha-senha num serviço à parte na rede interna do Docker.",
  planejada: "28/08/2026",
  realizada: "27/08/2026 17:15",
  situacao: "entregue",
  evidencia: "GitHub — commit + docker-compose.yml + print do login funcionando (e do fluxo de recuperação de senha)",
  url: "https://github.com/leonardoricci-tsi/api_filme_/commit/499cb42",
)[
  *O que foi feito.* A autenticação saiu do catálogo e virou o `auth-service/`, também em FastAPI. Ele cuida de cadastro, login, papel do usuário e recuperação de senha. No `docker-compose.yml` ele não tem `ports:`, só `expose: "8001"`, então só é alcançável pela rede interna `catalog-net`, pelo nome `http://auth-service:8001`. O catálogo continua sendo o único ponto de entrada público: toda rota `/auth/*` chega nele e é repassada internamente (`app/services/auth_client.py`). Nas demais rotas o catálogo não consulta o `auth-service`: o JWT é assinado por ele e verificado localmente pelo catálogo, com o mesmo `JWT_SECRET`, o que evita uma ida pela rede a cada requisição.

  A recuperação de senha gera um token aleatório (`secrets.token_urlsafe(32)`) com validade de 30 minutos e uso único, gravado na tabela `reset_tokens`. O link é enviado por e-mail via SMTP (Mailtrap em desenvolvimento). O pedido sempre devolve a mesma mensagem, exista ou não o e-mail, para não revelar quais e-mails têm conta. A entrega foi feita em etapas: `bd536aa` (docker compose), `72a259b` (scaffold do serviço), `db99632` (catálogo vira proxy), `2064573` e `258405e` (token de redefinição), `f21f1c2` (rotas no catálogo), `f307bb0` (envio real de e-mail) e `499cb42` (telas do Angular), commit em que o fluxo passou a funcionar de ponta a ponta. README e evidências vieram em `4ecfbcf`, às 17:26 do mesmo dia.

  #evidencia([Atividade 3 — commit 499cb42 no GitHub (repositório, hash, data e hora)], arquivo: "prints/a3-commit.png")
  #evidencia([Atividade 3 — `docker-compose.yml` no commit 499cb42: o catálogo (`api`) publica a porta; o `auth-service` só tem `expose: "8001"`, na rede `catalog-net`], arquivo: "prints/a3-docker-compose.png")
  #evidencia([Atividade 3 — login funcionando em produção: credenciais enviadas ao catálogo, repassadas ao `auth-service`, e usuário autenticado], arquivo: "prints/a3-login.jpg")
  #evidencia([Atividade 3 — e-mail de redefinição de senha recebido no Mailtrap], arquivo: "prints/email-recebido.png")
  #evidencia([Atividade 3 — link reutilizado é recusado (token de uso único)], arquivo: "prints/link-reutilizado-recusado.png")

  *Dificuldades e como foram resolvidas.* O login, que fazia parte do monolito, foi separado num container Docker próprio, e implementei o fluxo de "esqueci minha senha" com envio de e-mail. A parte mais complicada foi integrar o Brevo ao código via SMTP, o que exigiu pesquisar como fazer essa integração. A solução foi não amarrar o código a nenhum provedor: `auth-service/app/services/mailer.py` usa a biblioteca padrão do Python (`smtplib`), abre a conexão, ativa a criptografia com `starttls()`, faz login e envia a mensagem montada com `EmailMessage`. Host, porta, usuário, senha e remetente vêm de variáveis de ambiente (`SMTP_*` em `auth-service/app/config.py`). Em desenvolvimento elas apontam para o Mailtrap, e em produção as mesmas variáveis, cadastradas na stack do Portainer (`docker-compose.portainer.yml`), apontam para o Brevo, sem mudar nenhuma linha de código. Uma falha de envio é registrada no log do container e não derruba a requisição, e a resposta ao usuário é sempre a mesma mensagem genérica. Outro ponto foi o banco: como a disciplina fornece um único banco por aluno, o `auth-service` reaproveita a mesma instância MySQL com um histórico de migrations próprio, numa tabela de versão separada (`VERSION_TABLE` em `auth-service/alembic/env.py`).
]

#atividade(
  "4", "Controle de acesso por papel — RBAC",
  descricao: "O campo role passa a decidir permissões reais no backend (403 para usuário comum).",
  planejada: "04/09/2026",
  realizada: "02/09/2026 17:25",
  situacao: "entregue",
  evidencia: "GitHub — commit + print do 403 e da ação de admin",
  url: "https://github.com/leonardoricci-tsi/api_filme_/commit/bd02f64",
)[
  *O que foi feito.* Quatro papéis em escada, cada um incluindo as permissões do anterior: `cinefilo` (padrão no cadastro; só vê o catálogo), `nerd` (comenta e favorita), `stalker_do_tomhanks` (joga o quiz do pôster pixelado) e `admin`. Só o admin pode apagar comentários e favoritos de qualquer usuário e listar, promover e rebaixar usuários. A decisão é sempre do servidor. `require_papel_minimo` compara o nível do papel (`NIVEL_PAPEL`) e `require_admin` exige o papel exato. Os dois leem o claim `role` do JWT localmente (Padrão B), e quem não tem o papel recebe `403` mesmo chamando a API direto por curl ou Postman. A gestão de usuários fica no `auth-service`, que é o dono da tabela `usuarios` e faz a própria checagem de admin. O quiz confere a resposta só no servidor, usando um `round_id` assinado que o cliente não consegue forjar.

  Sequência no histórico, toda em 02/09: `349be5b` (papéis), `a472aa2` (moderação e gestão de papéis com `403` no backend, mais os testes em `tests/test_admin.py`), `2652d1b` (quiz), `8f4ee59` (README e prints do 403 e do 200), `a50ae97` e `047ca7f` (papéis e quiz no frontend), `d247b73` (correção) e `bd02f64` (painel de admin), que fecha a atividade.

  #evidencia([Atividade 4 — commit bd02f64 no GitHub (repositório, hash, data e hora)], arquivo: "prints/a4-commit.png")
  #evidencia([Atividade 4 — usuário comum recebe 403 ao tentar uma ação de admin], arquivo: "prints/rbac-403-comum.png")
  #evidencia([Atividade 4 — a mesma ação executada com sucesso pelo admin (200)], arquivo: "prints/rbac-200-admin.png")

  *Dificuldades e como foram resolvidas.* O desafio principal foi definir as regras de negócio: pensar nas particularidades de cada papel, no que cada um pode fazer e em todos os cenários que poderiam dar certo ou errado. Resolvi primeiro organizando os papéis numa escada (`NIVEL_PAPEL = {"cinefilo": 1, "nerd": 2, "stalker_do_tomhanks": 3, "admin": 4}` em `app/auth/dependencies.py`). Assim, uma rota que exige `nerd` libera automaticamente os papéis acima dele (`require_papel_minimo`). As ações que são só de admin usam uma segunda regra, `require_admin`, que exige o papel exato. Os cenários viraram testes automatizados, tanto os casos que devem dar certo quanto os que devem ser barrados: `tests/test_roles.py` (`cinefilo` não comenta nem favorita; `nerd`, `stalker_do_tomhanks` e `admin` sim), `tests/test_admin.py` (usuário comum recebe `403` nas rotas de moderação; admin lista e apaga dados de qualquer usuário e promove usuários) e `tests/test_quiz.py` (`cinefilo` e `nerd` não acessam o quiz; `stalker_do_tomhanks` e `admin` sim; `round_id` inválido é recusado). As regras ficaram documentadas numa tabela no README. Na implementação, também precisei corrigir campos que faltaram no commit da tela do quiz (`d247b73`) e o proxy de desenvolvimento do Angular para as rotas novas (`a50ae97`).
]

#atividade(
  "5", "Logs e auditoria",
  descricao: "Novo log-service com Redis registrando login, ações sensíveis e tentativas negadas.",
  planejada: "25/09/2026",
  realizada: "25/09/2026 13:49",
  situacao: "entregue",
  evidencia: "GitHub — commit + print da consulta de logs pelo admin",
  url: "https://github.com/leonardoricci-tsi/api_filme_/commit/08359fc",
)[
  *O que foi feito.* Um microsserviço novo, o `log-service/`, grava eventos de auditoria num Redis Stream (`XADD` para gravar, `XREVRANGE` para consultar). Nem ele nem o Redis têm porta publicada. Catálogo e `auth-service` nunca escrevem no Redis diretamente: mandam um `POST /logs` para o `log-service` de forma fire-and-forget, com timeout curto, para que uma queda do serviço de log não quebre a ação do usuário. São auditados login, logout, favoritar, comentar, apagar comentário por moderação e toda tentativa negada por permissão (`acesso_negado:{papel}`). Essa última é registrada dentro das próprias dependências do RBAC, o que cobre todas as rotas protegidas de uma vez. Cada evento tem `usuario_id`, `acao`, `timestamp` (gerado pelo `log-service`) e `ip`.

  A consulta (`GET /logs`) exige admin. Como o `log-service` não é público, o catálogo oferece `GET /admin/logs`: barra com `403` quem não é admin e repassa o token original para o `log-service`, que confere de novo. O serviço veio em `ae6ba68` (12:33), os eventos e a consulta em `08359fc` (13:49), a documentação e as evidências em `8d6049c` (14:10) e o Redis e o `log-service` foram adicionados à stack do Portainer em `bb7ca67` (14:45).

  #evidencia([Atividade 5 — commit 08359fc no GitHub (repositório, hash, data e hora)], arquivo: "prints/a5-commit.png")
  #evidencia([Atividade 5 — admin consultando o log de auditoria], arquivo: "prints/auditoria-consulta-admin.png")

  *Dificuldades e como foram resolvidas.* Implementei os logs de auditoria com o Redis num container próprio, registrando ações sensíveis e tentativas de acesso negadas. O desafio foi fazer esse registro funcionar de forma confiável sem sobrecarregar o sistema nem comprometer o funcionamento dele. Resolvi em quatro frentes. A primeira é o envio fire-and-forget: `registrar_evento()` em `app/services/log_client.py` manda o evento ao `log-service` com timeout curto (5 s) e engole qualquer erro, então favoritar, comentar ou logar nunca falham porque o serviço de log caiu. A segunda é o custo: o cliente HTTP é criado uma vez e reaproveitado entre as requisições, e o Redis Streams grava cada evento com um `XADD`, operação feita para escrita rápida e em alto volume. A terceira é a cobertura sem duplicar código: as tentativas negadas são registradas dentro de `require_admin` e `require_papel_minimo`, então todas as rotas protegidas ficam cobertas de uma vez. A quarta é a durabilidade: o Redis grava num volume (`redis-data:/data` no `docker-compose.yml`), então os eventos sobrevivem a um reinício do container. O comportamento está coberto em `tests/test_audit_log.py`.
]

#atividade(
  "6", "Upload e perfil de usuário",
  descricao: "Página de perfil com avatar no MinIO; só a referência fica no banco relacional.",
  planejada: "02/10/2026",
  realizada: "29/09/2026 20:37",
  situacao: "entregue",
  evidencia: "GitHub — commit + print do perfil com foto",
  url: "https://github.com/leonardoricci-tsi/api_filme_/commit/a8a6aae",
)[
  *O que foi feito.* Cada usuário tem uma página de perfil com nome, foto, bio e filmes favoritados. A foto vai para um object storage compatível com S3 e o MySQL guarda só a chave do objeto (`perfis.foto_key`). No lugar do MinIO foi usado o Garage, troca liberada pelo professor porque a edição community do MinIO foi arquivada. O código usa `boto3` como em qualquer S3. O upload é validado pelos bytes do arquivo com Pillow, e não pela extensão: até 2 MB (`413` acima disso), só JPEG, PNG e WEBP (`415` para o resto) e limite de pixels contra decompression bomb. A imagem é reduzida e salva de novo, o que descarta metadados EXIF como a localização GPS. A exibição usa URL pré-assinada válida por 15 minutos, e o bucket nunca fica público. Só o dono edita o próprio perfil: `require_dono_do_perfil` compara o ID da URL com o `sub` do JWT, devolve `403` para qualquer outro, inclusive admin, e registra a tentativa no log de auditoria.

  Etapas: `6ad4ca1` (Garage e cliente S3) e `575dead` (perfis) em 25/09, depois `be10862` (upload com validação) e `b2157be` (tela de perfil) em 29/09. O commit escolhido, `a8a6aae`, faz a foto aparecer em produção: o catálogo passa a assinar as URLs com o próprio domínio e a repassá-las ao Garage (`app/routers/storage_proxy.py`), além de colocar o Garage no Portainer e adicionar as evidências. Depois vieram `a8c1a2a` (correção na documentação) e `bb1a8a9` (foto no avatar do cabeçalho, 30/09).

  #evidencia([Atividade 6 — commit a8a6aae no GitHub (repositório, hash, data e hora)], arquivo: "prints/a6-commit.png")
  #evidencia([Atividade 6 — perfil com foto enviada ao Garage], arquivo: "prints/perfil-com-foto.png")
  #evidencia([Atividade 6 — 403 ao tentar editar o perfil de outro usuário], arquivo: "prints/perfil-403-outro-usuario.png")

  *Dificuldades e como foram resolvidas.* Para guardar as imagens, tentei primeiro o MinIO, mas não funcionou, então migrei para o Garage num container dedicado (com autorização do professor). As tentativas com o MinIO ficaram só no meu ambiente local e não chegaram a ser commitadas. O mais complicado foi a diferença entre HTTP e HTTPS e entre portas: o servidor só libera a porta do catálogo (HTTPS), o Garage fala HTTP na rede interna e uma página HTTPS não carrega imagem de um endereço HTTP. A solução foi usar dois clientes S3 em `app/services/storage.py`. Um fala com o Garage pela rede interna (`S3_ENDPOINT_URL`). O outro só assina as URLs pré-assinadas com o domínio público do catálogo (`S3_PUBLIC_URL`, assinatura `s3v4` e endereçamento por caminho). O navegador pede a foto ao próprio catálogo, e `app/routers/storage_proxy.py` repassa o pedido ao Garage com o caminho e a query exatamente como chegaram e com o mesmo `Host` que entrou na assinatura. Assim, quem valida a assinatura e a expiração continua sendo o Garage, e ele segue sem porta publicada. Também descartei a opção de bucket público, porque o Garage não tem bucket policy, e corrigi a documentação quando vi que uma URL expirada devolve `400`, e não `403` (`a8c1a2a`).
]

// ============================================================
= Atividades extras (opcional)
// ============================================================

#atividade(
  "E1", "Documentação Swagger/OpenAPI",
  descricao: "Swagger UI com pelo menos 2 serviços documentados e “Try it out” executado.",
  planejada: "sem prazo",
  realizada: "25/09/2026 15:04",
  situacao: "entregue",
  evidencia: "Repositório público no GitHub — commit com data e hora, README mencionando github.com/siriani (print na ficha da atividade 2), Swagger UI do catálogo e do auth-service, “Try it out” executado",
  url: "https://github.com/leonardoricci-tsi/api_filme_/commit/e480256",
)[
  *O que foi feito.* Os três serviços (catálogo, `auth-service` e `log-service`) são FastAPI, então o Swagger UI e a spec OpenAPI já existiam. Esta atividade documentou os erros: por padrão o FastAPI só descreve a resposta de sucesso, e cada `401`, `403`, `404`, `409` ou `502` aparecia como "Undocumented". Agora cada rota declara `responses=` com descrição e exemplo do erro que de fato levanta (`app/openapi_responses.py` e equivalentes nos outros serviços). O Swagger do catálogo é público em produção (`/docs`). Os do `auth-service` e do `log-service`, que não têm porta publicada, foram exportados para `docs/openapi/auth-service.json` e `docs/openapi/log-service.json`. Executando o `auth-service` localmente, o Swagger UI dele fica disponível em `localhost:8001/docs`.

  #evidencia([Extra E1 — commit e480256 no GitHub (repositório, hash, data e hora)], arquivo: "prints/e1-commit.png")
  #evidencia([Extra E1 — “Try it out” executado no Swagger público: 403 real, documentado], arquivo: "prints/swagger-try-it-out.png")
  #evidencia([Extra E1 — Swagger UI do `auth-service` (segundo serviço documentado), executado localmente em `localhost:8001/docs`], arquivo: "prints/e1-swagger-auth-service.png")

  *Dificuldades e como foram resolvidas.* Foi a atividade mais tranquila, porque eu já tinha experiência com FastAPI, que gera a documentação OpenAPI nativamente. A única dificuldade foi detalhar e organizar bem a documentação dos endpoints, principalmente os erros, que o FastAPI não documenta sozinho. Resolvi isso criando um módulo com as respostas de erro reutilizáveis (`app/openapi_responses.py`, com equivalentes no `auth-service` e no `log-service`), com descrição e exemplo de payload iguais ao `detail` que o código realmente devolve, e aplicando esses blocos em cada rota com `responses=`. Assim, o mesmo erro fica descrito do mesmo jeito em todas as rotas, sem repetir o mesmo dicionário. Os dois serviços internos não têm Swagger acessível de fora, então exportei a spec deles para `docs/openapi/`.
]

#atividade(
  "E2", "CI/CD com GitHub Actions",
  descricao: "Pipeline que testa e faz deploy a cada push.",
  planejada: "sem prazo",
  realizada: "30/09/2026 15:34",
  situacao: "entregue",
  evidencia: "Repositório público no GitHub — commit com data e hora, README mencionando github.com/siriani (print na ficha da atividade 2), .github/workflows/ci.yml, print do deploy automático",
  url: "https://github.com/leonardoricci-tsi/api_filme_/commit/e424517",
)[
  *O que foi feito.* O workflow `.github/workflows/ci.yml` roda a cada push: testes do catálogo e do `log-service` (`pytest`), build das quatro imagens Docker e um smoke test que sobe a stack inteira com um MySQL descartável, roda as migrations do zero e executa `scripts/smoke-test.sh` (cadastro, login, upload de foto, `403` no perfil alheio, eventos de auditoria). Se tudo passa e o push é na `main`, as imagens são publicadas no GHCR com a tag do commit (`sha-xxxxxxx`), e o job de deploy faz um commit do robô (`deploy: sha-... [skip ci]`) atualizando o `docker-compose.portainer.yml`. A stack no Portainer é ligada ao repositório por GitOps e coloca a nova versão no ar sozinha. Etapas: `63dd054` (testes e build), `2a42d76` (smoke test), `8c6671e` (GHCR) e `e424517` (deploy GitOps). Documentação e evidência em `7b185e1` e `fdfed9f`.

  #evidencia([Extra E2 — commit e424517 no GitHub (repositório, hash, data e hora)], arquivo: "prints/e2-commit.png")
  #evidencia([Extra E2 — deploy automático executado pelo pipeline], arquivo: "prints/cicd-deploy-automatico.png")

  *Dificuldades e como foram resolvidas.* Foi a atividade em que tive mais dificuldade: comandos, scripts de deploy automático e GitHub Actions eram ferramentas novas para mim, e precisei aprender tudo do zero para montar o pipeline. Resolvi construindo o workflow em etapas, uma por commit (`63dd054`, `2a42d76`, `8c6671e` e `e424517`), cada uma dependendo da anterior por `needs:` em `.github/workflows/ci.yml`. A ordem é: testes do catálogo e do `log-service`, depois o build das imagens, o smoke test, a publicação e o deploy. O smoke test sobe a stack inteira com `docker-compose.ci.yml` e um MySQL descartável e roda `scripts/smoke-test.sh` contra ela. As imagens são construídas para `linux/amd64`, a arquitetura do servidor, diferente do meu computador, e publicadas no GHCR usando o `GITHUB_TOKEN` do próprio Actions, sem segredo extra. O deploy usa `sed` para trocar a tag das imagens no `docker-compose.portainer.yml` e faz um commit do robô com `[skip ci]`, que o Portainer, ligado ao repositório por GitOps, aplica sozinho. As migrations continuam manuais em produção, para não dar ao GitHub acesso ao banco.
]

#atividade(
  "E3", "Observabilidade — health checks e métricas",
  descricao: "Endpoints de saúde e métricas, com o container reagindo à queda do Redis.",
  planejada: "sem prazo",
  realizada: "30/09/2026 18:29",
  situacao: "entregue",
  evidencia: "Repositório público no GitHub — commit com data e hora, README mencionando github.com/siriani (print na ficha da atividade 2), print do container unhealthy com o Redis fora e do painel do Grafana",
  url: "https://github.com/leonardoricci-tsi/api_filme_/commit/24b40b2",
)[
  *O que foi feito.* Cada serviço tem `GET /health/live` (liveness: o processo responde) e `GET /health` (readiness: testa as dependências e devolve `503` se uma crítica cair). No `log-service`, a dependência crítica é o Redis: com ele fora, o `/health` devolve `503` e o `HEALTHCHECK` do Docker marca o container como `unhealthy`. Quando o Redis volta, o container volta a `healthy`. No catálogo, só o MySQL é crítico; Garage, `auth-service` e `log-service` deixam o status `degraded` sem derrubar o serviço. Os três serviços expõem métricas Prometheus (`prometheus-fastapi-instrumentator`) numa porta interna, `9100`, não publicada. No compose local, um Prometheus e um Grafana com painel provisionado pelo repositório mostram requisições por minuto, taxa de erro e latência p95. Etapas: `b37a746` (health checks), `72ca482` (`HEALTHCHECK` no Docker), `dc4cf20` (métricas) e `24b40b2` (Prometheus e Grafana). Documentação em `5c20d35`.

  #evidencia([Extra E3 — commit 24b40b2 no GitHub (repositório, hash, data e hora)], arquivo: "prints/e3-commit.png")
  #evidencia([Extra E3 — com o Redis parado, o log-service aparece como unhealthy no Portainer (produção)], arquivo: "prints/obs-docker-ps-redis-fora.png")
  #evidencia([Extra E3 — painel do Grafana provisionado pelo repositório], arquivo: "prints/obs-grafana-painel.png")

  *Dificuldades e como foram resolvidas.* Health checks e métricas com Grafana eram funcionalidades que eu nunca tinha implementado. O desafio foi pesquisar como fazer e qual a melhor forma de integrar isso a um sistema que já estava quase completo. Escolhi abordagens que não exigiam mexer nas rotas existentes. Os health checks ficaram em routers novos (`app/routers/health.py` e equivalentes nos outros serviços), que testam cada dependência e separam o que é crítico (MySQL no catálogo e no `auth-service`, Redis no `log-service`) do que não é. As métricas vieram do `prometheus-fastapi-instrumentator`, que se acopla à aplicação inteira em `app/main.py` sem alterar cada endpoint. Nele eu excluí o `/health` da contagem e ajustei as faixas do histograma para 10 ms a 5 s, porque as faixas padrão davam um p95 inútil com a latência do MySQL remoto. O `/metrics` fica numa porta interna separada (`start_http_server`, porta 9100) para não ficar exposto na internet. O `HEALTHCHECK` de cada container usa Python (`urllib`), porque as imagens slim não têm `curl`. O Prometheus e o Grafana são provisionados por arquivos do repositório (`observabilidade/prometheus/prometheus.yml` e `observabilidade/grafana/provisioning/`), sem configuração manual pela interface.
]

// ============================================================
= Melhorias de UX/UI
// ============================================================

Além das funcionalidades pedidas em cada atividade, fui melhorando a interface do catálogo (Angular) ao longo do bimestre. A primeira versão do frontend era funcional, mas genérica: telas escuras com um formulário centralizado, sem identidade visual, e com o catálogo como única tela depois do login. As mudanças se concentraram em três commits de 29/08/2026 (`03daeaa`, `90d6ea7` e `6690ec0`) e foram complementadas depois pelo menu do usuário com papel e foto (`687aab5`, `b2157be` e `bb1a8a9`).

Para as comparações abaixo, executei localmente o código do commit `687aab5` (27/08/2026, último antes da reformulação visual), com o backend daquela época e o mesmo banco de dados. Os prints "depois" são da versão atual em produção. Os dois lados usam a mesma conta de teste e os mesmos dados ao vivo da TMDB, então a diferença que aparece é só a da interface.

== Página inicial pública

Antes, quem abria o site caía direto na tela de login, sem saber do que se tratava o sistema. Em `03daeaa` criei uma landing page pública (`features/landing/`), com uma chamada principal, botões "Criar conta grátis" e "Já tenho conta", cards explicando o que o catálogo oferece (catálogo completo, favoritos e comentários) e a seção "Escolha o seu nível de fã", que apresenta os papéis do sistema como planos. Os guards de rota foram ajustados para que o visitante veja essa página antes do login.

#figure(image("prints/ux-entrada.jpg", width: 100%), kind: image, supplement: [Figura], caption: [UX/UI — entrada do site: antes ia direto para o login; depois, landing page pública])

== Identidade visual e telas de login e cadastro

Em `90d6ea7` criei a identidade visual do projeto: logotipo próprio em SVG (`logo.svg`, `logo-icon.svg`, `logo-claquete.svg` e `logo-faixa.svg` em `frontend/public/`), usado no cabeçalho, nas telas de autenticação e como ícone da aba. As telas de login, cadastro, esqueci minha senha e redefinir senha ganharam um fundo ilustrado de sala de cinema (`fundo-login.svg`), campos com ícone, botão principal na cor de destaque (dourado) e o link "Esqueci minha senha" junto do campo de senha, onde o usuário procura por ele. Os estilos foram centralizados em `auth-shared.css`, para que as quatro telas fiquem consistentes.

#figure(image("prints/ux-login.jpg", width: 100%), kind: image, supplement: [Figura], caption: [UX/UI — tela de login antes e depois da identidade visual])

#figure(image("prints/ux-cadastro.jpg", width: 100%), kind: image, supplement: [Figura], caption: [UX/UI — tela de cadastro antes e depois])

== Catálogo: busca, paginação e filmes sem pôster

Em `6690ec0` o catálogo ganhou um campo de busca por título e paginação (botões "Anterior" e "Próxima" e números de página), que antes não existiam: todos os filmes eram carregados de uma vez. Os filmes sem pôster, que antes apareciam misturados como um card vazio ("Sem pôster"), passaram a ir para o fim da lista. Os cards ficaram mais limpos: o botão "Comentários" saiu de cada card, porque o card inteiro passou a ser clicável, e ficou só o botão de favoritar, que muda de cor quando o filme já é favorito.

#figure(image("prints/ux-catalogo.jpg", width: 100%), kind: image, supplement: [Figura], caption: [UX/UI — catálogo antes e depois: busca, cabeçalho com a marca e cards simplificados])

== Detalhes do filme

Antes, o botão "Comentários" abria um diálogo simples, só com os comentários e um campo de texto. Também no commit `6690ec0`, clicar no card passou a abrir um modal de detalhes com pôster, nota, sinopse completa e três abas: Comentários (agora com o nome de quem comentou), Onde assistir e Elenco. O modal pode ser fechado pelo botão de fechar (X) ou clicando fora dele, e o card também abre com a tecla Enter, o que ajuda quem navega pelo teclado.

#figure(image("prints/ux-detalhe.jpg", width: 100%), kind: image, supplement: [Figura], caption: [UX/UI — detalhes do filme: antes só comentários; depois, modal com sinopse, nota e abas])

== Menu do usuário

O menu aberto pelo avatar no cabeçalho passou a mostrar o papel do usuário como uma etiqueta (`687aab5`, adaptada aos novos papéis da atividade 4) e ganhou o atalho "Meu perfil", que leva à página de perfil criada na atividade 6 (`b2157be`). Em `bb1a8a9`, o avatar passou a exibir a foto de perfil do usuário quando ele tem uma, em vez de só a inicial do nome.

#figure(image("prints/ux-menu.jpg", width: 100%), kind: image, supplement: [Figura], caption: [UX/UI — menu do usuário: depois, com o papel atualizado e o atalho para o perfil])


// ============================================================
= Considerações finais
// ============================================================

O bimestre mostrou na prática a diferença entre um programa que funciona na própria máquina e um sistema publicado. O mesmo catálogo passou por separação em serviços, controle de acesso no servidor, auditoria, object storage e automação de deploy, e cada passo exigiu uma decisão de arquitetura explícita: o que fica público, quem é dono de cada dado, o que é crítico e o que pode falhar sem derrubar o resto.

A parte mais difícil foi lidar com as restrições do ambiente real: um único banco por aluno, um único domínio HTTPS no servidor e a diferença de arquitetura entre o computador de desenvolvimento e o servidor. Para o próximo bimestre, fica o hábito de documentar as decisões junto com o código e de automatizar a verificação desde o início.

Durante o bimestre, tivemos contato com diversas tecnologias, como Docker, FastAPI, Redis, object storage compatível com S3, GitHub Actions, Prometheus e Grafana, e pudemos entender o funcionamento de cada ferramenta. Nesse processo, as ferramentas de IA generativa ajudaram no desenvolvimento: deixaram mais rápido o estudo de bibliotecas que eu não conhecia, a pesquisa de soluções e a revisão do código. Assim, conseguimos ampliar o leque de oportunidades e de conhecimentos para os próximos desafios.


O diagrama abaixo mostra como a aplicação está hoje, ao fim do bimestre. O navegador só fala com o catálogo, por HTTPS, e todos os outros serviços ficam na rede interna do Docker, sem porta publicada. O MySQL é a instância remota da disciplina, fora da stack, e o Prometheus e o Grafana rodam só no ambiente local. Embaixo está o caminho de cada mudança até a produção: o push dispara o GitHub Actions, as imagens vão para o GHCR e o Portainer aplica a versão nova.

#let svc(pos, nome, det, name: none, fill: rgb("#fdf6ec"), stroke: 0.7pt + accent, dash: none) = node(
  pos, align(center)[#text(weight: "bold", size: 8.5pt)[#nome] \ #text(size: 7pt, fill: luma(80))[#det]],
  name: name, fill: fill, stroke: if dash == none { stroke } else { (paint: luma(120), thickness: 0.7pt, dash: dash) },
  corner-radius: 3pt, inset: 5pt, width: 2.7cm,
)
#let ext(pos, nome, det, name: none) = svc(pos, nome, det, name: name, fill: luma(245), stroke: 0.7pt + luma(150))

#figure(
  {
    set text(size: 7pt, hyphenate: false)
    set par(justify: false)
    align(center, scale(92%, reflow: true, diagram(
      spacing: (3mm, 9mm),
      edge-stroke: 0.6pt,
      mark-scale: 70%,
      ext((1, 0), [Navegador], [Angular (SPA)], name: <nav>),
      svc((1, 1), [Catálogo (api)], [FastAPI + build do Angular \ única porta publicada], name: <api>),
      ext((2.9, 1), [TMDB], [API pública de filmes], name: <tmdb>),
      ext((-1.1, 1), [MySQL remoto], [banco da disciplina \ (fora da stack)], name: <mysql>),
      svc((0, 2), [auth-service], [login, cadastro, papéis, \ esqueci-senha], name: <auth>),
      svc((1, 2.9), [log-service], [auditoria \ GET /logs só admin], name: <log>),
      svc((2, 2), [Garage], [object storage S3 \ fotos de perfil], name: <garage>),
      svc((1, 3.9), [Redis], [Stream audit_log], name: <redis>),
      ext((-1.1, 3), [SMTP], [Brevo (prod) \ Mailtrap (dev)], name: <smtp>),
      svc((2.2, 3.9), [Prometheus + Grafana], [só no compose local], name: <prom>, dash: "dashed"),
      node((1, 4.6), text(size: 7pt, fill: luma(90))[rede interna Docker (catalog-net) · stack no Portainer], name: <rotulo>, stroke: none),
      node(enclose: (<api>, <auth>, <log>, <garage>, <redis>, <prom>, <rotulo>), name: <rede>, stroke: (paint: luma(150), dash: "dashed", thickness: 0.6pt), corner-radius: 6pt, inset: 9pt),

      edge(<nav>, <api>, "-|>", [HTTPS], label-side: left),
      edge(<api>, <tmdb>, "-|>", [filmes ao vivo], label-side: left),
      edge(<api>, <mysql>, "-|>", [favoritos, \ comentários, perfis], label-side: right),
      edge(<auth>, <mysql>, "-|>", [usuarios, \ reset_tokens], label-side: left),
      edge(<api>, <auth>, "-|>", [proxy /auth/\*], label-side: right),
      edge(<api>, <log>, "-|>", [POST /logs], label-side: left),
      edge(<auth>, <log>, "-|>", [POST /logs], label-side: right),
      edge(<api>, <garage>, "-|>", [S3 + URL \ pré-assinada], label-side: left),
      edge(<log>, <redis>, "-|>", [XADD / XREVRANGE], label-side: left),
      edge(<auth>, <smtp>, "-|>", [e-mail de \ redefinição], label-side: right),
      edge(<prom>, <log>, "--|>", [coleta /metrics \ (api, auth, log)], label-side: right),
    )))

    v(3mm)
    align(center, diagram(
      spacing: (12mm, 6mm), edge-stroke: 0.6pt, mark-scale: 70%,
      ext((0, 0), [git push], [branch main], name: <push>),
      svc((1, 0), [GitHub Actions], [testes, build, \ smoke test], name: <ci>),
      ext((2, 0), [GHCR], [imagens sha-xxxxxxx], name: <ghcr>),
      svc((3, 0), [Portainer], [stack via Git \ (GitOps) no servidor], name: <portainer>),
      edge(<push>, <ci>, "-|>"),
      edge(<ci>, <ghcr>, "-|>", [publica], label-side: left, label-pos: 0.5, label-sep: 1pt),
      edge(<ghcr>, <portainer>, "-|>", [aplica], label-side: left, label-sep: 1pt),
    ))
  },
  kind: image, supplement: [Figura],
  caption: [Arquitetura atual da aplicação (acima) e fluxo de deploy (abaixo)],
)

// ============================================================
= Declaração de autoria
// ============================================================
#block(breakable: false)[
  Declaro que este relatório foi elaborado por mim, individualmente, e que as evidências apresentadas correspondem a entregas de minha autoria, verificáveis nos links informados. Nas atividades realizadas em grupo, o conteúdo aqui descrito refere-se à minha participação.

  #v(1.5cm)
  #grid(
    columns: (1fr, 1fr), gutter: 2cm,
    align(center)[#line(length: 100%, stroke: 0.5pt) \ #aluno],
    align(center)[#line(length: 100%, stroke: 0.5pt) \ Pompeia, #data-relatorio],
  )
]
