import telebot, threading, time, os
from telebot import types
from flask import Flask

TOKEN = "8814067918:AAHuKBx72jA_2Zx1cnqIO_H1Bdw3L9rrVww"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index(): return "ok"

RUB, DIA = 57543.19, 16700

STARS = {100:181.99,150:264.99,250:429.00,350:599.00,500:849.00,750:1259.00,1000:1679.00,1500:2499.00,2500:4199.00,5000:8299.00,10000:16599.00,25000:41499.00,50000:82999.00,100000:165999.00,150000:249999.00}
VIP1 = {1:2400,3:6000,6:10800,12:18900}
VIP2 = {1:1500,3:3900,6:6900,12:11700}
PREM = {3:1049.00,6:1399.00,12:2539.00}
DIAS = {100:100,300:300,500:500,1000:1000,2500:2500,5000:5000}
RUNES = {"save":240,"prot":240}
CONS = {"stone":160,"tag":100,"token":200}

ITEMS = {}
for m,d in VIP1.items(): ITEMS[f"vip1_{m}"] = {"name":f"👑 VIP 1 ({m} мес)","dia":d,"silver":d*DIA}
for m,d in VIP2.items(): ITEMS[f"vip2_{m}"] = {"name":f"👑 VIP 2 ({m} мес)","dia":d,"silver":d*DIA}
for a,r in STARS.items(): ITEMS[f"stars_{a}"] = {"name":f"⭐ {a} звёзд","silver":int(r*RUB)}
for a in DIAS: ITEMS[f"dia_{a}"] = {"name":f"💎 {a} алмазов","silver":a*DIA}
for m,r in PREM.items(): ITEMS[f"prem_{m}"] = {"name":f"💠 Premium ({m} мес)","silver":int(r*RUB)}
for k,d in RUNES.items():
    n = "🧿 Руна сохранения" if k=="save" else "🧿 Руна защиты"
    ITEMS[f"rune_{k}"] = {"name":n,"dia":d,"silver":d*DIA}
for k,d in CONS.items():
    n = {"stone":"🧪 Камень очищения","tag":"🧪 Бирка","token":"🧪 Жетон смены имени"}[k]
    ITEMS[f"cons_{k}"] = {"name":n,"dia":d,"silver":d*DIA}

carts,menu_msgs,cart_msgs,cart_pages,cart_owners,add_cnt,owners = {},{},{},{},{},{},{}
wrong_clicks = [0]
LINE = "━━━━━━━━━━━━━━━━━━"

def fmt(n):
    if n is None: return "—"
    if n >= 1e9: return f"{n/1e9:.3f} млрд"
    if n >= 1e6: return f"{n/1e6:.3f} млн"
    if n >= 1e3: return f"{n/1e3:.3f}к"
    return str(n)

def block(it, added=0):
    L = [LINE, it["name"], LINE]
    d, s = it.get("dia"), it.get("silver")
    if d and s: L += [f"💎 {d} алмазов","   или",f"💰 {fmt(s)} серебра"]
    elif d: L.append(f"💎 {d} алмазов")
    elif s: L.append(f"💰 {fmt(s)} серебра")
    L.append(LINE)
    if added > 0: L.append(f"✅ Добавлено в корзину: {added}")
    return "\n".join(L)

def star_disc(a):
    b, c = STARS[100]/100, STARS[a]/a
    if c >= b: return None
    return f"📊 Дешевле на {(b-c)/b*100:.3f}% чем 100 звёзд"

def block_stars(a, added=0):
    it = ITEMS[f"stars_{a}"]
    L = [LINE, it["name"], LINE, f"💰 {fmt(it['silver'])} серебра", LINE]
    d = star_disc(a)
    if d: L.append(d)
    if added > 0: L.append(f"✅ Добавлено в корзину: {added}")
    return "\n".join(L)

def check_owner(call):
    o = owners.get(call.message.message_id)
    if o is None:
        owners[call.message.message_id] = call.from_user.id
        return True
    if o != call.from_user.id:
        wrong_clicks[0] += 1
        txt = "Иди нахуй" if (wrong_clicks[0]-1)//5 % 2 == 0 else "Шут придёт, по попе атата"
        bot.answer_callback_query(call.id, txt)
        return False
    return True

def del_menu(chat_id, uid, delay=300):
    def w():
        time.sleep(delay)
        try:
            mid = menu_msgs.get(uid)
            if mid:
                bot.delete_message(chat_id, mid)
                menu_msgs.pop(uid, None)
                owners.pop(mid, None)
        except: pass
    threading.Thread(target=w, daemon=True).start()

def main_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("👑 VIP", callback_data="menu_vip"),
          types.InlineKeyboardButton("⭐ Звёзды", callback_data="menu_stars"),
          types.InlineKeyboardButton("💎 Алмазы", callback_data="menu_diamonds"),
          types.InlineKeyboardButton("⚜️ Руны", callback_data="menu_runes"),
          types.InlineKeyboardButton("💠 Premium", callback_data="menu_premium"),
          types.InlineKeyboardButton("📦 Расходники", callback_data="menu_consumables"))
    return m

def menu_text():
    return f"{LINE}\n🎮 FARMKILL\n{LINE}\n\n👋 Привет! Я помогу с выбором и валютой.\n📌 Выбери ниже, что хочешь:\n\n{LINE}\n⚠️ В группах дай боту админку.\n{LINE}\n\n👨‍💻 Разработчик — @yra228kil1"

@bot.message_handler(commands=['start','help'])
def start(message):
    uid, cid = message.from_user.id, message.chat.id
    old = cart_msgs.get(uid)
    if old:
        try: bot.delete_message(cid, old)
        except: pass
    carts[uid], cart_msgs[uid], cart_pages[uid], add_cnt[uid] = [], None, 0, {}
    n = message.from_user.username
    cart_owners[uid] = ("@"+n) if n else (message.from_user.first_name or "Гость")
    om = menu_msgs.get(uid)
    if om:
        try: bot.delete_message(cid, om)
        except: pass
        owners.pop(om, None)
    msg = bot.send_message(cid, menu_text(), reply_markup=main_menu(), reply_to_message_id=message.message_id)
    menu_msgs[uid] = msg.message_id
    owners[msg.message_id] = uid
    del_menu(cid, uid)

def kb(back, key):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data=back),
          types.InlineKeyboardButton("🛒 Хочу", callback_data=f"w|{key}"))
    return m

def kb_from_key(key):
    if key.startswith(("vip1_","vip2_")): return kb("menu_vip", key)
    if key.startswith("stars_"): return kb("menu_stars", key)
    if key.startswith("dia_"): return kb("menu_diamonds", key)
    if key.startswith("rune_"): return kb("menu_runes", key)
    if key.startswith("prem_"): return kb("menu_premium", key)
    if key.startswith("cons_"): return kb("menu_consumables", key)
    return kb("back_main", key)

def vip_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("VIP 1", callback_data="vip_type_1"),
          types.InlineKeyboardButton("VIP 2", callback_data="vip_type_2"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return m

def vip_per(t):
    m = types.InlineKeyboardMarkup(row_width=2)
    for p in (1,3,6,12): m.add(types.InlineKeyboardButton(f"{p} мес", callback_data=f"vip{t}_{p}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu_vip"))
    return m

@bot.callback_query_handler(func=lambda c: c.data == "menu_vip")
def cb_vip(c):
    if not check_owner(c): return
    try:
        bot.edit_message_text("👑 VIP\n\nВыбери тип:", c.message.chat.id, c.message.message_id, reply_markup=vip_menu())
        owners[c.message.message_id] = c.from_user.id
    except: pass

@bot.callback_query_handler(func=lambda c: c.data in ("vip_type_1","vip_type_2"))
def cb_vip_type(c):
    if not check_owner(c): return
    t = c.data.split("_")[2]
    try:
        bot.edit_message_text(f"👑 VIP {t}\n\nВыбери срок:", c.message.chat.id, c.message.message_id, reply_markup=vip_per(t))
        owners[c.message.message_id] = c.from_user.id
    except: pass

@bot.message_handler(commands=['vip'])
def cmd_vip(m): bot.send_message(m.chat.id, "👑 VIP\n\nВыбери тип:", reply_markup=vip_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith(("vip1_","vip2_")))
def cb_vip_item(c):
    if not check_owner(c): return
    it = ITEMS[c.data]
    uid, mid = c.from_user.id, c.message.message_id
    add = add_cnt.get(uid,{}).get(mid,0)
    try:
        bot.edit_message_text(block(it, add), c.message.chat.id, mid, reply_markup=kb("menu_vip", c.data))
        owners[mid] = uid
    except: pass

def stars_menu():
    m = types.InlineKeyboardMarkup(row_width=3)
    for a in STARS: m.add(types.InlineKeyboardButton(f"{a}", callback_data=f"stars_{a}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return m

@bot.callback_query_handler(func=lambda c: c.data == "menu_stars")
def cb_stars(c):
    if not check_owner(c): return
    try:
        bot.edit_message_text("⭐ Звёзды\n\nВыбери количество:", c.message.chat.id, c.message.message_id, reply_markup=stars_menu())
        owners[c.message.message_id] = c.from_user.id
    except: pass

@bot.message_handler(commands=['stars'])
def cmd_stars(m): bot.send_message(m.chat.id, "⭐ Звёзды\n\nВыбери количество:", reply_markup=stars_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("stars_"))
def cb_star_item(c):
    if not check_owner(c): return
    a = int(c.data.split("_")[1])
    uid, mid = c.from_user.id, c.message.message_id
    add = add_cnt.get(uid,{}).get(mid,0)
    try:
        bot.edit_message_text(block_stars(a, add), c.message.chat.id, mid, reply_markup=kb("menu_stars", c.data))
        owners[mid] = uid
    except: pass

def dias_menu():
    m = types.InlineKeyboardMarkup(row_width=3)
    for a in DIAS: m.add(types.InlineKeyboardButton(f"{a}", callback_data=f"dia_{a}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return m

@bot.callback_query_handler(func=lambda c: c.data == "menu_diamonds")
def cb_dias(c):
    if not check_owner(c): return
    try:
        bot.edit_message_text("💎 Алмазы\n\nВыбери количество:", c.message.chat.id, c.message.message_id, reply_markup=dias_menu())
        owners[c.message.message_id] = c.from_user.id
    except: pass

@bot.message_handler(commands=['diamonds'])
def cmd_dias(m): bot.send_message(m.chat.id, "💎 Алмазы\n\nВыбери количество:", reply_markup=dias_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("dia_"))
def cb_dia_item(c):
    if not check_owner(c): return
    it = ITEMS[c.data]
    uid, mid = c.from_user.id, c.message.message_id
    add = add_cnt.get(uid,{}).get(mid,0)
    try:
        bot.edit_message_text(block(it, add), c.message.chat.id, mid, reply_markup=kb("menu_diamonds", c.data))
        owners[mid] = uid
    except: pass

def runes_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("Руна сохранения", callback_data="rune_save"),
          types.InlineKeyboardButton("Руна защиты", callback_data="rune_prot"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return m

@bot.callback_query_handler(func=lambda c: c.data == "menu_runes")
def cb_runes(c):
    if not check_owner(c): return
    try:
        bot.edit_message_text("⚜️ Руны\n\nВыбери руну:", c.message.chat.id, c.message.message_id, reply_markup=runes_menu())
        owners[c.message.message_id] = c.from_user.id
    except: pass

@bot.message_handler(commands=['rune'])
def cmd_rune(m): bot.send_message(m.chat.id, "⚜️ Руны\n\nВыбери руну:", reply_markup=runes_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("rune_"))
def cb_rune_item(c):
    if not check_owner(c): return
    it = ITEMS[c.data]
    uid, mid = c.from_user.id, c.message.message_id
    add = add_cnt.get(uid,{}).get(mid,0)
    try:
        bot.edit_message_text(block(it, add), c.message.chat.id, mid, reply_markup=kb("menu_runes", c.data))
        owners[mid] = uid
    except: pass

def prem_menu():
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(types.InlineKeyboardButton("3 мес", callback_data="prem_3"),
          types.InlineKeyboardButton("6 мес", callback_data="prem_6"),
          types.InlineKeyboardButton("12 мес", callback_data="prem_12"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return m

@bot.callback_query_handler(func=lambda c: c.data == "menu_premium")
def cb_prem(c):
    if not check_owner(c): return
    try:
        bot.edit_message_text("💠 Telegram Premium\n\nВыбери срок:", c.message.chat.id, c.message.message_id, reply_markup=prem_menu())
        owners[c.message.message_id] = c.from_user.id
    except: pass

@bot.message_handler(commands=['premium'])
def cmd_prem(m): bot.send_message(m.chat.id, "💠 Telegram Premium\n\nВыбери срок:", reply_markup=prem_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("prem_"))
def cb_prem_item(c):
    if not check_owner(c): return
    it = ITEMS[c.data]
    uid, mid = c.from_user.id, c.message.message_id
    add = add_cnt.get(uid,{}).get(mid,0)
    try:
        bot.edit_message_text(block(it, add), c.message.chat.id, mid, reply_markup=kb("menu_premium", c.data))
        owners[mid] = uid
    except: pass

def cons_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🧪 Бирка", callback_data="cons_tag"),
          types.InlineKeyboardButton("🧪 Камень очищения", callback_data="cons_stone"),
          types.InlineKeyboardButton("🧪 Жетон имени", callback_data="cons_token"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return m

@bot.callback_query_handler(func=lambda c: c.data == "menu_consumables")
def cb_cons(c):
    if not check_owner(c): return
    try:
        bot.edit_message_text("📦 Расходники\n\nВыбери предмет:", c.message.chat.id, c.message.message_id, reply_markup=cons_menu())
        owners[c.message.message_id] = c.from_user.id
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("cons_"))
def cb_cons_item(c):
    if not check_owner(c): return
    it = ITEMS[c.data]
    uid, mid = c.from_user.id, c.message.message_id
    add = add_cnt.get(uid,{}).get(mid,0)
    try:
        bot.edit_message_text(block(it, add), c.message.chat.id, mid, reply_markup=kb("menu_consumables", c.data))
        owners[mid] = uid
    except: pass

@bot.message_handler(commands=['stone'])
def cmd_stone(m): bot.send_message(m.chat.id, block(ITEMS["cons_stone"]), reply_markup=kb("menu_consumables","cons_stone"))

@bot.message_handler(commands=['tag'])
def cmd_tag(m): bot.send_message(m.chat.id, block(ITEMS["cons_tag"]), reply_markup=kb("menu_consumables","cons_tag"))

@bot.message_handler(commands=['token'])
def cmd_token(m): bot.send_message(m.chat.id, block(ITEMS["cons_token"]), reply_markup=kb("menu_consumables","cons_token"))

def price_txt(it):
    d, s = it.get("dia"), it.get("silver")
    if d and s: return f"💎 {d} или 💰 {fmt(s)}"
    if d: return f"💎 {d} алмазов"
    if s: return f"💰 {fmt(s)}"
    return "—"

def cart_text(uid):
    n = cart_owners.get(uid, "Гость")
    items = carts.get(uid, [])
    L = [LINE, f"🛒 КОРЗИНА {n}", LINE, ""]
    if not items:
        L.append("Корзина пуста")
        return "\n".join(L)
    p = cart_pages.get(uid, 0)
    for i, it in enumerate(items[p*4:p*4+4], start=p*4+1):
        L.append(f"{i}. {it['name']} — {price_txt(it)}")
    td = sum(x.get("dia",0) for x in items if x.get("dia"))
    ts = sum(x.get("silver",0) for x in items if x.get("silver"))
    L += ["", LINE]
    if td>0 and ts>0: L.append(f"💰 Итого: 💎 {td} или {fmt(ts)} серебра")
    elif td>0: L.append(f"💎 Итого: {td} алмазов")
    elif ts>0: L.append(f"💰 Итого: {fmt(ts)} серебра")
    else: L.append("Итого: 0")
    L.append(LINE)
    return "\n".join(L)

def cart_kb(uid):
    items = carts.get(uid, [])
    m = types.InlineKeyboardMarkup(row_width=2)
    p = cart_pages.get(uid, 0)
    for i, it in enumerate(items[p*4:p*4+4], start=p*4):
        m.add(types.InlineKeyboardButton(f"❌ {it['name']}", callback_data=f"rm|{i}"))
    tp = max(1, (len(items)+3)//4)
    nav = []
    if p > 0: nav.append(types.InlineKeyboardButton("⬅️", callback_data="cart_prev"))
    nav.append(types.InlineKeyboardButton(f"{p+1}/{tp}", callback_data="cart_noop"))
    if p*4+4 < len(items): nav.append(types.InlineKeyboardButton("➡️", callback_data="cart_next"))
    if nav: m.row(*nav)
    if items: m.add(types.InlineKeyboardButton("🗑 Очистить всё", callback_data="cart_clear"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="cart_back"))
    return m

def render_cart(uid, cid, mid=None):
    t = cart_text(uid); k = cart_kb(uid)
    if mid:
        try:
            bot.edit_message_text(t, cid, mid, reply_markup=k)
            owners[mid] = uid
            return
        except: pass
    msg = bot.send_message(cid, t, reply_markup=k)
    cart_msgs[uid] = msg.message_id
    owners[msg.message_id] = uid

@bot.callback_query_handler(func=lambda c: c.data.startswith("w|"))
def cb_want(c):
    if not check_owner(c): return
    uid = c.from_user.id
    key = c.data.split("|",1)[1]
    if key not in ITEMS:
        bot.answer_callback_query(c.id, "❌ Товар не найден"); return
    it = ITEMS[key]
    carts.setdefault(uid, []).append({**{"key":key,"name":it["name"]}, **({"dia":it["dia"]} if it.get("dia") else {}), **({"silver":it["silver"]} if it.get("silver") else {})})
    mid = c.message.message_id
    add_cnt.setdefault(uid, {})[mid] = add_cnt[uid].get(mid,0) + 1
    add = add_cnt[uid][mid]
    txt = block_stars(int(key.split("_")[1]), add) if key.startswith("stars_") else block(it, add)
    try:
        bot.edit_message_text(txt, c.message.chat.id, mid, reply_markup=kb_from_key(key))
        owners[mid] = uid
    except: pass
    cmid = cart_msgs.get(uid)
    try: render_cart(uid, c.message.chat.id, cmid)
    except: render_cart(uid, c.message.chat.id)
    bot.answer_callback_query(c.id, "✅ Добавлено в корзину")

@bot.callback_query_handler(func=lambda c: c.data.startswith("rm|"))
def cb_rm(c):
    if not check_owner(c): return
    uid = c.from_user.id
    i = int(c.data.split("|")[1])
    items = carts.get(uid, [])
    if 0 <= i < len(items): items.pop(i)
    p = cart_pages.get(uid, 0)
    tp = max(1, (len(items)+3)//4)
    if p >= tp:
        p = tp-1; cart_pages[uid] = p
    if not items:
        mid = cart_msgs.get(uid)
        if mid:
            try: bot.delete_message(c.message.chat.id, mid)
            except: pass
        cart_msgs[uid] = None
        bot.answer_callback_query(c.id, "🗑 Корзина очищена")
        return
    render_cart(uid, c.message.chat.id, c.message.message_id)
    bot.answer_callback_query(c.id, "❌ Удалено")

@bot.callback_query_handler(func=lambda c: c.data == "cart_clear")
def cb_clear(c):
    if not check_owner(c): return
    uid = c.from_user.id
    carts[uid] = []
    mid = cart_msgs.get(uid)
    if mid:
        try: bot.delete_message(c.message.chat.id, mid)
        except: pass
    cart_msgs[uid] = None
    bot.answer_callback_query(c.id, "🗑 Корзина очищена")

@bot.callback_query_handler(func=lambda c: c.data == "cart_prev")
def cb_prev(c):
    if not check_owner(c): return
    uid = c.from_user.id
    cart_pages[uid] = max(0, cart_pages.get(uid,0)-1)
    render_cart(uid, c.message.chat.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "cart_next")
def cb_next(c):
    if not check_owner(c): return
    uid = c.from_user.id
    items = carts.get(uid, [])
    tp = max(1, (len(items)+3)//4)
    cart_pages[uid] = min(tp-1, cart_pages.get(uid,0)+1)
    render_cart(uid, c.message.chat.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "cart_noop")
def cb_noop(c): bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "cart_back")
def cb_back_cart(c):
    if not check_owner(c): return
    uid = c.from_user.id
    mid = cart_msgs.get(uid)
    if mid:
        try: bot.delete_message(c.message.chat.id, mid)
        except: pass
    cart_msgs[uid] = None
    msg = bot.send_message(c.message.chat.id, menu_text(), reply_markup=main_menu())
    menu_msgs[uid] = msg.message_id
    owners[msg.message_id] = uid
    del_menu(c.message.chat.id, uid)

@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def cb_back(c):
    if not check_owner(c): return
    uid = c.from_user.id
    try:
        bot.edit_message_text(menu_text(), c.message.chat.id, c.message.message_id, reply_markup=main_menu())
        owners[c.message.message_id] = uid
    except: pass

@bot.message_handler(func=lambda m: True)
def unknown(m):
    bot.send_message(m.chat.id, "❌ Команда не распознана.\nНапишите ещё раз и проверьте написание\nили дождитесь @yra228kil1")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000))), daemon=True).start()
    print("Бот запущен...")
    bot.infinity_polling()
