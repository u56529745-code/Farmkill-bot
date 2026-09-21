import telebot
from telebot import types

# ============ НАСТРОЙКИ ============
TOKEN = "8814067918:AAFap4BhU5KQ1HjsK0YpwmG9vSYaRTRtYaI"
bot = telebot.TeleBot(TOKEN)

# ============ КУРСЫ ============
RUB_TO_SILVER = 16700
DIAMOND_TO_SILVER = 16700

# ============ ЦЕНЫ ============
STARS = {
    100: 181.99,
    250: 429.00,
    500: 849.00,
    1000: 1679.00,
    2500: 4199.00,
    10000: 16599.00,
}

DIAMONDS = {
    100: 100,
    300: 300,
    500: 500,
    1000: 1000,
    2500: 2500,
    5000: 5000,
}

VIP = {
    1: 2400,
    2: 1500,
}

PREMIUM = {
    3: 1049.00,
    6: 1399.00,
    12: 2539.00,
}

RUNES = {
    "save": 240,
    "prot": 240,
}

CONSUMABLES = {
    "stone": 160,
    "tag": 100,
    "token": 200,
}

# ============ ФОРМАТИРОВАНИЕ ============
def fmt(num):
    if num >= 1_000_000:
        return f"{num / 1_000_000:.2f} млн"
    elif num >= 1_000:
        return f"{num / 1_000:.2f}к"
    return str(num)

def block(symbol, title, silver):
    return (
        f"{symbol}━━━━━━━━━━━━━━━━━━{symbol}\n"
        f"{title}\n"
        f"💰 {fmt(silver)} серебра\n"
        f"{symbol}━━━━━━━━━━━━━━━━━━{symbol}"
    )

def block_best(symbol, title, silver):
    return (
        f"🟢━━━━━━━━━━━━━━━━━━{symbol}\n"
        f"{title}\n"
        f"💰 {fmt(silver)} серебра\n"
        f"{symbol}━━━━━━━━━━━━━━━━━━🟢\n"
        f"💸 Выгодно"
    )

# ============ КОМАНДЫ ============
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 Привет! Я бот-калькулятор Farmkill.\n\n"
        "📋 Команды:\n"
        "/vip — VIP 1 и VIP 2\n"
        "/vip 1 — VIP 1\n"
        "/vip 2 — VIP 2\n"
        "/stars — звёзды (выбор)\n"
        "/stars 10000 — 10000 звёзд\n"
        "/rune — руны (выбор)\n"
        "/rune save — руна сохранения\n"
        "/rune prot — руна защиты\n"
        "/premium — Telegram Premium (выбор)\n"
        "/diamonds — алмазы (выбор)\n"
        "/stone — камень очищения\n"
        "/tag — бирка\n"
        "/token — жетон смены имени\n"
    )
    bot.send_message(message.chat.id, text)

# ----- VIP -----
@bot.message_handler(commands=['vip'])
def vip_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("VIP 1", callback_data="vip_1"),
            types.InlineKeyboardButton("VIP 2", callback_data="vip_2"),
        )
        bot.send_message(message.chat.id, "Выбери VIP:", reply_markup=markup)
        return
    level = args[1]
    if level == "1":
        send_vip(message, 1)
    elif level == "2":
        send_vip(message, 2)
    else:
        bot.send_message(message.chat.id, "❌ Укажи /vip 1 или /vip 2")

def send_vip(message, level):
    silver = VIP[level] * DIAMOND_TO_SILVER
    title = f"👑 VIP {level} (1 месяц)"
    bot.send_message(message.chat.id, block("✦", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("vip_"))
def vip_callback(call):
    level = int(call.data.split("_")[1])
    silver = VIP[level] * DIAMOND_TO_SILVER
    title = f"👑 VIP {level} (1 месяц)"
    bot.send_message(call.message.chat.id, block("✦", title, silver))

# ----- STARS -----
@bot.message_handler(commands=['stars'])
def stars_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("100", callback_data="stars_100"),
            types.InlineKeyboardButton("250", callback_data="stars_250"),
            types.InlineKeyboardButton("500", callback_data="stars_500"),
        )
        markup.add(
            types.InlineKeyboardButton("1000", callback_data="stars_1000"),
            types.InlineKeyboardButton("2500", callback_data="stars_2500"),
            types.InlineKeyboardButton("10000", callback_data="stars_10000"),
        )
        bot.send_message(message.chat.id, "Выбери количество звёзд:", reply_markup=markup)
        return
    try:
        amount = int(args[1])
    except:
        bot.send_message(message.chat.id, "❌ Укажи число: /stars 10000")
        return
    send_stars(message, amount)

def send_stars(message, amount):
    if amount not in STARS:
        bot.send_message(message.chat.id, "❌ Доступно: 100, 250, 500, 1000, 2500, 10000")
        return
    silver = STARS[amount] * RUB_TO_SILVER
    title = f"⭐ {amount} звёзд"
    if amount == 10000:
        bot.send_message(message.chat.id, block_best("⭐", title, silver))
    else:
        bot.send_message(message.chat.id, block("⭐", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("stars_"))
def stars_callback(call):
    amount = int(call.data.split("_")[1])
    send_stars(call.message, amount)

# ----- RUNES -----
@bot.message_handler(commands=['rune'])
def rune_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Руна сохранения", callback_data="rune_save"),
            types.InlineKeyboardButton("Руна защиты", callback_data="rune_prot"),
        )
        bot.send_message(message.chat.id, "Выбери руну:", reply_markup=markup)
        return
    key = args[1].lower()
    if key in ("save", "сохр"):
        send_rune(message, "save")
    elif key in ("prot", "защ"):
        send_rune(message, "prot")
    else:
        bot.send_message(message.chat.id, "❌ /rune save или /rune prot")

def send_rune(message, key):
    silver = RUNES[key] * DIAMOND_TO_SILVER
    title = "🧿 Руна сохранения" if key == "save" else "🧿 Руна защиты"
    bot.send_message(message.chat.id, block("⚜️", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("rune_"))
def rune_callback(call):
    key = call.data.split("_")[1]
    send_rune(call.message, key)

# ----- PREMIUM -----
@bot.message_handler(commands=['premium'])
def premium_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("3 месяца", callback_data="prem_3"),
            types.InlineKeyboardButton("6 месяцев", callback_data="prem_6"),
            types.InlineKeyboardButton("12 месяцев", callback_data="prem_12"),
        )
        bot.send_message(message.chat.id, "Выбери срок Premium:", reply_markup=markup)
        return
    try:
        months = int(args[1])
    except:
        bot.send_message(message.chat.id, "❌ Укажи срок: /premium 12")
        return
    send_premium(message, months)

def send_premium(message, months):
    if months not in PREMIUM:
        bot.send_message(message.chat.id, "❌ Доступно: 3, 6, 12")
        return
    silver = PREMIUM[months] * RUB_TO_SILVER
    title = f"📱 Telegram Premium ({months} мес)"
    if months == 12:
        bot.send_message(message.chat.id, block_best("💠", title, silver))
    else:
        bot.send_message(message.chat.id, block("💠", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("prem_"))
def premium_callback(call):
    months = int(call.data.split("_")[1])
    send_premium(call.message, months)

# ----- DIAMONDS -----
@bot.message_handler(commands=['diamonds'])
def diamonds_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("100", callback_data="dia_100"),
            types.InlineKeyboardButton("300", callback_data="dia_300"),
            types.InlineKeyboardButton("500", callback_data="dia_500"),
        )
        markup.add(
            types.InlineKeyboardButton("1000", callback_data="dia_1000"),
            types.InlineKeyboardButton("2500", callback_data="dia_2500"),
            types.InlineKeyboardButton("5000", callback_data="dia_5000"),
        )
        bot.send_message(message.chat.id, "Выбери количество алмазов:", reply_markup=markup)
        return

def send_diamonds(message, amount):
    silver = amount * DIAMOND_TO_SILVER
    title = f"💎 {amount} алмазов"
    if amount == 5000:
        bot.send_message(message.chat.id, block_best("💎", title, silver))
    else:
        bot.send_message(message.chat.id, block("💎", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("dia_"))
def diamonds_callback(call):
    amount = int(call.data.split("_")[1])
    send_diamonds(call.message, amount)

# ----- CONSUMABLES -----
@bot.message_handler(commands=['stone'])
def stone_cmd(message):
    silver = CONSUMABLES["stone"] * DIAMOND_TO_SILVER
    bot.send_message(message.chat.id, block("📦", "🧪 Камень очищения", silver))

@bot.message_handler(commands=['tag'])
def tag_cmd(message):
    silver = CONSUMABLES["tag"] * DIAMOND_TO_SILVER
    bot.send_message(message.chat.id, block("📦", "🧪 Бирка", silver))

@bot.message_handler(commands=['token'])
def token_cmd(message):
    silver = CONSUMABLES["token"] * DIAMOND_TO_SILVER
    bot.send_message(message.chat.id, block("📦", "🧪 Жетон смены имени", silver))

# ----- НЕИЗВЕСТНАЯ КОМАНДА -----
@bot.message_handler(func=lambda message: True)
def unknown(message):
    bot.send_message(
        message.chat.id,
        "❌ Команда не распознана.\n"
        "Напишите ещё раз и проверьте написание\n"
        "или дождитесь @yra228kil1"
    )

# ============ ЗАПУСК ============
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
