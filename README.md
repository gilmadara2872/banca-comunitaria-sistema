# Banca Comunitária Esperança Vida

Sistema de registro de doações e distribuições para a banca alimentícia comunitária
do Parque Araruna, Teresina-PI. Projeto de extensão da UNINASSAU.

**Sistema no ar:** https://banca-comunitaria-sistema-production-1e32.up.railway.app

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
| Backend | Flask 2.3 (Python 3.11) |
| Banco | PostgreSQL 16 (Railway) via SQLAlchemy 2.x |
| Frontend | HTML, CSS e JavaScript puro — sem framework |
| Gráficos | Chart.js 4 (carregado por CDN) |
| Deploy | Railway (Docker) |

O sistema é responsivo e roda em qualquer navegador moderno: Chrome, Firefox,
Edge, Safari, Android e iPhone.

---

## Estrutura

```
banca-comunitaria-sistema/
├── backend/
│   ├── app.py              # Flask: rotas da API e páginas
│   ├── auth.py             # Sessão e verificação de senha
│   ├── db.py               # Modelos SQLAlchemy e as consultas
│   ├── AUTH.md             # Detalhes do login
│   └── requirements.txt    # Dependências
├── frontend/
│   ├── login.html          # Tela de login
│   ├── index.html          # App: estoque, histórico e formulários
│   ├── stats.html          # Dashboard com gráficos
│   ├── manifest.json       # Ícone para instalação na tela inicial
│   └── sw.js               # Service worker
├── Dockerfile
├── docker-compose.yml
└── setup.py
```

---

## Rotas da API

Todas as rotas de dados exigem sessão iniciada (retornam `401` sem login).

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

python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

export ADMIN_SENHA="sua-senha"
export SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

python backend/app.py
```

Abre em http://localhost:5000

Sem `DATABASE_URL`, o sistema cai para um arquivo SQLite local (`banca.db`) —
útil para desenvolver sem subir banco nenhum.

---

## Variáveis de ambiente

| Variável | Obrigatória | Para que serve |
|---|---|---|
| `DATABASE_URL` | em produção | Conexão com o PostgreSQL |
| `ADMIN_SENHA` | **sim** | Senha que a equipe usa para entrar |
| `SESSION_SECRET` | recomendada | Chave que assina o cookie de sessão |
| `PORT` | Railway define | Porta do servidor (padrão 5000) |

**Sem `ADMIN_SENHA` o sistema não deixa ninguém entrar.** Não existe senha
padrão no código. Detalhes em [`backend/AUTH.md`](backend/AUTH.md).

---

## Deploy no Railway

O deploy é automático: cada `git push` na branch `main` reconstrói e publica.

```bash
git push origin main
```

Para criar o serviço do zero:

```bash
railway login
railway init
railway add --database postgres
railway link
railway up
```

Depois, no painel:

1. **Settings → Source** — confirmar repositório `gilmadara2872/banca-comunitaria-sistema`, branch `main`, trigger *On push*
2. **Settings → Networking → Generate Domain** — sem domínio o serviço não responde em nenhum endereço
3. **Variables** — `ADMIN_SENHA`, `SESSION_SECRET` e `DATABASE_URL` (copiada do serviço Postgres)

### Um repositório pode estar ligado a vários projetos do Railway

Cada projeto constrói separado e tem seu próprio endereço. Se o deploy passar e o
site continuar servindo a versão antiga, provavelmente você está abrindo o
domínio de outro projeto. Verifique em **Deployments** qual commit foi publicado.

---

## Notas técnicas

### Driver do PostgreSQL

O SQLAlchemy 2.x resolve `postgresql://` para o driver **psycopg (v3)**.
Instalar apenas `psycopg2-binary` faz o processo morrer no boot com
`ModuleNotFoundError: No module named 'psycopg'`.

Por isso o `requirements.txt` instala `psycopg[binary]` **e** o `db.py` fixa o
driver na URL (`postgresql+psycopg://`). Os dois juntos são necessários.

Esse erro acontece no boot, e o Railway continua marcando o build como
`Success` — a imagem foi construída, o problema é no start.

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
