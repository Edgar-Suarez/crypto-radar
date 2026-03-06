import httpx
import asyncio
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from db.database import send_browser_alert, log_alert, is_on_cooldown

SEVERITY_EMOJI = {"low": "📊", "medium": "⚠️", "high": "🚨", "extreme": "💥"}
COOLDOWN_MINUTES = {"low": 120, "medium": 60, "high": 30, "extreme": 10}

async def send_telegram(topic: str, message: str, severity: str = "medium"):
    token   = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    emoji = SEVERITY_EMOJI.get(severity, "📊")
    text  = (f"{emoji} *CRYPTO RADAR*\n\n*{topic}* — {severity.upper()}\n"
             f"{message}\n\n_{datetime.utcnow().strftime('%H:%M UTC')}_")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Telegram error: {e}")

async def dispatch_spike_alerts(spikes: list[dict]):
    for spike in spikes:
        topic    = spike["topic"]
        severity = spike.get("severity", "low")
        cooldown = COOLDOWN_MINUTES.get(severity, 60)
        if is_on_cooldown(topic, cooldown):
            continue
        message = (f"{topic} trending: {spike.get('mention_count')} mentions/h "
                   f"(velocity {spike.get('velocity_score')}x normal)")
        await send_telegram(topic, message, severity)
        send_browser_alert(topic, message, severity, spike)
        log_alert(topic, message, "all")

async def dispatch_reversal_alerts(reversals: list[dict]):
    for r in reversals:
        topic = r["coin"]
        if is_on_cooldown(f"reversal_{topic}", 240):
            continue
        emoji   = "📈" if "positive" in r["direction"] else "📉"
        message = f"{emoji} {topic} sentiment {r['direction'].replace('_',' ')} (Δ{r['delta']:+.2f})"
        await send_telegram(topic, message, "medium")
        send_browser_alert(topic, message, "medium", r)
        log_alert(f"reversal_{topic}", message, "all")

def sync_dispatch_spikes(spikes: list[dict]):
    try:
        asyncio.run(dispatch_spike_alerts(spikes))
    except RuntimeError:
        pass  # already in event loop — skip
