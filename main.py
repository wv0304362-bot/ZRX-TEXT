# -*- coding: utf-8 -*-
import telebot
from telebot import types
import time
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- PEQUENO SERVIDOR WEB PARA O RENDER NÃO DERRUBAR O BOT ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot do Telegram rodando 24h com sucesso!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# Inicia o servidor web em segundo plano numa "linha" separada (thread)
threading.Thread(target=run_server, daemon=True).start()
# -------------------------------------------------------------

ID_MASTER = 7714802499
ID_CANAL_OBRIGATORIO = "@TROPADAVX5"
LINK_CANAL_OBRIGATORIO = "https://t.me/TROPADAVX5"
TOKEN = "8983788536:AAH4Qt03cF5k2LoJERnJ6smwlAqdUEI6OQI"

bot = telebot.TeleBot(TOKEN)
dados_usuario = {}
            
def inicializar_arquivos():
    if not os.path.exists('admins.json'):
        with open('admins.json', 'w', encoding='utf-8') as f:
            json.dump([ID_MASTER], f, indent=2)
    if not os.path.exists('textos.json'):
        estrutura = {"KWAI":{},"INSTAGRAM":{},"WHATSAPP":{},"TIKTOK":{},"TELEGRAM":{},"DISCORD":{}}
        with open('textos.json', 'w', encoding='utf-8') as f:
            json.dump(estrutura, f, ensure_ascii=False, indent=2)

inicializar_arquivos()

def eh_admin(uid):
    with open('admins.json', 'r', encoding='utf-8') as f:
        return uid in json.load(f)

def usuario_esta_no_grupo(uid):
    if eh_admin(uid): return True
    try:
        m = bot.get_chat_member(ID_CANAL_OBRIGATORIO, uid)
        return m.status in ['member', 'administrator', 'creator']
    except:
        return True

def gerar_botoes_plataformas():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    with open('textos.json', 'r', encoding='utf-8') as f:
        banco = json.load(f)
    plataformas = list(banco.keys())
    for i in range(0, len(plataformas), 2):
        par = plataformas[i:i+2]
        if len(par) == 2:
            markup.row(types.KeyboardButton(f"📱 {par[0]}"), types.KeyboardButton(f"📱 {par[1]}"))
        else:
            markup.row(types.KeyboardButton(f"📱 {par[0]}"))
    return markup

def gerar_botoes_redes_sociais():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📺 YouTube", url="https://www.youtube.com/@ARCANJO_OFC7"))
    markup.row(types.InlineKeyboardButton("🟢 Canal do WhatsApp", url="https://whatsapp.com/channel/0029VbDAbKy4tRrwVxWQgv02"))
    markup.row(types.InlineKeyboardButton("✈️ Canal ZRX Nexarion", url="https://t.me/zrxnexarion"))
    markup.row(types.InlineKeyboardButton("💥 Tropa da VX5", url="https://t.me/TROPADAVX5"))
    markup.row(types.InlineKeyboardButton("💬 Discord Suporte", url="https://discord.gg/MH5UEqN6d"))
    return markup

@bot.message_handler(commands=['start', 'help'])
def menu_inicial(message):
    cid = message.chat.id
    uid = message.from_user.id
    if cid in dados_usuario: del dados_usuario[cid]
    bot.clear_step_handler_by_chat_id(chat_id=cid)

    if not usuario_esta_no_grupo(uid):
        mk = types.InlineKeyboardMarkup()
        mk.row(types.InlineKeyboardButton("📢 ENTRAR NA TROPA DA VX5", url=LINK_CANAL_OBRIGATORIO))
        mk.row(types.InlineKeyboardButton("🔄 JÁ ENTREI! VERIFICAR", url=f"https://t.me/{bot.get_me().username}?start=verify"))
        bot.send_message(cid, "⚠️ *ACESSO RESTRITO!*\n\nEntre no canal para liberar.", parse_mode="Markdown", reply_markup=mk)
        return

    bot.send_message(cid, "┌── [ 玄武 XUANWU V5 - LIVRE ] ──┐\n│ Escolha a plataforma abaixo:     \n└────────────────────────────────┘", reply_markup=gerar_botoes_plataformas())
    bot.send_message(cid, "🔗 *NOSSAS REDES OFICIAIS:*", parse_mode="Markdown", reply_markup=gerar_botoes_redes_sociais())

@bot.message_handler(commands=['paineladmin'])
def painel_adm(message):
    cid = message.chat.id
    if not eh_admin(message.from_user.id): return
    mk = types.InlineKeyboardMarkup()
    mk.row(types.InlineKeyboardButton("👑 Adicionar Novo Admin", callback_data="admin_add_novo"))
    mk.row(types.InlineKeyboardButton("➕ Adicionar Plataforma", callback_data="admin_add_plataforma"))
    mk.row(types.InlineKeyboardButton("✍️ Cadastrar Texto / Trava", callback_data="admin_novo_texto_menu"))
    mk.row(types.InlineKeyboardButton("🗑️ Limpar Rede Inteira", callback_data="admin_remover_texto_menu"))
    bot.send_message(cid, "⚙️ *PAINEL DE GERENCIAMENTO MASTER*", parse_mode="Markdown", reply_markup=mk)

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("📱 "))
def selecionar_plataforma(message):
    cid = message.chat.id
    if not usuario_esta_no_grupo(message.from_user.id): return
    plat = message.text.replace("📱 ", "").strip().upper()
    dados_usuario[cid] = {"plataforma_selecionada": plat}
    with open('textos.json', 'r', encoding='utf-8') as f:
        banco = json.load(f)
    categorias = list(banco.get(plat, {}).keys())
    if not categorias:
        bot.send_message(cid, f"⚠️ Nenhuma categoria para {plat} ainda.")
        return
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for cat in categorias: mk.add(types.KeyboardButton(f"📁 {cat}"))
    bot.send_message(cid, f"📱 *Plataforma:* {plat}\nSelecione a categoria:", parse_mode="Markdown", reply_markup=mk)

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("📁 "))
def processar_categoria_selecionada(message):
    cid = message.chat.id
    if not usuario_esta_no_grupo(message.from_user.id) or cid not in dados_usuario: return
    cat = message.text.replace("📁 ", "").strip().upper()
    plat = dados_usuario[cid]["plataforma_selecionada"]
    with open('textos.json', 'r', encoding='utf-8') as f:
        banco = json.load(f)
    lista = banco.get(plat, {}).get(cat, [])
    if not lista:
        bot.send_message(cid, "⚠️ Nenhum script ativo aqui.")
        return
    bot.send_message(cid, f"⚡ Carregando *{plat}*...", parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
    for idx, txt in enumerate(lista, 1):
        bot.send_message(cid, f"📋 *TEXTO [{idx}] - {cat}*\n\n`{txt}`\n\n⚡ _Clique para copiar!_", parse_mode="Markdown")
        time.sleep(0.3)
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add(types.KeyboardButton("/start"))
    bot.send_message(cid, "↩️ Use para voltar:", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('admin_', 'delplat_')))
def callbacks_admin(call):
    cid = call.message.chat.id
    if not eh_admin(call.from_user.id): return
    if call.data == "admin_add_novo":
        bot.send_message(cid, "👤 Envie o ID do novo Admin:")
        bot.register_next_step_handler(call.message, salvar_novo_admin_db)
    elif call.data == "admin_add_plataforma":
        bot.send_message(cid, "➕ Digite o nome da nova rede:")
        bot.register_next_step_handler(call.message, salvar_nova_plataforma_db)
    elif call.data == "admin_novo_texto_menu":
        with open('textos.json', 'r', encoding='utf-8') as f:
            banco = json.load(f)
        mk = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for p in banco.keys(): mk.add(types.KeyboardButton(p))
        bot.send_message(cid, "Selecione a PLATAFORMA:", reply_markup=mk)
        bot.register_next_step_handler(call.message, passo_add_texto_plataforma)
    elif call.data == "admin_remover_texto_menu":
        with open('textos.json', 'r', encoding='utf-8') as f:
            banco = json.load(f)
        mk = types.InlineKeyboardMarkup()
        for p in banco.keys(): mk.add(types.InlineKeyboardButton(p, callback_data=f"delplat_{p}"))
        bot.edit_message_text("🗑️ Selecione qual rede limpar:", cid, call.message.message_id, reply_markup=mk)
    elif call.data.startswith('delplat_'):
        p_alvo = call.data.split('_')[1]
        with open('textos.json', 'r', encoding='utf-8') as f:
            banco = json.load(f)
        banco[p_alvo] = {}
        with open('textos.json', 'w', encoding='utf-8') as f:
            json.dump(banco, f, ensure_ascii=False, indent=2)
        bot.send_message(cid, f"✅ Banco {p_alvo} resetado!")

def salvar_novo_admin_db(message):
    if message.text.strip().isdigit():
        nid = int(message.text.strip())
        with open('admins.json', 'r', encoding='utf-8') as f: ads = json.load(f)
        if nid not in ads:
            ads.append(nid)
            with open('admins.json', 'w', encoding='utf-8') as f: json.dump(ads, f)
        bot.send_message(message.chat.id, "✅ Admin adicionado!")

def salvar_nova_plataforma_db(message):
    np = message.text.strip().upper()
    with open('textos.json', 'r', encoding='utf-8') as f: banco = json.load(f)
    if np in banco: return
    banco[np] = {}
    with open('textos.json', 'w', encoding='utf-8') as f: json.dump(banco, f, ensure_ascii=False, indent=2)
    bot.send_message(message.chat.id, f"✅ Plataforma {np} criada!")

def passo_add_texto_plataforma(message):
    dados_usuario[message.chat.id] = {"adm_plat": message.text.strip().upper()}
    bot.send_message(message.chat.id, "📝 Digite a categoria/violação:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, passo_add_texto_categoria)

def passo_add_texto_categoria(message):
    dados_usuario[message.chat.id]["adm_cat"] = message.text.strip().upper()
    bot.send_message(message.chat.id, "✍️ Digite ou cole a trava/texto agora:")
    bot.register_next_step_handler(message, passo_add_texto_final)

def passo_add_texto_final(message):
    cid = message.chat.id
    txt = message.text.strip()
    plat = dados_usuario[cid]["adm_plat"]
    cat = dados_usuario[cid]["adm_cat"]
    with open('textos.json', 'r', encoding='utf-8') as f: banco = json.load(f)
    if cat not in banco[plat]: banco[plat][cat] = []
    banco[plat][cat].append(txt)
    with open('textos.json', 'w', encoding='utf-8') as f: json.dump(banco, f, ensure_ascii=False, indent=2)
    bot.send_message(cid, f"✅ Adicionado com sucesso em {plat} -> {cat}!")

print("[*] SERVIDOR WEB E BOT ONLINE NO RENDER...")
bot.infinity_polling()
