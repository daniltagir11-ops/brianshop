from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "ТВОЙ_ТОКЕН"
CHAT_ID = -1003816309605

@app.route("/send-order", methods=["POST"])
def send_order():
    data = request.json

    text = f"""
🚨 НОВЫЙ ЗАКАЗ #{data['orderId']}

👤 ID: {data['tgId']}
👤 Username: {data['username']}

💰 Сумма: {data['total']}₽
"""

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    return {"status": "ok"}
