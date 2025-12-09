# 🐳 Guia de Setup Docker - HorizonsRecorder

Este guia explica como subir o sistema completo usando Docker Compose.

## 📋 Pré-requisitos

- Docker instalado (versão 20.10+)
- Docker Compose instalado (versão 2.0+)
- PostgreSQL rodando e acessível (host: `172.17.0.1` ou configurar no `.env`)

## 🚀 Setup Rápido

### 1. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# PostgreSQL
DB_HOST=172.17.0.1
DB_PORT=5432
DB_NAME=clipradio_db
DB_USER=clipradio_user
DB_PASSWORD=sua_senha_aqui

# Segurança
SECRET_KEY=seu-secret-key-aleatorio-aqui
JWT_SECRET=seu-jwt-secret-aleatorio-aqui

# API URL (para o frontend acessar o backend)
VITE_API_URL=http://localhost:5000/api
```

**Importante:** Gere valores seguros para `SECRET_KEY` e `JWT_SECRET`:

```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### 2. Criar Diretórios de Storage

```bash
mkdir -p backend/storage/audio backend/storage/clips backend/uploads
```

### 3. Build e Subir os Containers

```bash
# Build das imagens
docker-compose build

# Subir os containers
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 4. Verificar Status

```bash
# Ver status dos containers
docker-compose ps

# Testar backend
curl http://localhost:5000/api/health

# Acessar frontend
# Abra: http://localhost:3000
```

## 🔧 Comandos Úteis

### Gerenciamento de Containers

```bash
# Parar containers
docker-compose stop

# Iniciar containers
docker-compose start

# Reiniciar containers
docker-compose restart

# Parar e remover containers
docker-compose down

# Parar, remover e limpar volumes
docker-compose down -v

# Rebuild e subir
docker-compose up -d --build
```

### Logs

```bash
# Ver todos os logs
docker-compose logs -f

# Logs apenas do backend
docker-compose logs -f backend

# Logs apenas do frontend
docker-compose logs -f frontend

# Últimas 100 linhas
docker-compose logs --tail=100
```

### Executar Comandos nos Containers

```bash
# Acessar shell do backend
docker-compose exec backend bash

# Acessar shell do frontend
docker-compose exec frontend sh

# Executar comando no backend
docker-compose exec backend python -c "from app import db; print('OK')"
```

## 🌐 Acessos

Após subir os containers:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000/api
- **Health Check:** http://localhost:5000/api/health

## 🔍 Troubleshooting

### Backend não conecta ao banco

1. Verificar se PostgreSQL está acessível:
   ```bash
   # Testar conexão do host
   psql -h 172.17.0.1 -U clipradio_user -d clipradio_db
   ```

2. Se PostgreSQL estiver em outro host, ajuste `DB_HOST` no `.env`

3. Verificar logs do backend:
   ```bash
   docker-compose logs backend
   ```

### Frontend não acessa o backend

1. Verificar se `VITE_API_URL` está correto no `.env`
2. Verificar se backend está rodando: `curl http://localhost:5000/api/health`
3. Verificar logs do nginx:
   ```bash
   docker-compose exec frontend cat /var/log/nginx/error.log
   ```

### Containers não sobem

1. Verificar portas disponíveis:
   ```bash
   # Linux/Mac
   lsof -i :3000
   lsof -i :5000
   
   # Windows
   netstat -ano | findstr :3000
   netstat -ano | findstr :5000
   ```

2. Se portas estiverem ocupadas, altere no `docker-compose.yml`:
   ```yaml
   ports:
     - "3001:80"  # Frontend
     - "5001:5000"  # Backend
   ```

### Rebuild completo

Se houver problemas, faça rebuild completo:

```bash
# Parar tudo
docker-compose down -v

# Remover imagens
docker-compose rm -f

# Rebuild
docker-compose build --no-cache

# Subir
docker-compose up -d
```

### Problemas com permissões (Linux)

Se houver problemas de permissão nos volumes:

```bash
sudo chown -R $USER:$USER backend/storage backend/uploads
```

## 📦 Volumes Persistidos

Os seguintes diretórios são persistidos no host:

- `./backend/storage` - Arquivos de áudio gravados
- `./backend/uploads` - Arquivos temporários

## 🔐 Segurança

⚠️ **Importante para Produção:**

1. Altere todas as senhas e secrets padrão
2. Use variáveis de ambiente seguras
3. Configure firewall adequadamente
4. Use HTTPS (adicione certificado SSL)
5. Configure backups regulares do banco de dados

## 🚀 Deploy em Produção

Para deploy em produção, considere:

1. **HTTPS/SSL:**
   - Use um proxy reverso (nginx/traefik) com SSL
   - Configure certificados Let's Encrypt

2. **Banco de Dados:**
   - Use um serviço gerenciado de PostgreSQL
   - Configure backups automáticos

3. **Variáveis de Ambiente:**
   - Use um gerenciador de secrets (Docker Secrets, HashiCorp Vault)

4. **Monitoramento:**
   - Configure health checks
   - Use ferramentas de monitoramento (Prometheus, Grafana)

## 📝 Estrutura de Containers

```
┌─────────────────┐
│   Frontend      │
│   (Nginx)       │ :3000
└────────┬────────┘
         │
         │ HTTP/WS
         │
┌────────▼────────┐
│   Backend       │
│   (Flask)       │ :5000
└────────┬────────┘
         │
         │ PostgreSQL
         │
┌────────▼────────┐
│   PostgreSQL    │
│   (Externo)     │ :5432
└─────────────────┘
```

## ✅ Checklist de Deploy

- [ ] Arquivo `.env` configurado
- [ ] Diretórios de storage criados
- [ ] PostgreSQL acessível
- [ ] Portas 3000 e 5000 disponíveis
- [ ] Build executado com sucesso
- [ ] Containers rodando (`docker-compose ps`)
- [ ] Health check OK (`curl http://localhost:5000/api/health`)
- [ ] Frontend acessível (http://localhost:3000)
- [ ] Teste de login funcionando

---

**Pronto!** Seu sistema está rodando no Docker! 🎉

