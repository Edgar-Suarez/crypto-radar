# 📡 Crypto Radar

Dashboard de inteligencia en tiempo real: tendencias crypto y startups desde Reddit, Hacker News, RSS y CoinGecko. **Stack 100% gratuito.**

---

## Stack

| Capa | Tecnología | Costo |
|------|-----------|-------|
| Backend | Python + FastAPI | Gratis (Railway) |
| Base de datos | Supabase (PostgreSQL) | Gratis (500MB) |
| Tiempo real | Supabase Realtime | Gratis (2M msgs/mes) |
| Análisis | VADER Sentiment | Gratis |
| Frontend | React + Vite + Tailwind | Gratis (Vercel) |
| Alertas | Telegram Bot | Gratis |

---

## Arquitectura

```
Reddit / HN / RSS / CoinGecko
        ↓  (cada 10 min)
  FastAPI Backend
  ├── Sentiment Engine (VADER + crypto vocab)
  ├── Trend Detector  (velocity + buzz score)
  └── Alert Dispatcher (Telegram + browser)
        ↓
  Supabase (PostgreSQL + Realtime)
        ↓
  React Dashboard (actualizaciones en vivo)
```

---

## Setup en 5 pasos

### 1. Supabase

1. Crear cuenta en [supabase.com](https://supabase.com)
2. Nuevo proyecto → copiar `Project URL` y las dos keys (`anon` y `service_role`)
3. Ir a **SQL Editor → New Query** → pegar y ejecutar `supabase_schema.sql`

### 2. Backend (local)

```bash
cd backend
cp .env.example .env
# Editar .env con tus credenciales de Supabase
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Verificar: `http://localhost:8000/docs`

### 3. Frontend (local)

```bash
cd frontend
cp .env.example .env
# Editar .env:
#   VITE_API_URL=http://localhost:8000   (vacío si usas proxy)
#   VITE_SUPABASE_URL=...
#   VITE_SUPABASE_ANON_KEY=...
npm install
npm run dev
```

Abrir: `http://localhost:5173`

### 4. Deploy Backend → Railway

1. `railway login` → `railway init` → `railway up`
2. Agregar variables de entorno en Railway dashboard:
   - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
   - `CORS_ORIGINS=https://tu-app.vercel.app`
3. Copiar la URL del backend (ej: `https://crypto-radar.up.railway.app`)

### 5. Deploy Frontend → Vercel

1. Push a GitHub
2. Importar en [vercel.com](https://vercel.com)
3. Agregar variables de entorno:
   - `VITE_API_URL=https://crypto-radar.up.railway.app`
   - `VITE_SUPABASE_URL=...`
   - `VITE_SUPABASE_ANON_KEY=...`
4. Deploy ✅

---

## Alertas Telegram (opcional)

1. Hablar con `@BotFather` en Telegram → `/newbot` → copiar token
2. Iniciar chat con el bot → obtener chat ID desde `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Agregar en `.env` del backend:
   ```
   TELEGRAM_BOT_TOKEN=7xxxxxx:AAFxxxxxx
   TELEGRAM_CHAT_ID=123456789
   ```

---

## Endpoints API

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/crypto/feed` | Feed de menciones con filtros |
| `GET /api/crypto/trending` | Coins trending de CoinGecko |
| `GET /api/trends/leaderboard?window=1` | Leaderboard por buzz score |
| `GET /api/trends/spikes` | Eventos de spike detectados |
| `GET /api/sentiment/market-mood` | Fear & Greed index |
| `GET /api/sentiment/coin/{symbol}/history` | Histórico de sentimiento |
| `GET /api/alerts/recent` | Últimas alertas enviadas |
| `GET /health` | Health check |

Documentación interactiva: `http://localhost:8000/docs`

---

## Variables de entorno

### Backend (`.env`)
```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...
TELEGRAM_BOT_TOKEN=          # Opcional
TELEGRAM_CHAT_ID=            # Opcional
CORS_ORIGINS=http://localhost:5173
ENVIRONMENT=development
```

### Frontend (`.env`)
```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
```

---

## Costo total: $0/mes

Todo el stack corre en tiers gratuitos.
