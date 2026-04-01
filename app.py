from flask import Flask, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# ===== Настройки =====
TOKEN = "8486993696:AAFLyvI3lbMYltXTKXVSbMj552dcXaXwgRI"
CHAT_ID = -1003816309605

# ===== Функция для сохранения заказа в Supabase =====
def save_order_to_supabase(order_data):
    SUPABASE_URL = "https://perxwqxtzgbvswimmkgt.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBlcnh3cXh0emdidnN3aW1ta2d0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwNTY1NTYsImV4cCI6MjA5MDYzMjU1Nn0.dmR6UpUOHsYgPgr8k9wWWiqdNhfGq38Qjk5so1l37YY"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "order_number": order_data.get("orderId"),
        "user_tg_id": int(order_data.get("tgId")),
        "items": order_data.get("items"),
        "total": order_data.get("total"),
        "status": "pending"
    }
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/orders",
            headers=headers,
            json=payload
        )
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Supabase error: {e}")
        return False

# ===== Маршрут для приема заказов =====
@app.route("/send-order", methods=["POST"])
def send_order():
    data = request.json

    if not data:
        return {"status": "error", "message": "No data received"}, 400

    # Сохраняем заказ в Supabase
    save_order_to_supabase(data)

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
🆕 <b>НОВЫЙ ЗАКАЗ #{data.get('orderId', 'N/A')}</b>
━━━━━━━━━━━━━━━━━━━
👤 <b>Клиент:</b>
┣ ID: <code>{data.get('tgId', '')}</code>
┣ Username: {data.get('username', '')}
┣ Время: {data.get('timestamp', '')}

📦 <b>Состав заказа:</b>
{items_text}
💰 <b>ИТОГО: {data.get('total', 0)}₽</b>
""".strip()

    # Inline-кнопки
    inline_keyboard = {
        "inline_keyboard": [[
            {"text": "👀 Просмотрено", "callback_data": f"view_{data.get('orderId', '')}"},
            {"text": "✅ Оплачен", "callback_data": f"paid_{data.get('orderId', '')}"},
            {"text": "📦 Выполнен", "callback_data": f"done_{data.get('orderId', '')}"}
        ]]
    }

    # Отправляем в Telegram
    resp = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": inline_keyboard
        }
    )

    if resp.status_code != 200:
        return {"status": "error", "message": resp.text}, 500

    return {"status": "ok", "success": True}

# ===== WEBHOOK ДЛЯ КНОПОК =====
@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json
    
    if not update or "callback_query" not in update:
        return {"status": "ok"}, 200
    
    callback = update["callback_query"]
    data = callback["data"]
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    
    action, order_id = data.split("_")
    
    status_map = {
        "view": ("viewed", "Просмотрено"),
        "paid": ("paid", "Оплачен"),
        "done": ("completed", "Выполнен")
    }
    
    if action not in status_map:
        return {"status": "ok"}, 200
    
    new_status, status_text = status_map[action]
    
    # Обновляем статус в Supabase
    SUPABASE_URL = "https://perxwqxtzgbvswimmkgt.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBlcnh3cXh0emdidnN3aW1ta2d0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwNTY1NTYsImV4cCI6MjA5MDYzMjU1Nn0.dmR6UpUOHsYgPgr8k9wWWiqdNhfGq38Qjk5so1l37YY"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/orders?order_number=eq.{order_id}",
        headers=headers,
        json={"status": new_status}
    )
    
    # Получаем заказ для user_tg_id
    order_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/orders?order_number=eq.{order_id}&select=*",
        headers=headers
    )
    order = order_response.json()[0] if order_response.status_code == 200 and order_response.json() else None
    
    # Обновляем сообщение модератора
    get_msg = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/getMessage",
        json={"chat_id": chat_id, "message_id": message_id}
    )
    
    if get_msg.status_code == 200 and get_msg.json().get("ok"):
        old_text = get_msg.json()["result"]["text"]
        new_text = old_text.replace("🆕 <b>НОВЫЙ ЗАКАЗ", f"🔄 <b>ЗАКАЗ {status_text.upper()}</b>")
        
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/editMessageText",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": new_text,
                "parse_mode": "HTML"
            }
        )
    
    # Отвечаем на callback
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
        json={
            "callback_query_id": callback["id"],
            "text": f"Статус изменён на \"{status_text}\"",
            "show_alert": False
        }
    )
    
    # Уведомляем пользователя
    if order and order.get("user_tg_id"):
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": order["user_tg_id"],
                "text": f"🔄 Статус вашего заказа #{order_id} изменён на \"{status_text}\"",
                "parse_mode": "HTML"
            }
        )
    
    return {"status": "ok"}, 200

# ===== Запуск сервера =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
