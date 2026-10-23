# Banca Comunitária Esperança Vida

Sistema de registro de doações e distribuições para a banca alimentícia comunitária
do Parque Araruna, Teresina-PI. Projeto de extensão da UNINASSAU.

**Sistema no ar:** https://banca-comunitaria-sistema.vercel.app

---

## O que o sistema faz

A equipe usa o sistema no celular ou no computador para:

- **Registrar doação** — produto, quantidade, nome de quem doou
- **Registrar distribuição** — produto, quantidade, nome de quem recebeu
- **Ver o estoque** atualizado a cada lançamento
- **Excluir lançamento errado** — o sistema desfaz o efeito no estoque
- **Limpar todos os registros** — apaga tudo e zera o estoque
- **Ver o dashboard** com gráficos e histórico, filtrável por data e tipo

O estoque é automático: uma doação soma, uma distribuição subtrai. Ninguém
digita o número do estoque à mão.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Flask 2.x (Python 3.11) |
| Banco | PostgreSQL (Supabase) via SQLAlchemy 2.x |
| Frontend | HTML, CSS e JavaScript puro — sem framework |
| Gráficos | Chart.js 4 (carregado por CDN) |
| Deploy | Vercel (serverless, preset Python) |

O sistema é responsivo e roda em qualquer navegador moderno: Chrome, Firefox,
Edge, Safari, Android e iPhone.

---

## Estrutura

```
banca-comunitaria-sistema/
├── backend/
│   ├── __init__.py         # torna backend importável (Vercel)
│   ├── app.py              # Flask: rotas da API e páginas
│   ├── auth.py             # Sessão e verificação de senha
│   ├── db.py               # Modelos SQLAlchemy e as consultas
│   ├── AUTH.md             # Detalhes do login
│   └── requirements.txt    # Dependências (fallback)
├── frontend/
│   ├── login.html          # Tela de login
│   ├── index.html          # App: estoque, histórico e formulários
│   ├── stats.html          # Dashboard com gráficos
│   ├── manifest.json       # Ícone para instalação na tela inicial
│   └── sw.js               # Service worker
├── pyproject.toml          # Entrypoint + dependências (Vercel instala daqui)
├── vercel.json             # Configuração Vercel (cron de keep-alive)
├── requirements.txt        # Fallback/compatibilidade
├── Dockerfile              # Deploy alternativo (Docker)
└── docker-compose.yml
```

---

## Rotas da API

Todas as rotas de dados exigem sessão iniciada (retornam `401` sem login),
exceto `/login` e `/api/health`.

| Rota | Método | Descrição |
|---|---|---|
| `/login` | GET, POST | Tela de login e verificação da senha |
| `/logout` | GET, POST | Encerra a sessão |
| `/api/sessao` | GET | Diz se está autenticado e se o login está configurado |
| `/api/estoque` | GET | Produtos com o estoque atual |
| `/api/resumo` | GET | Totais: produtos, baixo estoque, sem estoque |
| `/api/doacoes` | GET, POST | Lista e registra doações |
| `/api/doacoes/<id>` | DELETE | Apaga uma doação e desfaz o efeito no estoque |
| `/api/distribuicoes` | GET, POST | Lista e registra distribuições |
| `/api/distribuicoes/<id>` | DELETE | Apaga uma distribuição e devolve ao estoque |
| `/api/limpar` | POST | Apaga todas as movimentações e zera o estoque |
| `/dados` | GET | Tudo junto, para relatórios e scripts |
| `/api/health` | GET | Health check público (usado pelo cron de keep-alive) |

### Sobre o DELETE

Apagar um lançamento **desfaz o efeito dele no estoque**. Apagar uma doação de
10 sacos desconta 10; apagar uma distribuição devolve 10 ao estoque. Sem isso os
números ficariam errados sem ninguém perceber.

### Sobre o `/api/limpar`

Exige confirmação explícita no corpo do pedido:

```json
{"confirmar": "APAGAR TUDO"}
```

Sem essa string a rota recusa com `400`. É uma proteção: uma chamada direta por
linha de comando não apaga nada sem ela.

---

## Instalação local

```bash
git clone https://github.com/gilmadara2872/banca-comunitaria-sistema.git
cd banca-comunitaria-sistema

# python3-venv pode faltar no sistema; use uv
uv venv venv
VIRTUAL_ENV=$PWD/venv uv pip install -r backend/requirements.txt
./venv/bin/python backend/app.py
```

Abre em http://localhost:5000

Sem `DATABASE_URL`, o sistema cai para um arquivo SQLite local (`banca.db`) —
útil para desenvolver sem subir banco nenhum.

---

## Variáveis de ambiente

| Variável | Obrigatória | Para que serve |
|---|---|---|
| `DATABASE_URL` | em produção | Conexão com o PostgreSQL (pooler do Supabase) |
| `ADMIN_SENHA` | **sim** | Senha que a equipe usa para entrar |
| `SESSION_SECRET` | recomendada | Chave que assina o cookie de sessão |
| `POSTGRES_URL` / `POSTGRES_PRISMA_URL` | não | Fallbacks aceitos para a conexão do banco |

**Sem `ADMIN_SENHA` o sistema não deixa ninguém entrar.** Não existe senha
padrão no código. Detalhes em [`backend/AUTH.md`](backend/AUTH.md).

---

## Deploy no Vercel + Supabase

O app é um Flask servido pelo preset Python do Vercel. A nuvem é atualizada
pelo GitHub: editar local → testar local → commit → push na `main`. O Vercel
redeploya sozinho ao ver o push. Fallback: `vercel deploy --prod --yes` dentro
do clone (CLI autenticado).

Configuração necessária no repo (já aplicada):

- `pyproject.toml` com `entrypoint = "backend.app:app"` e `dependencies`
  (Flask, Flask-CORS, SQLAlchemy, psycopg[binary]). O Vercel instala a partir
  do `pyproject.toml` (ignora `requirements.txt` quando ele existe).
- `backend/__init__.py` vazio, para `backend.app` ser importável.
- Rota `/` usa `send_from_directory(frontend_dir, 'index.html')` com caminho
  absoluto (`frontend_dir`), não relativo — no serverless o cwd não é o do app.
- `.gitignore` ignora `.vercel` e `.env*`.

Env vars no Vercel (Project → Settings → Environment Variables):

- `DATABASE_URL` = connection string do **pooler** do Supabase (porta 6543 ou
  5432, host `*.pooler.supabase.com`). **Nunca use a URL direta**
  (`db.<ref>.supabase.co:5432`): ela resolve só para IPv6 e o Vercel (IPv4)
  falha com "Cannot assign requested address". O pooler é IPv4. Username do
  pooler: `postgres.<project_ref>`.
- `ADMIN_SENHA` e `SESSION_SECRET`.

Verificação: abrir https://banca-comunitaria-sistema.vercel.app/login e conferir
que o login funciona (não só status HTTP).

### Keep-alive (evitar pausa do Supabase free tier)

O Supabase free tier pausa o projeto após 7 dias de inatividade. Para evitar,
existe um cron diário (`0 6 * * *`) configurado em `vercel.json` que chama
`/api/health` (público, sem login). O endpoint executa `SELECT 1` no banco.

### Pitfalls do Vercel + Supabase

- **Supabase direct connection é IPv6-only** → Vercel não alcança. Usar sempre
  o pooler.
- **Pooler com muitas tentativas de senha errada** ativa circuit breaker
  (ECIRCUITBREAKER "too many authent"). Aguardar cooldown antes de tentar de
  novo.
- **Senha do banco não pode ser resetada via Management API/SQL**: o role
  `postgres` não é superuser no Supabase (`rolsuper=false`), então
  `ALTER ROLE postgres PASSWORD` falha. Resetar só pelo painel (Project
  Settings → Database → Reset database password).
- **Supavisor cacheia senha após rotação**: após resetar a senha no painel do
  Supabase, o pooler pode continuar rejeitando a senha nova por alguns minutos.
  Tentar de novo após 1-2 min; se persistir, resetar a senha mais uma vez
  (valor diferente) para forçar limpeza do cache.
- **Vercel redige valores secretos nos logs**: ao imprimir `DATABASE_URL` em
  stderr para debug, o Vercel mostra `***` no lugar da senha. Para confirmar que
  o valor está sendo lido, verifique o comprimento ou a estrutura (host, porta),
  nunca o conteúdo.
- **Vercel Deployment Protection (SSO)**: com ssoProtection
  `all_except_custom_domains`, deploys de preview retornam 401 "Protected
  deployment", mas aliases de domínio customizado não são protegidos. Para
  testar o deploy mais recente, use o alias ou desabilite a proteção no painel.

---

## Notas técnicas

### Driver do PostgreSQL

O SQLAlchemy 2.x resolve `postgresql://` para o driver **psycopg (v3)**.
Instalar apenas `psycopg2-binary` faz o processo morrer no boot com
`ModuleNotFoundError: No module named 'psycopg'`.

Por isso o `requirements.txt` instala `psycopg[binary]` **e** o `db.py` fixa o
driver na URL (`postgresql+psycopg://`). Os dois juntos são necessários.

### Tipos vindos do formulário

O `<select>` do HTML entrega o id do produto como texto. O SQLite aceita
comparar texto com inteiro, mas o PostgreSQL rejeita
(`operator does not exist: integer = character varying`).

A conversão para `int` fica em `db.py`, na função que grava — assim todas as
rotas ficam protegidas, e não só a que decoratei.

Isso só aparece gravando. Uma verificação que só faz `GET` passa com o banco
completamente quebrado.

### Escape de HTML

Nome de doador e de beneficiário vêm do banco e entram no HTML. Todo campo
passa por `escapar()` antes de ir para o `innerHTML` — sem isso, um nome com
`<img src=x onerror=...>` executa código no navegador de quem abre a tela.

### Cache de engine (Vercel warm)

O `db.py` mantém um cache em nível de módulo do engine do SQLAlchemy para
reutilizar o pool de conexões entre chamadas no mesmo processo (Vercel warm),
evitando estourar o limite de clientes do pooler (session mode = 15).

### Tabelas do banco

Criadas automaticamente no boot por `init_db()`, junto com os 12 produtos
iniciais (só se a tabela estiver vazia).

- `produtos` — nome, unidade, estoque atual
- `doacoes` — produto, quantidade, doador, data, observação
- `distribuicoes` — produto, quantidade, beneficiário, data, observação

---

## Produtos cadastrados

Arroz, Feijão, Óleo de cozinha, Leite em pó, Açúcar, Farinha de trigo,
Café em pó, Sal, Macarrão, Cuscuz, Gelatina, Chocolate em pó.

---

## Equipe

Projeto **PEX-MDL-54** — Banca Comunitária Esperança Vida, Parque Araruna,
Teresina-PI.

**Alunos:** Gilberto de Sousa Barbosa Filho, Rafael de Souza Freitas Carvalho,
Luiz Eduardo Ferreira Neto, Wendel Borges da Silva Vieira, Clara Maria Cavalcante Costa.

**Orientador:** Prof. Dr. Alan da Silva Assunção.

---

## Licença

Projeto acadêmico — uso livre.
