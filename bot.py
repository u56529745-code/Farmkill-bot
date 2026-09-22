import telebot
from telebot import types
import threading
import time
import os
from flask import Flask

# ============ НАСТРОЙКИ ============
TOKEN = "8814067918:AAE_D2BAXH6UcIUhsXytIPOmoEkEH4srnq8"
bot = telebot.TeleBot(TOKEN)

# ============ ВЕБ-СЕРВЕР ДЛЯ RENDER ============
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ============ КУРСЫ ============
RUB_TO_SILVER = 16700
DIAMOND_TO_SILVER = 16700

# ============ ЦЕНЫ ============
STARS = {100: 181.99, 250: 429.00, 500: 849.00, 1000: 1679.00, 2500: 4199.00, 10000: 16599.00}
DIAMONDS = {100: 100, 300: 300, 500: 500, 1000: 1000, 2500: 2500, 5000: 5000}
VIP = {1: 2400, 2: 1500}
PREMIUM = {3: 1049.00, 6: 1399.00, 12: 2539.00}
RUNES = {"save": 240, "prot": 240}
CONSUMABLES = {"stone": 160, "tag": 100, "token": 200}

# ============ БАЗА ТОВАРОВ ============
ITEMS = {}

for lvl, dia in VIP.items():
    ITEMS[f"vip_{lvl}"] = (f"👑 VIP {lvl} (1 месяц)", dia * DIAMOND_TO_SILVER)

for amt, rub in STARS.items():
    ITEMS[f"stars_{amt}"] = (f"⭐ {amt} звёзд", int(rub * RUB_TO_SILVER))

for amt in DIAMONDS:
    ITEMS[f"dia_{amt}"] = (f"💎 {amt} алмазов", amt * DIAMOND_TO_SILVER)

for m, rub in PREMIUM.items():
    ITEMS[f"prem_{m}"] = (f"💠 Telegram Premium ({m} мес)", int(rub * RUB_TO_SILVER))

for k, dia in RUNES.items():
    name = "🧿 Руна сохранения" if k == "save" else "🧿 Руна защиты"
    ITEMS[f"rune_{k}"] = (name, dia * DIAMOND_TO_SILVER)

for k, dia in CONSUMABLES.items():
    names = {"stone": "🧪 Камень очищения", "tag": "🧪 Бирка", "token": "🧪 Жетон смены имени"}
    ITEMS[f"cons_{k}"] = (names[k], dia * DIAMOND_TO_SILVER)

# ============ ХРАНИЛИЩА ============
carts = {}
menu_msgs = {}
cart_msgs = {}
cart_pages = {}
cart_owners = {}

# ============ ФОРМАТИРОВАНИЕ ============
def fmt(num):
    if num >= 1_000_000:
        return f"{num / 1_000_000:.2f} млн"
    elif num >= 1_000:
        return f"{num / 1_000:.2f}к"
    return str(num)

LINE = "━━━━━━━━━━━━━━━━━━"

def block(title, silver):
    return f"{LINE}\n{title}\n{LINE}\n💰 {fmt(silver)} серебра\n{LINE}"

def block_best(title, silver):
    return f"{LINE}\n{title}\n{LINE}\n💰 {fmt(silver)} серебра\n{LINE}\n🟢 💸 ВЫГОДНО"

# ============ АВТОУДАЛЕНИЕ ============
def delete_main_menu_later(chat_id, user_id, delay=300):
    def worker():
        time.sleep(delay)
        try:
            mid = menu_msgs.get(user_id)
            if mid:
                bot.delete_message(chat_id, mid)
                del menu_msgs[user_id]
        except:
            pass
    threading.Thread(target=worker, daemon=True).start()

# ============ ГЛАВНОЕ МЕНЮ ============
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👑 VIP", callback_data="menu_vip"),
        types.InlineKeyboardButton("⭐ Звёзды", callback_data="menu_stars"),
        types.InlineKeyboardButton("💎 Алмазы", callback_data="menu_diamonds"),
        types.InlineKeyboardButton("⚜️ Руны", callback_data="menu_runes"),
        types.InlineKeyboardButton("💠 Premium", callback_data="menu_premium"),
        types.InlineKeyboardButton("📦 Расходники", callback_data="menu_consumables"),
    )
    return markup

def main_menu_text():
    return (
        f"{LINE}\n🎮 FARMKILL\n{LINE}\n\n"
        f"👋 Привет! Я помогу с выбором и валютой.\n"
        f"📌 Выбери ниже, что хочешь:\n\n"
        f"{LINE}\n⚠️ В группах дай боту админку.\n{LINE}\n\n"
        f"👨‍💻 Разработчик — @yra228kil1"
    )

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    old_cart_msg = cart_msgs.get(user_id)
    if old_cart_msg:
        try:
            bot.delete_message(chat_id, old_cart_msg)
        except:
            pass
    carts[user_id] = []
    cart_msgs[user_id] = None
    cart_pages[user_id] = 0
    name = message.from_user.username
    cart_owners[user_id] = ("@" + name) if name else (message.from_user.first_name or "Гость")
    old_menu = menu_msgs.get(user_id)
    if old_menu:
        try:
            bot.delete_message(chat_id, old_menu)
        except:
            pass
    msg = bot.send_message(chat_id, main_menu_text(), reply_markup=main_menu())
    menu_msgs[user_id] = msg.message_id
    delete_main_menu_later(chat_id, user_id)

# ============ ХЕЛПЕР ============
def item_kb(back_cb, key):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data=back_cb),
        types.InlineKeyboardButton("🛒 Хочу", callback_data=f"w|{key}"),
    )
    return markup

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
    try:
        bot.edit_message_text("👑 VIP\n\nВыбери вариант:", call.message.chat.id, call.message.message_id, reply_markup=vip_menu())
    except:
        bot.send_message(call.message.chat.id, "👑 VIP\n\nВыбери вариант:", reply_markup=vip_menu())

@bot.message_handler(commands=['vip'])
def vip_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        bot.send_message(message.chat.id, "👑 VIP\n\nВыбери вариант:", reply_markup=vip_menu())
        return
    level = args[1]
    if level in ("1", "2"):
        send_item(message.chat.id, f"vip_{level}", "menu_vip")
    else:
        bot.send_message(message.chat.id, "❌ Укажи /vip 1 или /vip 2")

@bot.callback_query_handler(func=lambda call: call.data in ("vip_1", "vip_2"))
def vip_callback(call):
    level = call.data.split("_")[1]
    key = f"vip_{level}"
    title, silver = ITEMS[key]
    try:
        bot.edit_message_text(block(title, silver), call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_vip", key))
    except:
        bot.send_message(call.message.chat.id, block(title, silver), reply_markup=item_kb("menu_vip", key))

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
    try:
        bot.edit_message_text("⭐ Звёзды\n\nВыбери количество:", call.message.chat.id, call.message.message_id, reply_markup=stars_menu())
    except:
        bot.send_message(call.message.chat.id, "⭐ Звёзды\n\nВыбери количество:", reply_markup=stars_menu())

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
    if amount not in STARS:
        bot.send_message(message.chat.id, "❌ Доступно: 100, 250, 500, 1000, 2500, 10000")
        return
    send_item(message.chat.id, f"stars_{amount}", "menu_stars")

@bot.callback_query_handler(func=lambda call: call.data.startswith("stars_"))
def stars_callback(call):
    amount = call.data.split("_")[1]
    key = f"stars_{amount}"
    title, silver = ITEMS[key]
    text = block_best(title, silver) if amount == "10000" else block(title, silver)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_stars", key))
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=item_kb("menu_stars", key))

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
    try:
        bot.edit_message_text("💎 Алмазы\n\nВыбери количество:", call.message.chat.id, call.message.message_id, reply_markup=diamonds_menu())
    except:
        bot.send_message(call.message.chat.id, "💎 Алмазы\n\nВыбери количество:", reply_markup=diamonds_menu())

@bot.message_handler(commands=['diamonds'])
def diamonds_cmd(message):
    bot.send_message(message.chat.id, "💎 Алмазы\n\nВыбери количество:", reply_markup=diamonds_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("dia_"))
def diamonds_callback(call):
    amount = call.data.split("_")[1]
    key = f"dia_{amount}"
    title, silver = ITEMS[key]
    text = block_best(title, silver) if amount == "5000" else block(title, silver)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_diamonds", key))
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=item_kb("menu_diamonds", key))

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
    try:
        bot.edit_message_text("⚜️ Руны\n\nВыбери руну:", call.message.chat.id, call.message.message_id, reply_markup=runes_menu())
    except:
        bot.send_message(call.message.chat.id, "⚜️ Руны\n\nВыбери руну:", reply_markup=runes_menu())

@bot.message_handler(commands=['rune'])
def rune_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        bot.send_message(message.chat.id, "⚜️ Руны\n\nВыбери руну:", reply_markup=runes_menu())
        return
    key = args[1].lower()
    if key in ("save", "сохр"):
        send_item(message.chat.id, "rune_save", "menu_runes")
    elif key in ("prot", "защ"):
        send_item(message.chat.id, "rune_prot", "menu_runes")
    else:
        bot.send_message(message.chat.id, "❌ /rune save или /rune prot")

@bot.callback_query_handler(func=lambda call: call.data.startswith("rune_"))
def rune_callback(call):
    key = call.data
    title, silver = ITEMS[key]
    try:
        bot.edit_message_text(block(title, silver), call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_runes", key))
    except:
        bot.send_message(call.message.chat.id, block(title, silver), reply_markup=item_kb("menu_runes", key))

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
    try:
        bot.edit_message_text("💠 Telegram Premium\n\nВыбери срок:", call.message.chat.id, call.message.message_id, reply_markup=premium_menu())
    except:
        bot.send_message(call.message.chat.id, "💠 Telegram Premium\n\nВыбери срок:", reply_markup=premium_menu())

@bot.message_handler(commands=['premium'])
def premium_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        bot.send_message(message.chat.id, "💠 Telegram Premium\n\nВыбери срок:", reply_markup=premium_menu())
        return
    try:
        months = int(args[1])
    except:
        bot.send_message(message.chat.id, "❌ Укажи срок: /premium 12")
        return
    if months not in PREMIUM:
        bot.send_message(message.chat.id, "❌ Доступно: 3, 6, 12")
        return
    send_item(message.chat.id, f"prem_{months}", "menu_premium")

@bot.callback_query_handler(func=lambda call: call.data.startswith("prem_"))
def premium_callback(call):
    months = call.data.split("_")[1]
    key = f"prem_{months}"
    title, silver = ITEMS[key]
    text = block_best(title, silver) if months == "12" else block(title, silver)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_premium", key))
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=item_kb("menu_premium", key))

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
    try:
        bot.edit_message_text("📦 Расходники\n\nВыбери предмет:", call.message.chat.id, call.message.message_id, reply_markup=consumables_menu())
    except:
        bot.send_message(call.message.chat.id, "📦 Расходники\n\nВыбери предмет:", reply_markup=consumables_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("cons_"))
def consumables_callback(call):
    key = call.data
    title, silver = ITEMS[key]
    try:
        bot.edit_message_text(block(title, silver), call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_consumables", key))
    except:
        bot.send_message(call.message.chat.id, block(title, silver), reply_markup=item_kb("menu_consumables", key))

@bot.message_handler(commands=['stone'])
def stone_cmd(message):
    send_item(message.chat.id, "cons_stone", "menu_consumables")

@bot.message_handler(commands=['tag'])
def tag_cmd(message):
    send_item(message.chat.id, "cons_tag", "menu_consumables")

@bot.message_handler(commands=['token'])
def token_cmd(message):
    send_item(message.chat.id, "cons_token", "menu_consumables")

# ============ УНИВЕРСАЛЬНАЯ ОТПРАВКА ============
def send_item(chat_id, key, back_cb):
    title, silver = ITEMS[key]
    text = block(title, silver)
    if key in ("stars_10000", "dia_5000", "prem_12"):
        text = block_best(title, silver)
    bot.send_message(chat_id, text, reply_markup=item_kb(back_cb, key))

# ============ КОРЗИНА ============
def cart_text(user_id):
    name = cart_owners.get(user_id, "Гость")
    items = carts.get(user_id, [])
    lines = [LINE, f"🛒 КОРЗИНА {name}", LINE, ""]
    if not items:
        lines.append("Корзина пуста")
        return "\n".join(lines)
    page = cart_pages.get(user_id, 0)
    start = page * 4
    end = start + 4
    for i, item in enumerate(items[start:end], start=start + 1):
        lines.append(f"{i}. {item['name']} — {fmt(item['price'])}")
    full_total = sum(it["price"] for it in items)
    lines.append("")
    lines.append(LINE)
    lines.append(f"💰 Итого: {fmt(full_total)} серебра")
    lines.append(LINE)
    return "\n".join(lines)

def cart_kb(user_id):
    items = carts.get(user_id, [])
    markup = types.InlineKeyboardMarkup(row_width=2)
    page = cart_pages.get(user_id, 0)
    start = page * 4
    end = start + 4
    for i, item in enumerate(items[start:end], start=start):
        markup.add(types.InlineKeyboardButton(f"❌ {item['name']}", callback_data=f"rm|{i}"))
    total_pages = max(1, (len(items) + 3) // 4)
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️", callback_data="cart_prev"))
    nav.append(types.InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="cart_noop"))
    if end < len(items):
        nav.append(types.InlineKeyboardButton("➡️", callback_data="cart_next"))
    if nav:
        markup.row(*nav)
    if items:
        markup.add(types.InlineKeyboardButton("🗑 Очистить всё", callback_data="cart_clear"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="cart_back"))
    return markup

def render_cart(user_id, chat_id, message_id=None):
    text = cart_text(user_id)
    kb = cart_kb(user_id)
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
            return
        except:
            pass
    msg = bot.send_message(chat_id, text, reply_markup=kb)
    cart_msgs[user_id] = msg.message_id

# ============ ХОЧУ ============
@bot.callback_query_handler(func=lambda call: call.data.startswith("w|"))
def want_callback(call):
    user_id = call.from_user.id
    key = call.data.split("|", 1)[1]
    if key not in ITEMS:
        bot.answer_callback_query(call.id, "❌ Товар не найден")
        return
    title, price = ITEMS[key]
    if user_id not in carts:
        carts[user_id] = []
    carts[user_id].append({"key": key, "name": title, "price": price})
    mid = cart_msgs.get(user_id)
    if mid:
        try:
            render_cart(user_id, call.message.chat.id, mid)
            bot.answer_callback_query(call.id, "✅ Добавлено в корзину")
            return
        except:
            pass
    render_cart(user_id, call.message.chat.id)
    bot.answer_callback_query(call.id, "✅ Добавлено в корзину")

# ============ УДАЛЕНИЕ ============
@bot.callback_query_handler(func=lambda call: call.data.startswith("rm|"))
def remove_item(call):
    user_id = call.from_user.id
    idx = int(call.data.split("|")[1])
    items = carts.get(user_id, [])
    if 0 <= idx < len(items):
        items.pop(idx)
    page = cart_pages.get(user_id, 0)
    total_pages = max(1, (len(items) + 3) // 4)
    if page >= total_pages:
        page = total_pages - 1
        cart_pages[user_id] = page
    if not items:
        mid = cart_msgs.get(user_id)
        if mid:
            try:
                bot.delete_message(call.message.chat.id, mid)
            except:
                pass
        cart_msgs[user_id] = None
        bot.answer_callback_query(call.id, "🗑 Корзина очищена")
        return
    render_cart(user_id, call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "❌ Удалено")

# ============ ОЧИСТИТЬ ВСЁ ============
@bot.callback_query_handler(func=lambda call: call.data == "cart_clear")
def cart_clear(call):
    user_id = call.from_user.id
    carts[user_id] = []
    mid = cart_msgs.get(user_id)
    if mid:
        try:
            bot.delete_message(call.message.chat.id, mid)
        except:
            pass
    cart_msgs[user_id] = None
    bot.answer_callback_query(call.id, "🗑 Корзина очищена")

# ============ НАВИГАЦИЯ ============
@bot.callback_query_handler(func=lambda call: call.data == "cart_prev")
def cart_prev(call):
    user_id = call.from_user.id
    cart_pages[user_id] = max(0, cart_pages.get(user_id, 0) - 1)
    render_cart(user_id, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "cart_next")
def cart_next(call):
    user_id = call.from_user.id
    items = carts.get(user_id, [])
    total_pages = max(1, (len(items) + 3) // 4)
    cart_pages[user_id] = min(total_pages - 1, cart_pages.get(user_id, 0) + 1)
    render_cart(user_id, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "cart_noop")
def cart_noop(call):
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "cart_back")
def cart_back(call):
    user_id = call.from_user.id
    mid = cart_msgs.get(user_id)
    if mid:
        try:
            bot.delete_message(call.message.chat.id, mid)
        except:
            pass
    cart_msgs[user_id] = None
    msg = bot.send_message(call.message.chat.id, main_menu_text(), reply_markup=main_menu())
    menu_msgs[user_id] = msg.message_id
    delete_main_menu_later(call.message.chat.id, user_id)

# ============ НАЗАД В ГЛАВНОЕ ============
@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    user_id = call.from_user.id
    try:
        bot.edit_message_text(main_menu_text(), call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    except:
        msg = bot.send_message(call.message.chat.id, main_menu_text(), reply_markup=main_menu())
        menu_msgs[user_id] = msg.message_id
        delete_main_menu_later(call.message.chat.id, user_id)

# ============ НЕИЗВЕСТНАЯ КОМАНДА ============
@bot.message_handler(func=lambda message: True)
def unknown(message):
    bot.send_message(
        message.chat.id,
        "❌ Команда не распознана.\nНапишите ещё раз и проверьте написание\nили дождитесь @yra228kil1"
    )

# ============ ЗАПУСК ============
if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот запущен...")
    bot.infinity_polling()
