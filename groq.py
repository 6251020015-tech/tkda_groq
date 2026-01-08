import requests
import time
import threading
from flask import Flask

# ===== GROQ CONFIG =====
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"   # MODEL ĐÚNG 100%

# ===== BLYNK CONFIG =====
BLYNK_TOKEN = "GB3AxX2_BzZyYvpIbXqFFzygRNooh4QS"
BLYNK_BASE_URL = "https://blynk.cloud/external/api"

app = Flask(__name__)

# ---------- BLYNK FUNCTIONS ----------
def get_value(pin):
    url = f"{BLYNK_BASE_URL}/get?token={BLYNK_TOKEN}&{pin}"
    res = requests.get(url)
    if res.status_code == 200 and res.text.strip() != "":
        return res.text.strip()
    return ""

def set_value(pin, val):
    url = f"{BLYNK_BASE_URL}/update?token={BLYNK_TOKEN}&{pin}={val}"
    requests.get(url)

def write_output_long(msg, chunk_size=200):
    parts = [msg[i:i + chunk_size] for i in range(0, len(msg), chunk_size)]
    for p in parts:
        set_value("V6", p)
        time.sleep(0.2)

def clear_input():
    set_value("V5", "")

# ---------- GROQ AI FUNCTION ----------
def ask_groq(prompt, history):
    messages = []

    for item in history:
        messages.append({"role": item["role"], "content": item["content"]})

    messages.append({"role": "user", "content": prompt})

    payload = {"model": MODEL, "messages": messages}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    res = requests.post(GROQ_URL, json=payload, headers=headers)

    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]

    return f"⚠️ Groq API Error: {res.text}"

# ---------- MAIN LOOP ----------
def main_loop():
    conversation_history = []
    print("🤖 Bot Groq AI đã khởi động!")

    while True:
        try:
            temp = get_value("V1")
            hum = get_value("V2")
            soil = get_value("V3")

            # --- AI Auto Mode ---
            if get_value("V7") == "1":
                prompt = f"""
                Đây là dữ liệu cảm biến:
                - Nhiệt độ: {temp} °C
                - Độ ẩm không khí: {hum} %
                - Độ ẩm đất: {soil} %

                Hãy phân tích tình trạng môi trường và đưa ra lời khuyên tưới tiêu hợp lý, nên tưới nớc hay không, trả lời ngắn gọn 20 .
                """

                reply = ask_groq(prompt, conversation_history)
                write_output_long(reply)

                conversation_history.append({"role": "user", "content": prompt})
                conversation_history.append({"role": "assistant", "content": reply})

                set_value("V7", "0")

            # --- Manual Ask ---
            user_input = get_value("V5")
            if user_input:
                reply = ask_groq(user_input, conversation_history)
                write_output_long(reply)

                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": reply})

                clear_input()

            time.sleep(1)

        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(2)

@app.route("/")
def home():
    return "✅ Bot Groq AI đang chạy!"

if __name__ == "__main__":
    thread = threading.Thread(target=main_loop, daemon=True)
    thread.start()

    app.run(host="0.0.0.0", port=10000)
