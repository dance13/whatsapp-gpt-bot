from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@app.route("/webhook", methods=["GET"])
def verify():
    # VERIFY TOKEN HANDSHAKE
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # Проверяем входящие сообщения
    if data and "entry" in data:
        for entry in data["entry"]:
            for change in entry["changes"]:
                value = change.get("value")
                if value and "messages" in value:
                    for msg in value["messages"]:
                        if msg.get("type") == "text":
                            user_text = msg["text"]["body"]
                            from_number = msg["from"]

                            # Генерируем ответ через OpenAI
                            ai_response = chat_with_openai(user_text)

                            # Отправляем обратно в WhatsApp
                            send_message(from_number, ai_response)

    return jsonify({"status": "ok"}), 200


def chat_with_openai(user_text):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Ты — ассистент компании."},
            {"role": "user", "content": user_text}
        ]
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        json=data,
        headers=headers
    )

    result = response.json()
    reply = result["choices"][0]["message"]["content"]
    return reply


def send_message(to, message):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    requests.post(url, json=data, headers=headers)


if __name__ == "__main__":
    app.run(port=5000)
