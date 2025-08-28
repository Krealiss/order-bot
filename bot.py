import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "5302824520:AAG6D_Rjn0atmuB99G3U9drbzpaF_hXhMeI"
CHAT_ID = "577102344"
bot = telebot.TeleBot(BOT_TOKEN)

app = FastAPI()

# ✅ Дозволяємо CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # або твій фронтенд домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Обробка замовлень з сайту ===
@app.post("/order")
async def new_order(request: Request):
    data = await request.json()
    name = data["name"]
    phone = data["phone"]
    qty = data["qty"]
    delivery = data["delivery"]
    address = data["address"]
    contact_method = data["contactMethod"]
    total = data["total"]

    now = datetime.datetime.now()
    date = now.strftime("%d.%m.%Y")
    time = now.strftime("%H:%M:%S")
    order_number = f"#{now.strftime('%Y%m%d%H%M%S')}"

    delivery_text = {
        "0": "Самовивіз (0 грн)",
        "80": "Нова пошта (80 грн)",
        "60": "Укрпошта (60 грн)"
    }.get(delivery, "Невідомо")

    message = f"""
🛒 НОВЕ ЗАМОВЛЕННЯ {order_number}
📅 Дата: {date}
⏰ Час: {time}

👤 Ім'я: {name}
📞 Телефон: {phone}
💬 Зв'язок: {contact_method}
📦 Кількість: {qty}
🚚 Доставка: {delivery_text}
🏠 Адреса: {address}
💰 Сума: {total} грн

📌 Статус: Нове (неопрацьоване)
    """

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Відмітити", callback_data=f"mark_{order_number}"))

    bot.send_message(CHAT_ID, message, reply_markup=markup)

    return JSONResponse(content={"status": "ok", "orderNumber": order_number})


# === Обробка callback від Telegram ===
@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    json_str = await request.body()
    update = telebot.types.Update.de_json(json_str.decode("utf-8"))
    bot.process_new_updates([update])
    return "!", 200


# === Кнопки ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("mark_"))
def callback_mark(call):
    order_id = call.data.split("_")[1]

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Так", callback_data=f"confirm_{order_id}_yes"),
        InlineKeyboardButton("❌ Ні", callback_data=f"confirm_{order_id}_no")
    )

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def callback_confirm(call):
    _, order_id, answer = call.data.split("_")

    if answer == "yes":
        now = datetime.datetime.now().strftime("%d.%m %H:%M")
        text_lines = call.message.text.split("\n")
        for i, line in enumerate(text_lines):
            if line.startswith("📌 Статус:"):
                text_lines[i] = f"📌 Статус: ✅ Опрацьоване ({now})"
        updated_text = "\n".join(text_lines)

        bot.edit_message_text(
            updated_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Відмітити", callback_data=f"mark_{order_id}"))

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )