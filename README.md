# Banca Alimentícia PWA
# Sistema para gerenciamento de doações e distribuições

## Estrutura
```
banca_app/
├── backend/
│   ├── app.py              # Flask app
│   ├── db.py               # SQLite operations
│   └── requirements.txt
├── frontend/
│   ├── index.html         # PWA interface
│   ├── manifest.json      # PWA manifest
│   └── sw.js              # Service worker (cache)
├── static/
│   └── style.css
└── requirements.txt
```

## Instalação local
```bash
cd banca_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python backend/app.py
# Acessar: http://localhost:5000
```

## Deploy no Railway
```bash
cd banca_app
railway login
railway init
railway link
railway up
```
