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
RUB_TO_SILVER = 57543.19
DIAMOND_TO_SILVER = 16700

# ============ ЗВЁЗДЫ ============
STARS_PRICES = {
    100: 181.99, 150: 264.99, 250: 429.00, 350: 599.00, 500: 849.00,
    750: 1259.00, 1000: 1679.00, 1500: 2499.00, 2500: 4199.00,
    5000: 8299.00, 10000: 16599.00, 25000: 41499.00,
    50000: 82999.00, 100000: 165999.00, 150000: 249999.00,
}

# ============ VIP (за алмазы, все сроки) ============
VIP1 = {1: 2400, 3: 6000, 6: 10800, 12: 18900}
VIP2 = {1: 1500, 3: 3900, 6: 6900, 12: 11700}

# ============ PREMIUM (за рубли) ============
PREMIUM = {3: 1049.00, 6: 1399.00, 12: 2539.00}

# ============ АЛМАЗЫ ============
DIAMONDS = {100: 100, 300: 300, 500: 500, 1000: 1000, 2500: 2500, 5000: 5000}

# ============ РУНЫ, РАСХОДНИКИ ============
RUNES = {"save": 240, "prot": 240}
CONSUMABLES = {"stone": 160, "tag": 100, "token": 200}

# ============ БАЗА ТОВАРОВ ============
ITEMS = {}

# VIP 1
for m, dia in VIP1.items():
    ITEMS[f"vip1_{m}"] = {
        "name": f"👑 VIP 1 ({m} мес)",
        "dia": dia,
        "silver": dia * DIAMOND_TO_SILVER,
    }
# VIP 2
for m, dia in VIP2.items():
    ITEMS[f"vip2_{m}"] = {
        "name": f"👑 VIP 2 ({m} мес)",
        "dia": dia,
        "silver": dia * DIAMOND_TO_SILVER,
    }
# Звёзды — только серебро (рубли)
for amt, rub in STARS_PRICES.items():
    ITEMS[f"stars_{amt}"] = {
        "name": f"⭐ {amt} звёзд",
        "silver": int(rub * RUB_TO_SILVER),
    }
# Алмазы — только серебро (по курсу алмаза)
for amt in DIAMONDS:
    ITEMS[f"dia_{amt}"] = {
        "name": f"💎 {amt} алмазов",
        "silver": amt * DIAMOND_TO_SILVER,
    }
# Premium — только серебро (рубли)
for m, rub in PREMIUM.items():
    ITEMS[f"prem_{m}"] = {
        "name": f"💠 Premium ({m} мес)",
        "silver": int(rub * RUB_TO_SILVER),
    }
# Руны — двойная
for k, dia in RUNES.items():
    name = "🧿 Руна сохранения" if k == "save" else "🧿 Руна защиты"
    ITEMS[f"rune_{k}"] = {
        "name": name,
        "dia": dia,
        "silver": dia * DIAMOND_TO_SILVER,
    }
# Расходники — двойная
for k, dia in CONSUMABLES.items():
    names = {"stone": "🧪 Камень очищения", "tag": "🧪 Бирка", "token": "🧪 Жетон смены имени"}
    ITEMS[f"cons_{k}"] = {
        "name": names[k],
        "dia": dia,
        "silver": dia * DIAMOND_TO_SILVER,
    }

# ============ ХРАНИЛИЩА ============
carts = {}
menu_msgs = {}
cart_msgs = {}
cart_pages = {}
cart_owners = {}

# ============ ФОРМАТИРОВАНИЕ ============
def fmt(num):
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.3f} млрд"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.3f} млн"
    elif num >= 1_000:
        return f"{num / 1_000:.3f}к"
    return str(num)

LINE = "━━━━━━━━━━━━━━━━━━"

def block(item):
    lines = [LINE, item["name"], LINE]
    if "dia" in item:
        lines.append(f"💎 {item['dia']} алмазов")
        lines.append("   или")
        lines.append(f"💰 {fmt(item['silver'])} серебра")
    else:
        lines.append(f"💰 {fmt(item['silver'])} серебра")
    lines.append(LINE)
    return "\n".join(lines)

def stars_discount(amount):
    base = STARS_PRICES[100] / 100
    cur = STARS_PRICES[amount] / amount
    if cur >= base:
        return None
    pct = (base - cur) / base * 100
    return f"📊 Дешевле на {pct:.3f}% чем 100 звёзд"

def block_stars(amount):
    item = ITEMS[f"stars_{amount}"]
    lines = [LINE, item["name"], LINE, f"💰 {fmt(item['silver'])} серебра", LINE]
    disc = stars_discount(amount)
    if disc:
        lines.append(disc)
    return "\n".join(lines)

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
        types.InlineKeyboardButton("VIP 1", callback_data="vip_type_1"),
        types.InlineKeyboardButton("VIP 2", callback_data="vip_type_2"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

def vip_periods_menu(vip_type):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for m in (1, 3, 6, 12):
        markup.add(types.InlineKeyboardButton(f"{m} мес", callback_data=f"vip{vip_type}_{m}"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_vip"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "menu_vip")
def menu_vip(call):
    try:
        bot.edit_message_text("👑 VIP\n\nВыбери тип:", call.message.chat.id, call.message.message_id, reply_markup=vip_menu())
    except:
        bot.send_message(call.message.chat.id, "👑 VIP\n\nВыбери тип:", reply_markup=vip_menu())

@bot.callback_query_handler(func=lambda call: call.data in ("vip_type_1", "vip_type_2"))
def vip_type_cb(call):
    t = call.data.split("_")[2]
    try:
        bot.edit_message_text(f"👑 VIP {t}\n\nВыбери срок:", call.message.chat.id, call.message.message_id,
                              reply_markup=vip_periods_menu(t))
    except:
        bot.send_message(call.message.chat.id, f"👑 VIP {t}\n\nВыбери срок:", reply_markup=vip_periods_menu(t))

@bot.message_handler(commands=['vip'])
def vip_cmd(message):
    args = message.text.split()
    if len(args) == 1:
        bot.send_message(message.chat.id, "👑 VIP\n\nВыбери тип:", reply_markup=vip_menu())
        return
    bot.send_message(message.chat.id, "❌ Используй меню: /start")

@bot.callback_query_handler(func=lambda call: call.data.startswith("vip1_") or call.data.startswith("vip2_"))
def vip_item_cb(call):
    key = call.data
    item = ITEMS[key]
    try:
        bot.edit_message_text(block(item), call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_vip", key))
    except:
        bot.send_message(call.message.chat.id, block(item), reply_markup=item_kb("menu_vip", key))

# ============ STARS ============
def stars_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    for amt in STARS_PRICES.keys():
        markup.add(types.InlineKeyboardButton(f"{amt}", callback_data=f"stars_{amt}"))
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
    bot.send_message(message.chat.id, "⭐ Звёзды\n\nВыбери количество:", reply_markup=stars_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("stars_"))
def stars_callback(call):
    amount = int(call.data.split("_")[1])
    key = f"stars_{amount}"
    try:
        bot.edit_message_text(block_stars(amount), call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_stars", key))
    except:
        bot.send_message(call.message.chat.id, block_stars(amount), reply_markup=item_kb("menu_stars", key))

# ============ DIAMONDS ============
def diamonds_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    for amt in DIAMONDS.keys():
        markup.add(types.InlineKeyboardButton(f"{amt}", callback_data=f"dia_{amt}"))
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
    item = ITEMS[key]
    try:
        bot.edit_message_text(block(item), call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_diamonds", key))
    except:
        bot.send_message(call.message.chat.id, block(item), reply_markup=item_kb("menu_diamonds", key))

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
    bot.send_message(message.chat.id, "⚜️ Руны\n\nВыбери руну:", reply_markup=runes_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("rune_"))
def rune_callback(call):
    key = call.data
    item = ITEMS[key]
    try:
        bot.edit_message_text(block(item), call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_runes", key))
    except:
        bot.send_message(call.message.chat.id, block(item), reply_markup=item_kb("menu_runes", key))

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
    bot.send_message(message.chat.id, "💠 Telegram Premium\n\nВыбери срок:", reply_markup=premium_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("prem_"))
def premium_callback(call):
    months = call.data.split("_")[1]
    key = f"prem_{months}"
    item = ITEMS[key]
    try:
        bot.edit_message_text(block(item), call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_premium", key))
    except:
        bot.send_message(call.message.chat.id, block(item), reply_markup=item_kb("menu_premium", key))

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
    item = ITEMS[key]
    try:
        bot.edit_message_text(block(item), call.message.chat.id, call.message.message_id,
                              reply_markup=item_kb("menu_consumables", key))
    except:
        bot.send_message(call.message.chat.id, block(item), reply_markup=item_kb("menu_consumables", key))

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
    item = ITEMS[key]
    bot.send_message(chat_id, block(item), reply_markup=item_kb(back_cb, key))

# ============ КОРЗИНА ============
def item_price_text(item):
    has_dia = "dia" in item
    has_silver = "silver" in item
    if has_dia and has_silver:
        return f"💎 {item['dia']} или 💰 {fmt(item['silver'])}"
    elif has_dia:
        return f"💎 {item['dia']} алмазов"
    else:
        return f"💰 {fmt(item['silver'])}"

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
    total_dia = sum(it["dia"] for it in items if "dia" in it)
    total_silver = sum(it["silver"] for it in items if "silver" in it)
    lines.append("")
    lines.append(LINE)
    if total_dia > 0 and total_silver > 0:
        lines.append(f"💰 Итого: 💎 {total_dia} или {fmt(total_silver)} серебра")
    elif total_dia > 0:
        lines.append(f"💎 Итого: {total_dia} алмазов")
    else:
        lines.append(f"💰 Итого: {fmt(total_silver)} серебра")
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
    item = ITEMS[key]
    if user_id not in carts:
        carts[user_id] = []
    carts[user_id].append({
        "key": key,
        "name": item["name"],
        "dia": item.get("dia"),
        "silver": item.get("silver"),
    })
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
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот запущен...")
    bot.infinity_polling()
