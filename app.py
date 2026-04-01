from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json

app = Flask(__name__)
CORS(app)

# ===== Настройки =====
TOKEN = "8486993696:AAFLyvI3lbMYltXTKXVSbMj552dcXaXwgRI"
CHAT_ID = -1003816309605

SUPABASE_URL = "https://perxwqxtzgbvswimmkgt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBlcnh3cXh0emdidnN3aW1ta2d0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwNTY1NTYsImV4cCI6MjA5MDYzMjU1Nn0.dmR6UpUOHsYgPgr8k9wWWiqdNhfGq38Qjk5so1l37YY"

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

# ========== ЭНДПОИНТЫ ДЛЯ ПРОФИЛЯ ==========

@app.route("/user", methods=["POST"])
def user():
    try:
        data = request.json
        tg_id = data.get("tgId")
        username = data.get("username", "")
        first_name = data.get("firstName", "")
        
        if not tg_id:
            return jsonify({"success": False, "error": "No tgId"}), 400
        
        headers = supabase_headers()
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?tg_id=eq.{tg_id}&select=*",
            headers=headers
        )
        
        if response.status_code == 200 and response.json():
            user_data = response.json()[0]
            return jsonify({"success": True, "user": user_data})
        
        referral_code = str(tg_id)[:8] + "X"
        payload = {
            "tg_id": tg_id,
            "username": username,
            "first_name": first_name,
            "referral_code": referral_code,
            "balance": 0,
            "is_admin": False
        }
        
        create_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            json=payload
        )
        
        if create_response.status_code in [200, 201]:
            get_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/users?tg_id=eq.{tg_id}&select=*",
                headers=headers
            )
            if get_response.status_code == 200 and get_response.json():
                return jsonify({"success": True, "user": get_response.json()[0]})
        
        return jsonify({"success": False, "error": "Failed to create user"}), 500
        
    except Exception as e:
        print(f"Error in /user: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/orders", methods=["POST"])
def get_orders():
    try:
        data = request.json
        tg_id = data.get("tgId")
        
        if not tg_id:
            return jsonify({"success": False, "orders": []}), 400
        
        headers = supabase_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/orders?user_tg_id=eq.{tg_id}&order=created_at.desc",
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify({"success": True, "orders": response.json()})
        
        return jsonify({"success": False, "orders": []}), 500
        
    except Exception as e:
        print(f"Error in /orders: {e}")
        return jsonify({"success": False, "orders": []}), 500


@app.route("/stats", methods=["POST"])
def get_stats():
    try:
        data = request.json
        tg_id = data.get("tgId")
        
        if not tg_id:
            return jsonify({"success": False, "stats": {"orders_count": 0, "total_spent": 0}}), 400
        
        headers = supabase_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/orders?user_tg_id=eq.{tg_id}&select=total,status",
            headers=headers
        )
        
        orders = response.json() if response.status_code == 200 else []
        total_spent = sum(o.get("total", 0) for o in orders if o.get("status") == "completed")
        
        return jsonify({
            "success": True,
            "stats": {
                "orders_count": len(orders),
                "total_spent": total_spent
            }
        })
        
    except Exception as e:
        print(f"Error in /stats: {e}")
        return jsonify({"success": False, "stats": {"orders_count": 0, "total_spent": 0}}), 500


@app.route("/save-cart", methods=["POST"])
def save_cart():
    try:
        data = request.json
        user_tg_id = data.get("userTgId")
        name = data.get("name")
        items = data.get("items")
        
        if not user_tg_id:
            return jsonify({"success": False}), 400
        
        headers = supabase_headers()
        payload = {
            "user_tg_id": user_tg_id,
            "name": name,
            "items": json.dumps(items)
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/saved_carts",
            headers=headers,
            json=payload
        )
        
        return jsonify({"success": response.status_code in [200, 201]})
        
    except Exception as e:
        print(f"Error in /save-cart: {e}")
        return jsonify({"success": False}), 500


@app.route("/get-carts", methods=["POST"])
def get_carts():
    try:
        data = request.json
        user_tg_id = data.get("userTgId")
        
        if not user_tg_id:
            return jsonify({"success": False, "carts": []}), 400
        
        headers = supabase_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/saved_carts?user_tg_id=eq.{user_tg_id}&order=created_at.desc",
            headers=headers
        )
        
        if response.status_code == 200:
            carts = response.json()
            for cart in carts:
                if isinstance(cart.get("items"), str):
                    try:
                        cart["items"] = json.loads(cart["items"])
                    except:
                        cart["items"] = []
            return jsonify({"success": True, "carts": carts})
        
        return jsonify({"success": False, "carts": []}), 500
        
    except Exception as e:
        print(f"Error in /get-carts: {e}")
        return jsonify({"success": False, "carts": []}), 500


@app.route("/delete-cart", methods=["POST"])
def delete_cart():
    try:
        data = request.json
        cart_id = data.get("cartId")
        
        if not cart_id:
            return jsonify({"success": False}), 400
        
        headers = supabase_headers()
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/saved_carts?id=eq.{cart_id}",
            headers=headers
        )
        
        return jsonify({"success": response.status_code == 200})
        
    except Exception as e:
        print(f"Error in /delete-cart: {e}")
        return jsonify({"success": False}), 500


# ========== ОСНОВНОЙ ЭНДПОИНТ ДЛЯ ЗАКАЗОВ ==========

@app.route("/send-order", methods=["POST"])
def send_order():
    try:
        data = request.json

        if not data:
            return jsonify({"success": False, "error": "No data received"}), 400

        headers = supabase_headers()
        payload = {
            "order_number": data.get("orderId"),
            "user_tg_id": int(data.get("tgId")),
            "items": json.dumps(data.get("items")),
            "total": data.get("total"),
            "status": "pending"
        }
        
        supabase_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/orders",
            headers=headers,
            json=payload
        )
        
        print(f"Supabase save: {supabase_response.status_code}")

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

        inline_keyboard = {
            "inline_keyboard": [[
                {"text": "👀 Просмотрено", "callback_data": f"view_{data.get('orderId', '')}"},
                {"text": "✅ Оплачен", "callback_data": f"paid_{data.get('orderId', '')}"},
                {"text": "📦 Выполнен", "callback_data": f"done_{data.get('orderId', '')}"}
            ]]
        }

        tg_response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": inline_keyboard
            }
        )
        
        print(f"Telegram send: {tg_response.status_code}")

        return jsonify({"success": True})

    except Exception as e:
        print(f"Error in /send-order: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ========== WEBHOOK ДЛЯ КНОПОК ==========

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    try:
        update = request.json
        
        print(f"Webhook received: {update}")
        
        if not update or "callback_query" not in update:
            return jsonify({"status": "ok"}), 200
        
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
            return jsonify({"status": "ok"}), 200
        
        new_status, status_text = status_map[action]
        
        headers = supabase_headers()
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/orders?order_number=eq.{order_id}",
            headers=headers,
            json={"status": new_status}
        )
        
        order_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/orders?order_number=eq.{order_id}&select=*",
            headers=headers
        )
        order = order_response.json()[0] if order_response.status_code == 200 and order_response.json() else None
        
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
        
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
            json={
                "callback_query_id": callback["id"],
                "text": f"Статус изменён на \"{status_text}\"",
                "show_alert": False
            }
        )
        
        if order and order.get("user_tg_id"):
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={
                    "chat_id": order["user_tg_id"],
                    "text": f"🔄 Статус вашего заказа #{order_id} изменён на \"{status_text}\"",
                    "parse_mode": "HTML"
                }
            )
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Error in webhook: {e}")
        return jsonify({"status": "ok"}), 200


# ========== УСТАНОВКА WEBHOOK ПРИ ЗАПУСКЕ ==========
def set_webhook():
    try:
        url = "https://api.telegram.org/bot8486993696:AAFLyvI3lbMYltXTKXVSbMj552dcXaXwgRI/setWebhook"
        webhook_url = "https://brianshop-production.up.railway.app/webhook"
        allowed_updates = ["message", "callback_query"]
        response = requests.post(url, json={"url": webhook_url, "allowed_updates": allowed_updates})
        print("Webhook set:", response.json())
    except Exception as e:
        print(f"Error setting webhook: {e}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
