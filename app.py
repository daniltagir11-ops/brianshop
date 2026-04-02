from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import hashlib
import hmac

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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ========== РЕГИСТРАЦИЯ С ПАРОЛЕМ ==========
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.json
        tg_id = data.get("tgId")
        username = data.get("username", "")
        first_name = data.get("firstName", "")
        password = data.get("password", "")
        
        if not tg_id or not password:
            return jsonify({"success": False, "error": "Missing tgId or password"}), 400
        
        headers = supabase_headers()
        
        # Проверяем, существует ли пользователь
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?tg_id=eq.{tg_id}&select=*",
            headers=headers
        )
        
        if response.status_code == 200 and response.json():
            return jsonify({"success": False, "error": "User already exists"}), 400
        
        # Создаём пользователя с паролем
        referral_code = str(tg_id)[:8] + "X"
        payload = {
            "tg_id": tg_id,
            "username": username,
            "first_name": first_name,
            "referral_code": referral_code,
            "balance": 0,
            "is_admin": False,
            "password": hash_password(password)
        }
        
        create_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            json=payload
        )
        
        if create_response.status_code in [200, 201]:
            return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Failed to create user"}), 500
        
    except Exception as e:
        print(f"Error in /register: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ========== ЛОГИН С ПАРОЛЕМ ==========
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        tg_id = data.get("tgId")
        password = data.get("password")
        
        if not tg_id or not password:
            return jsonify({"success": False, "error": "Missing tgId or password"}), 400
        
        headers = supabase_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?tg_id=eq.{tg_id}&select=*",
            headers=headers
        )
        
        if response.status_code != 200 or not response.json():
            return jsonify({"success": False, "error": "User not found"}), 404
        
        user = response.json()[0]
        stored_hash = user.get("password", "")
        
        if stored_hash and stored_hash == hash_password(password):
            return jsonify({"success": True, "user": user})
        
        return jsonify({"success": False, "error": "Invalid password"}), 401
        
    except Exception as e:
        print(f"Error in /login: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ========== ПРОВЕРКА СУЩЕСТВОВАНИЯ ПОЛЬЗОВАТЕЛЯ ==========
@app.route("/check-user", methods=["POST"])
def check_user():
    try:
        data = request.json
        tg_id = data.get("tgId")
        
        if not tg_id:
            return jsonify({"exists": False}), 400
        
        headers = supabase_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?tg_id=eq.{tg_id}&select=*",
            headers=headers
        )
        
        if response.status_code == 200 and response.json():
            user = response.json()[0]
            return jsonify({"exists": True, "hasPassword": bool(user.get("password"))})
        
        return jsonify({"exists": False})
        
    except Exception as e:
        print(f"Error in /check-user: {e}")
        return jsonify({"exists": False}), 500

# ========== ПОЛУЧЕНИЕ ПОГОДЫ ==========
WEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"  # Замени на свой ключ

@app.route("/weather", methods=["POST"])
def get_weather():
    try:
        data = request.json
        lat = data.get("lat")
        lon = data.get("lon")
        
        if not lat or not lon:
            return jsonify({"success": False, "error": "No coordinates"}), 400
        
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        
        if response.status_code == 200:
            weather_data = response.json()
            weather_main = weather_data.get("weather", [{}])[0].get("main", "").lower()
            temp = weather_data.get("main", {}).get("temp", 0)
            
            # Определяем тип погоды
            if weather_main in ["clear"]:
                weather_type = "sunny"
            elif weather_main in ["rain", "drizzle", "thunderstorm"]:
                weather_type = "rainy"
            elif weather_main in ["snow"]:
                weather_type = "snowy"
            else:
                weather_type = "cloudy"
            
            return jsonify({
                "success": True,
                "weather": weather_type,
                "temp": temp,
                "description": weather_data.get("weather", [{}])[0].get("description", "")
            })
        
        return jsonify({"success": False, "error": "Weather API error"}), 500
        
    except Exception as e:
        print(f"Error in /weather: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ========== ОСТАЛЬНЫЕ ЭНДПОИНТЫ (заказы, корзины и т.д.) ==========
# ... (оставляем все предыдущие эндпоинты без изменений)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
