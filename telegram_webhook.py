"""
Server webhook Telegram: nhận tin của khách, trả lời chữ và ảnh.

Cài đặt:
    pip install fastapi uvicorn httpx

Biến môi trường (KHÔNG ghi token vào code):
    export TELEGRAM_BOT_TOKEN="123456789:AAH..."
    export WEBHOOK_SECRET="chuoi-bi-mat-tu-chon-A-Za-z0-9_-"

Chạy:
    uvicorn telegram_webhook:app --host 0.0.0.0 --port 8000
"""
import logging
import os

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("telegram-webhook")

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SECRET = os.getenv("WEBHOOK_SECRET")
API = f"https://api.telegram.org/bot{TOKEN}"

# Ảnh mẫu công khai để test gửi ảnh
SAMPLE_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"

app = FastAPI()
client = httpx.AsyncClient(timeout=10)


async def send_text(chat_id: int, text: str):
    r = await client.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text})
    log.info("sendMessage -> %s %s", r.status_code, r.text[:200])


async def send_photo(chat_id: int, photo_url: str, caption: str = ""):
    r = await client.post(
        f"{API}/sendPhoto",
        json={"chat_id": chat_id, "photo": photo_url, "caption": caption},
    )
    log.info("sendPhoto -> %s %s", r.status_code, r.text[:200])


@app.get("/")
async def health():
    return {"ok": True}


@app.post("/telegram/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    print("SECRET FROM ENV =", SECRET)
    print("SECRET FROM TELEGRAM =", x_telegram_bot_api_secret_token)
    
    # Chỉ nhận request thật từ Telegram (khớp secret_token đã đăng ký với setWebhook)
    if x_telegram_bot_api_secret_token != SECRET:
        raise HTTPException(status_code=403, detail="forbidden")

    update = await request.json()
    log.info("=== NHẬN UPDATE TỪ TELEGRAM ===\n%s", update)

    message = update.get("message")
    if not message:
        return {"ok": True}  # bỏ qua các loại update khác

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.strip().lower() == "anh":
        await send_photo(chat_id, SAMPLE_IMAGE, "Ảnh test")
    elif message.get("photo"):
        await send_text(chat_id, "Đã nhận ảnh của bạn.")
    else:
        await send_text(chat_id, f"Server nhận được: {text}")

    # Luôn trả 200 nhanh để Telegram không gửi lại update
    return {"ok": True}
