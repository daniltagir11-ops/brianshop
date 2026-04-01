from webhook import webhook
from flask import Flask, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# ===== Настройки =====
TOKEN = "8486993696:AAFLyvI3lbMYltXTKXVSbMj552dcXaXwgRI"  # твой бот
CHAT_ID = -1003816309605  # твой чат

# ===== Маршрут для приема заказов =====
@app.route("/send-order", methods=["POST"])
def send_order():
    data = request.json

    if not data:
        return {"status": "error", "message": "No data received"}, 400

    # Формируем сообщение для Telegram
    items_text = ""
    for item in data.get("items", []):
        if item["type"] == "physical":
            items_text += f"┣ 📱 {item['name']}\n┣ 📦 Кол-во: {item['qty']} шт.\n┣ 💰 Цена: {item['price']}₽/шт.\n┣ 💵 Сумма: {item['total']}₽\n\n"
        elif item["type"] == "stars":
            items_text += f"┣ ⭐ {item['name']}\n┣ 📦 Кол-во: {item['qty']} шт.\n┣ 💰 Цена: 1.4₽/шт.\n┣ 💵 Сумма: {round(item['total'])}₽\n\n"
        elif item["type"] == "toncoin":
            items_text += f"┣ 💎 {item['name']}\n┣ 📦 Кол-во: {item['qty']} TON\n┣ 💰 Цена: 110₽/TON\n┣ 💵 Сумма: {item['total']}₽\n\n"
        else:
            items_text += f"┣ 🏷️ {item['name']}\n┣ ⏱ Срок: {item['days']} дн.\n┣ 💰 Цена: {item['price']}₽/день\n┣ 💵 Сумма: {item['total']}₽\n\n"

    message = f"""
🚨 НОВЫЙ ЗАКАЗ #{data.get('orderId', 'N/A')}
━━━━━━━━━━━━━━━━━━━
👤 <b>Информация о клиенте:</b>
┣ Telegram ID: <code>{data.get('tgId', '')}</code>
┣ Username: {data.get('username', '')}
┣ Время: {data.get('timestamp', '')}

📦 <b>Состав заказа:</b>
{items_text}
💰 <b>ИТОГО: {data.get('total', 0)}₽</b>
━━━━━━━━━━━━━━━━━━━
💬 <b>Действия:</b>
✅ Связаться с клиентом
✅ Подтвердить наличие
✅ Отправить реквизиты
""".strip()

    # Отправляем сообщение через Telegram API
    resp = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
    )

    if resp.status_code != 200:
        return {"status": "error", "message": resp.text}, 500

    return {"status": "ok"}
app.add_url_rule('/webhook', view_func=webhook, methods=['POST'])
# ===== Запуск сервера =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
