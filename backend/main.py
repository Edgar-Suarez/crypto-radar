import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from routers import crypto, trends, sentiment, alerts
from services.scheduler import start_scheduler

_scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    _scheduler = start_scheduler()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)

app = FastAPI(
    title="Crypto Radar API",
    description="Real-time crypto & startup intelligence — 100% free stack",
    version="1.0.0",
    lifespan=lifespan,
)

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crypto.router,    prefix="/api/crypto",    tags=["Crypto"])
app.include_router(trends.router,    prefix="/api/trends",    tags=["Trends"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["Sentiment"])
app.include_router(alerts.router,    prefix="/api/alerts",    tags=["Alerts"])

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.utcnow().isoformat(),
    }
