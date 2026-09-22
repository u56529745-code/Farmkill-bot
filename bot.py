import telebot
from telebot import types
import threading
import time

# ============ НАСТРОЙКИ ============
TOKEN = "8814067918:AAHVt-7m6mCafGS8sCAuOE8N2SqNma_cvZM"
bot = telebot.TeleBot(TOKEN)

# ============ КУРСЫ ============
RUB_TO_SILVER = 16700
DIAMOND_TO_SILVER = 16700

# ============ ЦЕНЫ ============
STARS = {
    100: 181.99, 250: 429.00, 500: 849.00,
    1000: 1679.00, 2500: 4199.00, 10000: 16599.00,
}
DIAMONDS = {100: 100, 300: 300, 500: 500, 1000: 1000, 2500: 2500, 5000: 5000}
VIP = {1: 2400, 2: 1500}
PREMIUM = {3: 1049.00, 6: 1399.00, 12: 2539.00}
RUNES = {"save": 240, "prot": 240}
CONSUMABLES = {"stone": 160, "tag": 100, "token": 200}

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
    return (
        f"{LINE}\n"
        f"{title}\n"
        f"{LINE}\n"
        f"💰 {fmt(silver)} серебра\n"
        f"{LINE}"
    )

def block_best(title, silver):
    return (
        f"{LINE}\n"
        f"{title}\n"
        f"{LINE}\n"
        f"💰 {fmt(silver)} серебра\n"
        f"{LINE}\n"
        f"🟢 💸 ВЫГОДНО"
    )

# ============ АВТОУДАЛЕНИЕ ГЛАВНОГО МЕНЮ ============
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
        types.InlineKeyboardButton("📱 Premium", callback_data="menu_premium"),
        types.InlineKeyboardButton("📦 Расходники", callback_data="menu_consumables"),
    )
    return markup

def main_menu_text():
    return (
        f"{LINE}\n"
        f"🎮 FARMKILL\n"
        f"{LINE}\n\n"
        f"👋 Привет! Я помогу с выбором и валютой.\n"
        f"📌 Выбери ниже, что хочешь:\n\n"
        f"{LINE}\n"
        f"⚠️ В группах дай боту админку.\n"
        f"{LINE}\n\n"
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
    if name:
        cart_owners[user_id] = "@" + name
    else:
        cart_owners[user_id] = message.from_user.first_name or "Гость"
    old_menu = menu_msgs.get(user_id)
    if old_menu:
        try:
            bot.delete_message(chat_id, old_menu)
        except:
            pass
    msg = bot.send_message(chat_id, main_menu_text(), reply_markup=main_menu())
    menu_msgs[user_id] = msg.message_id
    delete_main_menu_later(chat_id, user_id)

# ============ ХЕЛПЕР ДЛЯ ТОВАРОВ ============
def item_kb(back_cb, want_key, want_name, want_price):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data=back_cb),
        types.InlineKeyboardButton("🛒 Хочу", callback_data=f"want|{want_key}|{want_name}|{want_price}"),
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
        bot.edit_message_text("👑 VIP\n\nВыбери вариант:", call.message.chat.id,
                              call.message.message_id, reply_markup=vip_menu())
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
        send_vip(message.chat.id, int(level))
    else:
        bot.send_message(message.chat.id, "❌ Укажи /vip 1 или /vip 2")

def send_vip(chat_id, level):
    silver = VIP[level] * DIAMOND_TO_SILVER
    title = f"👑 VIP {level} (1 месяц)"
    bot.send_message(chat_id, block(title, silver),
                     reply_markup=item_kb("menu_vip", f"vip_{level}", title, silver))

@bot.callback_query_handler(func=lambda call: call.data in ("vip_1", "vip_2"))
def vip_callback(call):
    level = int(call.data.split("_")[1])
    silver = VIP[level] * DIAMOND_TO_SILVER
    title = f"👑 VIP {level} (1 месяц)"
    try:
        bot.edit_message_text(block(title, silver), call.message.chat.id,
                              call.message.message_id,
                              reply_markup=item_kb("menu_vip", f"vip_{level}", title, silver))
    except:
        send_vip(call.message.chat.id, level)

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
        bot.edit_message_text("⭐ Звёзды\n\nВыбери количество:", call.message.chat.id,
                              call.message.message_id, reply_markup=stars_menu())
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
    send_stars(message.chat.id, amount)

def send_stars(chat_id, amount):
    if amount not in STARS:
        bot.send_message(chat_id, "❌ Доступно: 100, 250, 500, 1000, 2500, 10000")
        return
    silver = STARS[amount] * RUB_TO_SILVER
    title = f"⭐ {amount} звёзд"
    text = block_best(title, silver) if amount == 10000 else block(title, silver)
    bot.send_message(chat_id, text,
                     reply_markup=item_kb("menu_stars", f"stars_{amount}", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("stars_"))
def stars_callback(call):
    amount = int(call.data.split("_")[1])
    silver = STARS[amount] * RUB_TO_SILVER
    title = f"⭐ {amount} звёзд"
    text = block_best(title, silver) if amount == 10000 else block(title, silver)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_stars", f"stars_{amount}", title, silver))
    except:
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
    try:
        bot.edit_message_text("💎 Алмазы\n\nВыбери количество:", call.message.chat.id,
                              call.message.message_id, reply_markup=diamonds_menu())
    except:
        bot.send_message(call.message.chat.id, "💎 Алмазы\n\nВыбери количество:", reply_markup=diamonds_menu())

@bot.message_handler(commands=['diamonds'])
def diamonds_cmd(message):
    bot.send_message(message.chat.id, "💎 Алмазы\n\nВыбери количество:", reply_markup=diamonds_menu())

def send_diamonds(chat_id, amount):
    silver = amount * DIAMOND_TO_SILVER
    title = f"💎 {amount} алмазов"
    text = block_best(title, silver) if amount == 5000 else block(title, silver)
    bot.send_message(chat_id, text,
                     reply_markup=item_kb("menu_diamonds", f"dia_{amount}", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("dia_"))
def diamonds_callback(call):
    amount = int(call.data.split("_")[1])
    silver = amount * DIAMOND_TO_SILVER
    title = f"💎 {amount} алмазов"
    text = block_best(title, silver) if amount == 5000 else block(title, silver)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_diamonds", f"dia_{amount}", title, silver))
    except:
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
    try:
        bot.edit_message_text("⚜️ Руны\n\nВыбери руну:", call.message.chat.id,
                              call.message.message_id, reply_markup=runes_menu())
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
        send_rune(message.chat.id, "save")
    elif key in ("prot", "защ"):
        send_rune(message.chat.id, "prot")
    else:
        bot.send_message(message.chat.id, "❌ /rune save или /rune prot")

def send_rune(chat_id, key):
    silver = RUNES[key] * DIAMOND_TO_SILVER
    title = "🧿 Руна сохранения" if key == "save" else "🧿 Руна защиты"
    bot.send_message(chat_id, block(title, silver),
                     reply_markup=item_kb("menu_runes", f"rune_{key}", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("rune_"))
def rune_callback(call):
    key = call.data.split("_")[1]
    silver = RUNES[key] * DIAMOND_TO_SILVER
    title = "🧿 Руна сохранения" if key == "save" else "🧿 Руна защиты"
    try:
        bot.edit_message_text(block(title, silver), call.message.chat.id,
                              call.message.message_id,
                              reply_markup=item_kb("menu_runes", f"rune_{key}", title, silver))
    except:
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
    try:
        bot.edit_message_text("📱 Telegram Premium\n\nВыбери срок:", call.message.chat.id,
                              call.message.message_id, reply_markup=premium_menu())
    except:
        bot.send_message(call.message.chat.id, "📱 Telegram Premium\n\nВыбери срок:", reply_markup=premium_menu())

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
    text = block_best(title, silver) if months == 12 else block(title, silver)
    bot.send_message(chat_id, text,
                     reply_markup=item_kb("menu_premium", f"prem_{months}", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("prem_"))
def premium_callback(call):
    months = int(call.data.split("_")[1])
    silver = PREMIUM[months] * RUB_TO_SILVER
    title = f"📱 Telegram Premium ({months} мес)"
    text = block_best(title, silver) if months == 12 else block(title, silver)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_premium", f"prem_{months}", title, silver))
    except:
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
    try:
        bot.edit_message_text("📦 Расходники\n\nВыбери предмет:", call.message.chat.id,
                              call.message.message_id, reply_markup=consumables_menu())
    except:
        bot.send_message(call.message.chat.id, "📦 Расходники\n\nВыбери предмет:", reply_markup=consumables_menu())

def send_consumable(chat_id, key):
    silver = CONSUMABLES[key] * DIAMOND_TO_SILVER
    titles = {"stone": "🧪 Камень очищения", "tag": "🧪 Бирка", "token": "🧪 Жетон смены имени"}
    title = titles[key]
    bot.send_message(chat_id, block(title, silver),
                     reply_markup=item_kb("menu_consumables", f"cons_{key}", title, silver))

@bot.callback_query_handler(func=lambda call: call.data.startswith("cons_"))
def consumables_callback(call):
    key = call.data.split("_")[1]
    silver = CONSUMABLES[key] * DIAMOND_TO_SILVER
    titles = {"stone": "🧪 Камень очищения", "tag": "🧪 Бирка", "token": "🧪 Жетон смены имени"}
    title = titles[key]
    try:
        bot.edit_message_text(block(title, silver), call.message.chat.id,
                              call.message.message_id,
                              reply_markup=item_kb("menu_consumables", f"cons_{key}", title, silver))
    except:
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
@bot.callback_query_handler(func=lambda call: call.data.startswith("want|"))
def want_callback(call):
    user_id = call.from_user.id
    _, key, name, price = call.data.split("|")
    price = int(price)
    if user_id not in carts:
        carts[user_id] = []
    carts[user_id].append({"key": key, "name": name, "price": price})
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

# ============ УДАЛЕНИЕ ТОВАРА (❌) ============
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

# ============ НАВИГАЦИЯ СТРАНИЦ ============
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

# ============ НАЗАД ИЗ КОРЗИНЫ ============
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

# ============ НАЗАД В ГЛАВНОЕ МЕНЮ ============
@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    user_id = call.from_user.id
    try:
        bot.edit_message_text(main_menu_text(), call.message.chat.id,
                              call.message.message_id, reply_markup=main_menu())
    except:
        msg = bot.send_message(call.message.chat.id, main_menu_text(), reply_markup=main_menu())
        menu_msgs[user_id] = msg.message_id
        delete_main_menu_later(call.message.chat.id, user_id)

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
