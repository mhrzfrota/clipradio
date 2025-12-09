# 🚀 Quick Start - Docker

## Setup em 3 passos

### 1. Criar arquivo `.env` na raiz:

```env
DB_HOST=172.17.0.1
DB_PORT=5432
DB_NAME=clipradio_db
DB_USER=clipradio_user
DB_PASSWORD=sua_senha

SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

VITE_API_URL=http://localhost:5000/api
```

### 2. Criar diretórios:

```bash
mkdir -p backend/storage/audio backend/storage/clips backend/uploads
```

### 3. Subir containers:

```bash
docker-compose up -d --build
```

## Acessar

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:5000/api
- **Health:** http://localhost:5000/api/health

## Comandos úteis

```bash
# Ver logs
docker-compose logs -f

# Parar
docker-compose stop

# Reiniciar
docker-compose restart

# Parar e remover
docker-compose down
```

Veja `DOCKER_SETUP.md` para mais detalhes!

