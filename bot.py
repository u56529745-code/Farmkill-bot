import telebot
from telebot import types
import threading
import time
import os
from flask import Flask

# ============ НАСТРОЙКИ ============
TOKEN = "8814067918:AAHuKBx72jA_2Zx1cnqIO_H1Bdw3L9rrVww"
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
RUB_TO_SILVER = 57543.19
DIAMOND_TO_SILVER = 16700

# ============ ЦЕНЫ ============
STARS_PRICES = {
    100: 181.99, 150: 264.99, 250: 429.00, 350: 599.00, 500: 849.00,
    750: 1259.00, 1000: 1679.00, 1500: 2499.00, 2500: 4199.00,
    5000: 8299.00, 10000: 16599.00, 25000: 41499.00,
    50000: 82999.00, 100000: 165999.00, 150000: 249999.00,
}
VIP1 = {1: 2400, 3: 6000, 6: 10800, 12: 18900}
VIP2 = {1: 1500, 3: 3900, 6: 6900, 12: 11700}
PREMIUM = {3: 1049.00, 6: 1399.00, 12: 2539.00}
DIAMONDS = {100: 100, 300: 300, 500: 500, 1000: 1000, 2500: 2500, 5000: 5000}
RUNES = {"save": 240, "prot": 240}
CONSUMABLES = {"stone": 160, "tag": 100, "token": 200}

# ============ БАЗА ТОВАРОВ ============
ITEMS = {}

for m, dia in VIP1.items():
    ITEMS[f"vip1_{m}"] = {"name": f"👑 VIP 1 ({m} мес)", "dia": dia, "silver": dia * DIAMOND_TO_SILVER}
for m, dia in VIP2.items():
    ITEMS[f"vip2_{m}"] = {"name": f"👑 VIP 2 ({m} мес)", "dia": dia, "silver": dia * DIAMOND_TO_SILVER}
for amt, rub in STARS_PRICES.items():
    ITEMS[f"stars_{amt}"] = {"name": f"⭐ {amt} звёзд", "silver": int(rub * RUB_TO_SILVER)}
for amt in DIAMONDS:
    ITEMS[f"dia_{amt}"] = {"name": f"💎 {amt} алмазов", "silver": amt * DIAMOND_TO_SILVER}
for m, rub in PREMIUM.items():
    ITEMS[f"prem_{m}"] = {"name": f"💠 Premium ({m} мес)", "silver": int(rub * RUB_TO_SILVER)}
for k, dia in RUNES.items():
    name = "🧿 Руна сохранения" if k == "save" else "🧿 Руна защиты"
    ITEMS[f"rune_{k}"] = {"name": name, "dia": dia, "silver": dia * DIAMOND_TO_SILVER}
for k, dia in CONSUMABLES.items():
    names = {"stone": "🧪 Камень очищения", "tag": "🧪 Бирка", "token": "🧪 Жетон смены имени"}
    ITEMS[f"cons_{k}"] = {"name": names[k], "dia": dia, "silver": dia * DIAMOND_TO_SILVER}

# ============ ХРАНИЛИЩА ============
carts = {}
menu_msgs = {}
cart_msgs = {}
cart_pages = {}
cart_owners = {}
add_counters = {}
# owners[message_id] = user_id (кто создал меню/товар/корзину)
owners = {}

# ============ ФОРМАТИРОВАНИЕ ============
def fmt(num):
    if num is None:
        return "—"
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.3f} млрд"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.3f} млн"
    elif num >= 1_000:
        return f"{num / 1_000:.3f}к"
    return str(num)

LINE = "━━━━━━━━━━━━━━━━━━"

def block(item, added=0):
    lines = [LINE, item["name"], LINE]
    dia = item.get("dia")
    silver = item.get("silver")
    if dia and silver:
        lines.append(f"💎 {dia} алмазов")
        lines.append("   или")
        lines.append(f"💰 {fmt(silver)} серебра")
    elif dia:
        lines.append(f"💎 {dia} алмазов")
    elif silver:
        lines.append(f"💰 {fmt(silver)} серебра")
    lines.append(LINE)
    if added > 0:
        lines.append(f"✅ Добавлено в корзину: {added}")
    return "\n".join(lines)

def stars_discount(amount):
    base = STARS_PRICES[100] / 100
    cur = STARS_PRICES[amount] / amount
    if cur >= base:
        return None
    pct = (base - cur) / base * 100
    return f"📊 Дешевле на {pct:.3f}% чем 100 звёзд"

def block_stars(amount, added=0):
    item = ITEMS[f"stars_{amount}"]
    lines = [LINE, item["name"], LINE, f"💰 {fmt(item['silver'])} серебра", LINE]
    disc = stars_discount(amount)
    if disc:
        lines.append(disc)
    if added > 0:
        lines.append(f"✅ Добавлено в корзину: {added}")
    return "\n".join(lines)

# ============ ПРОВЕРКА ВЛАДЕЛЬЦА ============
def check_owner(call):
    """Проверяет, что нажал владелец меню. Возвращает True, если ок."""
    owner = owners.get(call.message.message_id)
    if owner is None:
        # Если владелец не записан — считаем, что это владелец
        owners[call.message.message_id] = call.from_user.id
        return True
    if owner != call.from_user.id:
        bot.answer_callback_query(call.id, "❌ Это не твоё меню")
        return False
    return True

# ============ АВТОУДАЛЕНИЕ ============
def delete_main_menu_later(chat_id, user_id, delay=300):
    def worker():
        time.sleep(delay)
        try:
            mid = menu_msgs.get(user_id)
            if mid:
                bot.delete_message(chat_id, mid)
                del menu_msgs[user_id]
                owners.pop(mid, None)
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
    # Удаляем старую корзину
    old_cart_msg = cart_msgs.get(user_id)
    if old_cart_msg:
        try:
            bot.delete_message(chat_id, old_cart_msg)
        except:
            pass
    carts[user_id] = []
    cart_msgs[user_id] = None
    cart_pages[user_id] = 0
    add_counters[user_id] = {}
    name = message.from_user.username
    cart_owners[user_id] = ("@" + name) if name else (message.from_user.first_name or "Гость")
    # Удаляем старое меню
    old_menu = menu_msgs.get(user_id)
    if old_menu:
        try:
            bot.delete_message(chat_id, old_menu)
        except:
            pass
        owners.pop(old_menu, None)
    # Отправляем меню (в ответ на сообщение игрока)
    msg = bot.send_message(
        chat_id,
        main_menu_text(),
        reply_markup=main_menu(),
        reply_to_message_id=message.message_id
    )
    menu_msgs[user_id] = msg.message_id
    owners[msg.message_id] = user_id
    delete_main_menu_later(chat_id, user_id)

# ============ ХЕЛПЕР ============
def item_kb(back_cb, key):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data=back_cb),
        types.InlineKeyboardButton("🛒 Хочу", callback_data=f"w|{key}"),
    )
    return markup

def item_kb_from_key(key):
    if key.startswith("vip1_") or key.startswith("vip2_"):
        return item_kb("menu_vip", key)
    elif key.startswith("stars_"):
        return item_kb("menu_stars", key)
    elif key.startswith("dia_"):
        return item_kb("menu_diamonds", key)
    elif key.startswith("rune_"):
        return item_kb("menu_runes", key)
    elif key.startswith("prem_"):
        return item_kb("menu_premium", key)
    elif key.startswith("cons_"):
        return item_kb("menu_consumables", key)
    return item_kb("back_main", key)

# ============ VIP ============
def vip_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("VIP 1", callback_data="vip_type_1"),
        types.InlineKeyboardButton("VIP 2", callback_data="vip_type_2"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

def vip_periods_menu(t):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for m in (1, 3, 6, 12):
        markup.add(types.InlineKeyboardButton(f"{m} мес", callback_data=f"vip{t}_{m}"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_vip"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_vip")
def menu_vip(call):
    if not check_owner(call):
        return
    try:
        bot.edit_message_text("👑 VIP\n\nВыбери тип:", call.message.chat.id, call.message.message_id, reply_markup=vip_menu())
        owners[call.message.message_id] = call.from_user.id
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data in ("vip_type_1", "vip_type_2"))
def vip_type_cb(call):
    if not check_owner(call):
        return
    t = call.data.split("_")[2]
    try:
        bot.edit_message_text(f"👑 VIP {t}\n\nВыбери срок:", call.message.chat.id, call.message.message_id,
                              reply_markup=vip_periods_menu(t))
        owners[call.message.message_id] = call.from_user.id
    except:
        pass

@bot.message_handler(commands=['vip'])
def vip_cmd(message):
    bot.send_message(message.chat.id, "👑 VIP\n\nВыбери тип:", reply_markup=vip_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("vip1_") or call.data.startswith("vip2_"))
def vip_item_cb(call):
    if not check_owner(call):
        return
    key = call.data
    item = ITEMS[key]
    user_id = call.from_user.id
    mid = call.message.message_id
    added = add_counters.get(user_id, {}).get(mid, 0)
    try:
        bot.edit_message_text(block(item, added), call.message.chat.id, mid,
                              reply_markup=item_kb("menu_vip", key))
        owners[mid] = user_id
    except:
        pass

# ============ STARS ============
def stars_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    for amt in STARS_PRICES.keys():
        markup.add(types.InlineKeyboardButton(f"{amt}", callback_data=f"stars_{amt}"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_stars")
def menu_stars(call):
    if not check_owner(call):
        return
    try:
        bot.edit_message_text("⭐ Звёзды\n\nВыбери количество:", call.message.chat.id, call.message.message_id, reply_markup=stars_menu())
        owners[call.message.message_id] = call.from_user.id
    except:
        pass

@bot.message_handler(commands=['stars'])
def stars_cmd(message):
    bot.send_message(message.chat.id, "⭐ Звёзды\n\nВыбери количество:", reply_markup=stars_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("stars_"))
def stars_callback(call):
    if not check_owner(call):
        return
    amount = int(call.data.split("_")[1])
    key = f"stars_{amount}"
    user_id = call.from_user.id
    mid = call.message.message_id
    added = add_counters.get(user_id, {}).get(mid, 0)
    try:
        bot.edit_message_text(block_stars(amount, added), call.message.chat.id, mid,
                              reply_markup=item_kb("menu_stars", key))
        owners[mid] = user_id
    except:
        pass

# ============ DIAMONDS ============
def diamonds_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    for amt in DIAMONDS.keys():
        markup.add(types.InlineKeyboardButton(f"{amt}", callback_data=f"dia_{amt}"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_diamonds")
def menu_diamonds(call):
    if not check_owner(call):
        return
    try:
        bot.edit_message_text("💎 Алмазы\n\nВыбери количество:", call.message.chat.id, call.message.message_id, reply_markup=diamonds_menu())
        owners[call.message.message_id] = call.from_user.id
    except:
        pass

@bot.message_handler(commands=['diamonds'])
def diamonds_cmd(message):
    bot.send_message(message.chat.id, "💎 Алмазы\n\nВыбери количество:", reply_markup=diamonds_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("dia_"))
def diamonds_callback(call):
    if not check_owner(call):
        return
    amount = call.data.split("_")[1]
    key = f"dia_{amount}"
    item = ITEMS[key]
    user_id = call.from_user.id
    mid = call.message.message_id
    added = add_counters.get(user_id, {}).get(mid, 0)
    try:
        bot.edit_message_text(block(item, added), call.message.chat.id, mid,
                              reply_markup=item_kb("menu_diamonds", key))
        owners[mid] = user_id
    except:
        pass

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
    if not check_owner(call):
        return
    try:
        bot.edit_message_text("⚜️ Руны\n\nВыбери руну:", call.message.chat.id, call.message.message_id, reply_markup=runes_menu())
        owners[call.message.message_id] = call.from_user.id
    except:
        pass

@bot.message_handler(commands=['rune'])
def rune_cmd(message):
    bot.send_message(message.chat.id, "⚜️ Руны\n\nВыбери руну:", reply_markup=runes_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("rune_"))
def rune_callback(call):
    if not check_owner(call):
        return
    key = call.data
    item = ITEMS[key]
    user_id = call.from_user.id
    mid = call.message.message_id
    added = add_counters.get(user_id, {}).get(mid, 0)
    try:
        bot.edit_message_text(block(item, added), call.message.chat.id, mid,
                              reply_markup=item_kb("menu_runes", key))
        owners[mid] = user_id
    except:
        pass

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
    if not check_owner(call):
        return
    try:
        bot.edit_message_text("💠 Telegram Premium\n\nВыбери срок:", call.message.chat.id, call.message.message_id, reply_markup=premium_menu())
        owners[call.message.message_id] = call.from_user.id
    except:
        pass

@bot.message_handler(commands=['premium'])
def premium_cmd(message):
    bot.send_message(message.chat.id, "💠 Telegram Premium\n\nВыбери срок:", reply_markup=premium_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("prem_"))
def premium_callback(call):
    if not check_owner(call):
        return
    months = call.data.split("_")[1]
    key = f"prem_{months}"
    item = ITEMS[key]
    user_id = call.from_user.id
    mid = call.message.message_id
    added = add_counters.get(user_id, {}).get(mid, 0)
    try:
        bot.edit_message_text(block(item, added), call.message.chat.id, mid,
                              reply_markup=item_kb("menu_premium", key))
        owners[mid] = user_id
    except:
        pass

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
    if not check_owner(call):
        return
    try:
        bot.edit_message_text("📦 Расходники\n\nВыбери предмет:", call.message.chat.id, call.message.message_id, reply_markup=consumables_menu())
        owners[call.message.message_id] = call.from_user.id
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("cons_"))
def consumables_callback(call):
    if not check_owner(call):
        return
    key = call.data
    item = ITEMS[key]
    user_id = call.from_user.id
    mid = call.message.message_id
    added = add_counters.get(user_id, {}).get(mid, 0)
    try:
        bot.edit_message_text(block(item, added), call.message.chat.id, mid,
                              reply_markup=item_kb("menu_consumables", key))
        owners[mid] = user_id
    except:
        pass

@bot.message_handler(commands=['stone'])
def stone_cmd(message):
    item = ITEMS["cons_stone"]
    bot.send_message(message.chat.id, block(item), reply_markup=item_kb("menu_consumables", "cons_stone"))

@bot.message_handler(commands=['tag'])
def tag_cmd(message):
    item = ITEMS["cons_tag"]
    bot.send_message(message.chat.id, block(item), reply_markup=item_kb("menu_consumables", "cons_tag"))

@bot.message_handler(commands=['token'])
def token_cmd(message):
    item = ITEMS["cons_token"]
    bot.send_message(message.chat.id, block(item), reply_markup=item_kb("menu_consumables", "cons_token"))

# ============ КОРЗИНА ============
def item_price_text(item):
    dia = item.get("dia")
    silver = item.get("silver")
    if dia and silver:
        return f"💎 {dia} или 💰 {fmt(silver)}"
    elif dia:
        return f"💎 {dia} алмазов"
    elif silver:
        return f"💰 {fmt(silver)}"
    return "—"

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
        lines.append(f"{i}. {item['name']} — {item_price_text(item)}")
    total_dia = sum(it.get("dia", 0) for it in items if it.get("dia"))
    total_silver = sum(it.get("silver", 0) for it in items if it.get("silver"))
    lines.append("")
    lines.append(LINE)
    if total_dia > 0 and total_silver > 0:
        lines.append(f"💰 Итого: 💎 {total_dia} или {fmt(total_silver)} серебра")
    elif total_dia > 0:
        lines.append(f"💎 Итого: {total_dia} алмазов")
    elif total_silver > 0:
        lines.append(f"💰 Итого: {fmt(total_silver)} серебра")
    else:
        lines.append("Итого: 0")
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
            owners[message_id] = user_id
            return
        except:
            pass
    msg = bot.send_message(chat_id, text, reply_markup=kb)
    cart_msgs[user_id] = msg.message_id
    owners[msg.message_id] = user_id

# ============ ХОЧУ ============
@bot.callback_query_handler(func=lambda call: call.data.startswith("w|"))
def want_callback(call):
    if not check_owner(call):
        return
    user_id = call.from_user.id
    key = call.data.split("|", 1)[1]
    if key not in ITEMS:
        bot.answer_callback_query(call.id, "❌ Товар не найден")
        return
    item = ITEMS[key]
    if user_id not in carts:
        carts[user_id] = []
    entry = {"key": key, "name": item["name"]}
    if item.get("dia"):
        entry["dia"] = item["dia"]
    if item.get("silver"):
        entry["silver"] = item["silver"]
    carts[user_id].append(entry)

    mid = call.message.message_id
    if user_id not in add_counters:
        add_counters[user_id] = {}
    add_counters[user_id][mid] = add_counters[user_id].get(mid, 0) + 1
    added = add_counters[user_id][mid]

    if key.startswith("stars_"):
        amount = int(key.split("_")[1])
        text = block_stars(amount, added)
    else:
        text = block(item, added)
    try:
        bot.edit_message_text(text, call.message.chat.id, mid,
                              reply_markup=item_kb_from_key(key))
        owners[mid] = user_id
    except:
        pass

    cart_mid = cart_msgs.get(user_id)
    if cart_mid:
        try:
            render_cart(user_id, call.message.chat.id, cart_mid)
        except:
            render_cart(user_id, call.message.chat.id)
    else:
        render_cart(user_id, call.message.chat.id)
    bot.answer_callback_query(call.id, "✅ Добавлено в корзину")

# ============ УДАЛЕНИЕ ============
@bot.callback_query_handler(func=lambda call: call.data.startswith("rm|"))
def remove_item(call):
    if not check_owner(call):
        return
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
    if not check_owner(call):
        return
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
    if not check_owner(call):
        return
    user_id = call.from_user.id
    cart_pages[user_id] = max(0, cart_pages.get(user_id, 0) - 1)
    render_cart(user_id, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "cart_next")
def cart_next(call):
    if not check_owner(call):
        return
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
    if not check_owner(call):
        return
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
    owners[msg.message_id] = user_id
    delete_main_menu_later(call.message.chat.id, user_id)

# ============ НАЗАД В ГЛАВНОЕ ============
@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    if not check_owner(call):
        return
    user_id = call.from_user.id
    try:
        bot.edit_message_text(main_menu_text(), call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        owners[call.message.message_id] = user_id
    except:
        pass

# ============ НЕИЗВЕСТНАЯ КОМАНДА ============
@bot.message_handler(func=lambda message: True)
def unknown(message):
    bot.send_message(
        message.chat.id,
        "❌ Команда не распознана.\nНапишите ещё раз и проверьте написание\nили дождитесь @yra228kil1"
    )

# ============ ЗАПУСК ============
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот запущен...")
    bot.infinity_polling()
