# Banca Comunitária Sistema

Sistema de gerenciamento de doações e distribuições para banca alimentícia comunitária. Projeto de extensão da UNINASSAU.

## Stack
- **Backend:** Flask (Python)
- **Frontend:** HTML/CSS/JS vanilla, mobile-first
- **Banco:** PostgreSQL (SQLAlchemy ORM)
- **Deploy:** Railway (Docker)
- **Dashboard:** Chart.js

## Estrutura
```
banca-comunitaria-sistema/
├── backend/
│   ├── app.py              # Flask app + rotas API
│   ├── db.py               # SQLAlchemy models + queries
│   └── requirements.txt    # Flask, SQLAlchemy, psycopg2
├── frontend/
│   ├── index.html          # Interface mobile (registro de doações/distribuições)
│   └── stats.html          # Dashboard com gráficos e histórico
├── Dockerfile
└── docker-compose.yml
```

## Rotas
- `/` — Interface principal de registro
- `/stats` — Dashboard com gráficos (pizza, barras) e histórico
- `/api/estoque` — Produtos e estoque atual
- `/api/doacoes` — GET/POST de doações
- `/api/distribuicoes` — GET/POST de distribuições
- `/api/resumo` — Resumo do estoque

## Instalação local
```bash
cd banca_app
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python backend/app.py
# Acessar: http://localhost:5000
```

## Deploy no Railway
```bash
cd banca_app
railway login
railway init
railway add --database postgres
railway link
railway up
```

## Variáveis de ambiente
- `DATABASE_URL` — PostgreSQL connection string (Railway define automaticamente)
- `PORT` — Porta do servidor (padrão: 5000)

## Produtos iniciais cadastrados
Arroz, Feijão, Óleo de cozinha, Leite em pó, Açúcar, Farinha de trigo, Café em pó, Sal, Macarrão, Cuscuz, Gelatina, Chocolate em pó.

## Equipe
Projeto PEX-MDL-54 — Banca Comunitária Esperança Vida, Parque Araruna, Teresina-PI.
Alunos: Gilberto de Sousa Barbosa Filho, Rafael de Souza Freitas Carvalho, Luiz Eduardo Ferreira Neto, Wendel Borges da Silva Vieira, Clara Maria Cavalcante Costa.
Orientador: Prof. Dr. Alan da Silva Assunção.

## Licença
Projeto acadêmico — uso livre.
