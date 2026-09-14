# ─── Dockerfile — Sistema Banca Alimentícia ────────────────────────────────
# Base: Python 3.11 slim (leve, oficial)
FROM python:3.11-slim

# Diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências do sistema (se precisar de alguma lib C no futuro)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python (cacheável se só mudar código depois)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do app
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Criar diretório de dados persistentes
RUN mkdir -p /data

# Variável de ambiente para onde o SQLite vai escrever
ENV DATA_DIR=/data
ENV PORT=5000

# Exposição da porta (o Railway mapeia automático)
EXPOSE 5000

# Comando de inicialização
# O DATA_DIR é montado como volume no docker-compose para persistência do SQLite
CMD ["python", "backend/app.py"]
