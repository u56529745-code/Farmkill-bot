import telebot
from telebot import types

# ============ НАСТРОЙКИ ============
TOKEN = "8814067918:AAHVt-7m6mCafGS8sCAuOE8N2SqNma_cvZM"
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

# ============ ГЛАВНОЕ МЕНЮ ============
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👑 VIP", callback_data="menu_vip"),
        types.InlineKeyboardButton("⭐ Звёзды", callback_data="menu_stars"),
        types.InlineKeyboardButton("💎 Алмазы", callback_data="menu_diamonds"),
        types.InlineKeyboardButton("⚜️ Руны", callback_data="menu_runes"),
        types.InlineKeyboardButton("📱 Premium", callback_data="menu_premium"),
        types.InlineKeyboardButton("📦 Расходники", callback_data="menu_consumables"),
    )
    return markup

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я помогу с выбором и валютой.\n\nВыбери ниже, что хочешь:",
        reply_markup=main_menu()
    )

# ============ VIP ============
def vip_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("VIP 1", callback_data="vip_1"),
        types.InlineKeyboardButton("VIP 2", callback_data="vip_2"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_vip")
def menu_vip(call):
    bot.edit_message_text(
        "👑 VIP\n\nВыбери вариант:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=vip_menu()
    )

@bot.message_handler(commands=['vip'])
def vip_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        bot.send_message(message.chat.id, "👑 VIP\n\nВыбери вариант:", reply_markup=vip_menu())
        return
    level = args[1]
    if level == "1":
        send_vip(message.chat.id, 1)
    elif level == "2":
        send_vip(message.chat.id, 2)
    else:
        bot.send_message(message.chat.id, "❌ Укажи /vip 1 или /vip 2")

def send_vip(chat_id, level):
    silver = VIP[level] * DIAMOND_TO_SILVER
    title = f"👑 VIP {level} (1 месяц)"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_vip"))
    bot.send_message(chat_id, block("✦", title, silver), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vip_"))
def vip_callback(call):
    level = int(call.data.split("_")[1])
    silver = VIP[level] * DIAMOND_TO_SILVER
    title = f"👑 VIP {level} (1 месяц)"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_vip"))
    bot.send_message(call.message.chat.id, block("✦", title, silver), reply_markup=markup)

# ============ STARS ============
def stars_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("100", callback_data="stars_100"),
        types.InlineKeyboardButton("250", callback_data="stars_250"),
        types.InlineKeyboardButton("500", callback_data="stars_500"),
        types.InlineKeyboardButton("1000", callback_data="stars_1000"),
        types.InlineKeyboardButton("2500", callback_data="stars_2500"),
        types.InlineKeyboardButton("10000", callback_data="stars_10000"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_stars")
def menu_stars(call):
    bot.edit_message_text(
        "⭐ Звёзды\n\nВыбери количество:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=stars_menu()
    )

@bot.message_handler(commands=['stars'])
def stars_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        bot.send_message(message.chat.id, "⭐ Звёзды\n\nВыбери количество:", reply_markup=stars_menu())
        return
    try:
        amount = int(args[1])
    except:
        bot.send_message(message.chat.id, "❌ Укажи число: /stars 10000")
        return
    send_stars(message.chat.id, amount)

def send_stars(chat_id, amount):
    if amount not in STARS:
        bot.send_message(chat_id, "❌ Доступно: 100, 250, 500, 1000, 2500, 10000")
        return
    silver = STARS[amount] * RUB_TO_SILVER
    title = f"⭐ {amount} звёзд"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_stars"))
    if amount == 10000:
        bot.send_message(chat_id, block_best("⭐", title, silver), reply_markup=markup)
    else:
        bot.send_message(chat_id, block("⭐", title, silver), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("stars_"))
def stars_callback(call):
    amount = int(call.data.split("_")[1])
    send_stars(call.message.chat.id, amount)

# ============ DIAMONDS ============
def diamonds_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("100", callback_data="dia_100"),
        types.InlineKeyboardButton("300", callback_data="dia_300"),
        types.InlineKeyboardButton("500", callback_data="dia_500"),
        types.InlineKeyboardButton("1000", callback_data="dia_1000"),
        types.InlineKeyboardButton("2500", callback_data="dia_2500"),
        types.InlineKeyboardButton("5000", callback_data="dia_5000"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_diamonds")
def menu_diamonds(call):
    bot.edit_message_text(
        "💎 Алмазы\n\nВыбери количество:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=diamonds_menu()
    )

@bot.message_handler(commands=['diamonds'])
def diamonds_cmd(message):
    bot.send_message(message.chat.id, "💎 Алмазы\n\nВыбери количество:", reply_markup=diamonds_menu())

def send_diamonds(chat_id, amount):
    silver = amount * DIAMOND_TO_SILVER
    title = f"💎 {amount} алмазов"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_diamonds"))
    if amount == 5000:
        bot.send_message(chat_id, block_best("💎", title, silver), reply_markup=markup)
    else:
        bot.send_message(chat_id, block("💎", title, silver), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dia_"))
def diamonds_callback(call):
    amount = int(call.data.split("_")[1])
    send_diamonds(call.message.chat.id, amount)

# ============ RUNES ============
def runes_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Руна сохранения", callback_data="rune_save"),
        types.InlineKeyboardButton("Руна защиты", callback_data="rune_prot"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_runes")
def menu_runes(call):
    bot.edit_message_text(
        "⚜️ Руны\n\nВыбери руну:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=runes_menu()
    )

@bot.message_handler(commands=['rune'])
def rune_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        bot.send_message(message.chat.id, "⚜️ Руны\n\nВыбери руну:", reply_markup=runes_menu())
        return
    key = args[1].lower()
    if key in ("save", "сохр"):
        send_rune(message.chat.id, "save")
    elif key in ("prot", "защ"):
        send_rune(message.chat.id, "prot")
    else:
        bot.send_message(message.chat.id, "❌ /rune save или /rune prot")

def send_rune(chat_id, key):
    silver = RUNES[key] * DIAMOND_TO_SILVER
    title = "🧿 Руна сохранения" if key == "save" else "🧿 Руна защиты"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_runes"))
    bot.send_message(chat_id, block("⚜️", title, silver), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rune_"))
def rune_callback(call):
    key = call.data.split("_")[1]
    send_rune(call.message.chat.id, key)

# ============ PREMIUM ============
def premium_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("3 мес", callback_data="prem_3"),
        types.InlineKeyboardButton("6 мес", callback_data="prem_6"),
        types.InlineKeyboardButton("12 мес", callback_data="prem_12"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_premium")
def menu_premium(call):
    bot.edit_message_text(
        "📱 Telegram Premium\n\nВыбери срок:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=premium_menu()
    )

@bot.message_handler(commands=['premium'])
def premium_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        bot.send_message(message.chat.id, "📱 Telegram Premium\n\nВыбери срок:", reply_markup=premium_menu())
        return
    try:
        months = int(args[1])
    except:
        bot.send_message(message.chat.id, "❌ Укажи срок: /premium 12")
        return
    send_premium(message.chat.id, months)

def send_premium(chat_id, months):
    if months not in PREMIUM:
        bot.send_message(chat_id, "❌ Доступно: 3, 6, 12")
        return
    silver = PREMIUM[months] * RUB_TO_SILVER
    title = f"📱 Telegram Premium ({months} мес)"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_premium"))
    if months == 12:
        bot.send_message(chat_id, block_best("💠", title, silver), reply_markup=markup)
    else:
        bot.send_message(chat_id, block("💠", title, silver), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("prem_"))
def premium_callback(call):
    months = int(call.data.split("_")[1])
    send_premium(call.message.chat.id, months)

# ============ CONSUMABLES ============
def consumables_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🧪 Бирка", callback_data="cons_tag"),
        types.InlineKeyboardButton("🧪 Камень очищения", callback_data="cons_stone"),
        types.InlineKeyboardButton("🧪 Жетон имени", callback_data="cons_token"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_consumables")
def menu_consumables(call):
    bot.edit_message_text(
        "📦 Расходники\n\nВыбери предмет:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=consumables_menu()
    )

def send_consumable(chat_id, key):
    silver = CONSUMABLES[key] * DIAMOND_TO_SILVER
    titles = {
        "stone": "🧪 Камень очищения",
        "tag": "🧪 Бирка",
        "token": "🧪 Жетон смены имени",
    }
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_consumables"))
    bot.send_message(chat_id, block("📦", titles[key], silver), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cons_"))
def consumables_callback(call):
    key = call.data.split("_")[1]
    send_consumable(call.message.chat.id, key)

@bot.message_handler(commands=['stone'])
def stone_cmd(message):
    send_consumable(message.chat.id, "stone")

@bot.message_handler(commands=['tag'])
def tag_cmd(message):
    send_consumable(message.chat.id, "tag")

@bot.message_handler(commands=['token'])
def token_cmd(message):
    send_consumable(message.chat.id, "token")

# ============ НАЗАД В ГЛАВНОЕ ============
@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    bot.edit_message_text(
        "👋 Привет! Я помогу с выбором и валютой.\n\nВыбери ниже, что хочешь:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu()
    )

# ============ НЕИЗВЕСТНАЯ КОМАНДА ============
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
