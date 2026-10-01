# Autenticação

O sistema usa **senha única, compartilhada pela equipe**. Quem sabe a
senha entra; quem não sabe não consegue ler nem alterar os dados.

## Variáveis de ambiente

| Variável | Obrigatória | Para quê |
|---|---|---|
| `ADMIN_SENHA` | **sim** | A senha que libera o acesso |
| `SESSION_SECRET` | recomendado | Chave que assina o cookie de sessão |

Sem `ADMIN_SENHA` o sistema **sobe protegido**: ninguém entra. A tela de
login avisa que o login não foi configurado. Não existe senha padrão
no código — essa é a falha mais comum em projeto de faculdade.

## Testar localmente

```bash
export ADMIN_SENHA="minha-senha-de-teste"
export SESSION_SECRET="qualquer-coisa-longa"
python backend/app.py
```

Abra `http://localhost:5000` — vai redirecionar para `/login`.

No Railway (uma vez só):

1. Serviço → **Variables**
2. `ADMIN_SENHA` = a senha que você quiser
3. `SESSION_SECRET` = um valor aleatório e longo

Para gerar um bom `SESSION_SECRET`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Se trocar a `SESSION_SECRET`, todo mundo é desconectado. Isso é
esperado.

## Como funciona

- `POST /login` compara a senha com a do ambiente, em **tempo
  constante** (`hmac.compare_digest`) — não vaza informação por
  tempo de resposta.
- A sessão dura 12 horas, depois exige entrar de novo.
- Páginas (`/`, `/stats`) redirecionam para `/login`.
- APIs (`/api/*`) devolvem `401` em JSON, e o frontend manda a pessoa
  para a tela de login sozinha.
- O botão ↩ no canto superior direito encerra a sessão.

## Rotas protegidas

```
/                 /stats              /dados
/api/estoque      /api/doacoes        /api/distribuicoes
/api/resumo
```

## Rotas públicas

```
GET  /login         a tela de login
POST /login         confere a senha
GET  /logout        encerra a sessão
GET  /api/sessao    o frontend pergunta se ainda está logado
```

## O que este login NÃO faz

Ele **não** cria usuários separados nem registra quem registrou cada
movimentação. É um controle de acesso de porta única: protege o banco
de quem está de fora, mas dentro todos compartilham a mesma identidade.

Para registrar **quem** registrou cada doação/distribuição, o caminho é
uma tabela de usuários — com campo de login em cada registro. É a
evolução natural deste código: a estrutura já está preparada, falta
trocar a senha única por uma tabela.

## Nota de segurança

Para um projeto de extensão real, dois cuidados:

1. A senha do banco (`DATABASE_URL`) fica exposta em logs se alguém
   cadastrar a variável `DATABASE_PUBLIC_URL` no GitHub. Não faça.
2. HTTPS é obrigatório fora de localhost. No Railway já vem por padrão.
