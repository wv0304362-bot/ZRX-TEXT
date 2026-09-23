# -*- coding: utf-8 -*-
import telebot
from telebot import types
import os
import json
import requests
import threading
import time
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SERVIDOR WEB PARA O RENDER E UPTIMEROBOT ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot de Consultas VIP Rodando 24h!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# ----------------------------------------------------

TOKEN = "8718117505:AAE3Mzg1LoN6xXitx6qmLPXX08Rlstxct-w"
ID_DONO = 7714802499
LINK_CONTATO = "https://t.me/Zenithzrx"
LINK_WHATSAPP_CANAL = "https://whatsapp.com/channel/0029ValKVsrBFLgb53LmY22v"

# Força o encerramento de qualquer conexão anterior presa na API do Telegram para evitar erro 409
import urllib.request
try:
    urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True").read()
    time.sleep(1)
except Exception as e:
    print(f"Erro ao limpar webhook anterior: {e}")

bot = telebot.TeleBot(TOKEN)

aguardando_input = {}
ARQUIVO_USUARIOS = "usuarios_autorizados.json"
ARQUIVO_CONFIG = "config_foto.json"
ARQUIVO_PRECOS = "config_precos.json"

PRECOS_DEFAULT = {
    "10": "R$ 15,00",
    "30": "R$ 25,00",
    "100": "R$ 40,00"
}

def carregar_precos():
    if not os.path.exists(ARQUIVO_PRECOS):
        return PRECOS_DEFAULT
    with open(ARQUIVO_PRECOS, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return PRECOS_DEFAULT

def salvar_precos(dados):
    with open(ARQUIVO_PRECOS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_config():
    if not os.path.exists(ARQUIVO_CONFIG):
        return {"foto_url": None}
    with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {"foto_url": None}

def salvar_config(dados):
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        return {}
    with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {}

def salvar_usuarios(dados):
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def verificar_acesso(uid):
    if int(uid) == ID_DONO:
        return True
    usuarios = carregar_usuarios()
    str_uid = str(uid)
    if str_uid in usuarios:
        validade_str = usuarios[str_uid].get("validade")
        if validade_str:
            validade = datetime.fromisoformat(validade_str)
            if datetime.now() < validade:
                return True
    return False

def registrar_usuario_ativo(uid):
    usuarios = carregar_usuarios()
    str_uid = str(uid)
    if str_uid not in usuarios and int(uid) != ID_DONO:
        usuarios[str_uid] = {"validade": ""}
        salvar_usuarios(usuarios)

def menu_principal_teclado():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💡 all - menu (Ver Consultas)", callback_data="abrir_menu_consultas"),
        types.InlineKeyboardButton("💰 my - info (Ver Preços)", callback_data="ver_precos_menu"),
        types.InlineKeyboardButton("📢 contact - whatsapp (Canal)", url=LINK_WHATSAPP_CANAL)
    )
    return markup

def menu_consultas_tabela():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 Consulta CPF", callback_data="cons_cpf"),
        types.InlineKeyboardButton("📱 Consulta Telefone", callback_data="cons_tel"),
        types.InlineKeyboardButton("📧 Consulta E-mail", callback_data="cons_email"),
        types.InlineKeyboardButton("🪪 Consulta RG", callback_data="cons_rg"),
        types.InlineKeyboardButton("👤 Consulta Nome", callback_data="cons_nome"),
        types.InlineKeyboardButton("📍 Consulta CEP", callback_data="cons_cep"),
        types.InlineKeyboardButton("👥 Consulta Parente", callback_data="cons_parente"),
        types.InlineKeyboardButton("📄 Consulta SPC (Doc/Nome)", callback_data="cons_spc"),
        types.InlineKeyboardButton("⬅️ Voltar ao Início", callback_data="voltar_inicio")
    )
    return markup

def menu_planos_pagamento():
    precos = carregar_precos()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"💎 10 Dias - {precos.get('10')}", url=LINK_CONTATO),
        types.InlineKeyboardButton(f"💎 30 Dias - {precos.get('30')}", url=LINK_CONTATO),
        types.InlineKeyboardButton(f"💎 100 Dias - {precos.get('100')}", url=LINK_CONTATO),
        types.InlineKeyboardButton("🔄 Já paguei / Verificar Acesso", callback_data="verificar_liberacao"),
        types.InlineKeyboardButton("⬅️ Voltar ao Início", callback_data="voltar_inicio")
    )
    return markup

def formatar_resposta_json(conteudo_texto):
    try:
        dados = json.loads(conteudo_texto)
        if isinstance(dados, dict):
            texto_formatado = "📋 *RELATÓRIO DA CONSULTA*\n\n"
            for chave, valor in dados.items():
                if valor:
                    texto_formatado += f"• *{str(chaves_amigaveis(chave))}:* {str(valor)}\n"
            return texto_formatado
        elif isinstance(dados, list):
            if not dados:
                return "⚠️ Nenhum registro encontrado."
            texto_formatado = f"📋 *RELATÓRIO DA CONSULTA* (Total: {len(dados)})\n\n"
            for i, item in enumerate(dados[:5], 1):
                texto_formatado += f"--- *Registro [{i}]* ---\n"
                if isinstance(item, dict):
                    for chave, valor in item.items():
                        if valor:
                            texto_formatado += f"• *{str(chaves_amigaveis(chave))}:* {str(valor)}\n"
                else:
                    texto_formatado += f"{str(item)}\n"
                texto_formatado += "\n"
            return texto_formatado
    except:
        pass
    
    if len(conteudo_texto) > 4000:
        return f"```\n{conteudo_texto[:4000]}\n```\n\n*(Resultado cortado por excesso de caracteres)*"
    return f"```\n{conteudo_texto}\n```"

def chaves_amigaveis(chave):
    mapa = {
        "cpf": "CPF",
        "nome": "Nome",
        "telefone": "Telefone",
        "email": "E-mail",
        "rg": "RG",
        "cep": "CEP",
        "nascimento": "Data de Nascimento",
        "mae": "Nome da Mãe"
    }
    return mapa.get(str(chave).lower(), str(chave).capitalize())

@bot.message_handler(func=lambda msg: msg.chat.id in aguardando_input)
def processar_consulta(message):
    cid = message.chat.id
    uid = message.from_user.id
    
    if not verificar_acesso(uid):
        bot.send_message(cid, "❌ Seu acesso expirou.")
        aguardando_input.pop(cid, None)
        return

    tipo = aguardando_input.pop(cid, None)
    dado = message.text.strip()
    
    bot.send_message(cid, "🔍 Buscando informações na base de dados, aguarde...")
    
    url = ""
    try:
        if tipo == "cons_cpf":
            url = f"http://apisbrasilpro.site/consulta_serasa.php?cpf={dado}"
        elif tipo == "cons_tel":
            url = f"http://apisbrasilpro.site/consulta_serasa.php?telefone={dado}"
        elif tipo == "cons_email":
            url = f"http://apisbrasilpro.site/consulta_serasa.php?email={dado}"
        elif tipo == "cons_rg":
            url = f"http://apisbrasilpro.site/consulta_serasa.php?rg={dado}"
        elif tipo == "cons_nome":
            nome_formatado = dado.replace(" ", "%20")
            url = f"http://apisbrasilpro.site/consulta_serasa.php?nome={nome_formatado}"
        elif tipo == "cons_cep":
            url = f"http://apisbrasilpro.site/telefone0.php?cep={dado}"
        elif tipo == "cons_parente":
            url = f"http://apisbrasilpro.site/consulta_serasa.php?cpf_parente={dado}"
        elif tipo == "cons_spc":
            if dado.isdigit():
                url = f"http://apisbrasilpro.site/spc1.php?doc={dado}"
            else:
                nome_formatado = dado.replace(" ", "%20")
                url = f"http://apisbrasilpro.site/spc1.php?nome={nome_formatado}"
        
        if url:
            resposta = requests.get(url, timeout=15)
            conteudo_bruto = resposta.text
            
            if not conteudo_bruto.strip():
                resultado_final = "⚠️ Nenhum dado encontrado para esta consulta."
            else:
                resultado_final = formatar_resposta_json(conteudo_bruto)

            bot.send_message(cid, resultado_final, parse_mode="Markdown")
        else:
            bot.send_message(cid, "⚠️ Tipo de consulta inválido.")
            
    except Exception as e:
        bot.send_message(cid, f"❌ Erro ao conectar com a API: `{str(e)}`", parse_mode="Markdown")
    
    bot.send_message(cid, "Deseja realizar outra consulta?", reply_markup=menu_consultas_tabela())

@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    cid = message.chat.id
    uid = message.from_user.id
    
    if message.chat.type != 'private':
        return

    registrar_usuario_ativo(uid)

    if not verificar_acesso(uid):
        precos = carregar_precos()
        texto_bloqueio = (
            "⛔ *ACESSO RESTRITO / PLANO EXPIRADO*\n\n"
            "Este bot é pago. Escolha um dos planos abaixo para adquirir seu acesso:\n\n"
            f"💎 10 Dias: {precos.get('10')}\n"
            f"💎 30 Dias: {precos.get('30')}\n"
            f"💎 100 Dias: {precos.get('100')}\n\n"
            "Clique no botão abaixo para falar com o suporte e comprar:"
        )
        markup_bloqueio = types.InlineKeyboardMarkup(row_width=1)
        markup_bloqueio.add(
            types.InlineKeyboardButton("💬 Comprar com @Zenithzrx", url=LINK_CONTATO),
            types.InlineKeyboardButton("🔄 Já paguei / Verificar Acesso", callback_data="verificar_liberacao")
        )
        bot.send_message(cid, texto_bloqueio, parse_mode="Markdown", reply_markup=markup_bloqueio)
        return

    # Layout limpo em tabela idêntico ao modelo da imagem de referência
    texto_sucesso = (
        "✂️ **Shoyu - Xposed .**\n\n"
        "Hello — ═[ **@Zenithzrx** ]═\n"
        "★ ✂️\n\n"
        "This bot is a multi-session VIP consultation bot that allows you to manage queries from a single interface.\n\n"
        "```text\n"
        "   Information         Details   \n"
        "───────────────────────────────\n"
        " Creator            @Zenithzrx \n"
        " Version            15.0       \n"
        " Type               Main Bot   \n"
        " Mode               Public     \n"
        " Status             🟢 Online  \n"
        "```"
    )

    config = carregar_config()
    foto_url = config.get("foto_url")

    if foto_url:
        try:
            bot.send_photo(cid, foto_url, caption=texto_sucesso, parse_mode="Markdown", reply_markup=menu_principal_teclado())
            return
        except Exception as e:
            print(f"Erro ao enviar foto salva: {e}")
    
    bot.send_message(cid, texto_sucesso, parse_mode="Markdown", reply_markup=menu_principal_teclado())

@bot.callback_query_handler(func=lambda call: call.data in ["abrir_menu_consultas", "ver_precos_menu", "voltar_inicio"])
def callback_navegacao_principal(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    
    if call.data == "abrir_menu_consultas":
        if not verificar_acesso(uid):
            bot.answer_callback_query(call.id, "❌ Acesso expirado!", show_alert=True)
            return
        bot.edit_message_caption("📋 **MENU DE CONSULTAS DISPONÍVEIS:**\n\nSelecione abaixo o tipo de consulta:", chat_id=cid, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=menu_consultas_tabela())
    
    elif call.data == "ver_precos_menu":
        precos = carregar_precos()
        texto_precos = (
            "💎 **TABELA DE PREÇOS E PLANOS VIP**\n\n"
            f"• 10 Dias: `{precos.get('10')}`\n"
            f"• 30 Dias: `{precos.get('30')}`\n"
            f"• 100 Dias: `{precos.get('100')}`\n\n"
            "Clique abaixo para falar com o suporte:"
        )
        bot.edit_message_caption(texto_precos, chat_id=cid, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=menu_planos_pagamento())
    
    elif call.data == "voltar_inicio":
        texto_sucesso = (
            "✂️ **Shoyu - Xposed .**\n\n"
            "Hello — ═[ **@Zenithzrx** ]═\n"
            "★ ✂️\n\n"
            "```text\n"
            "   Information         Details   \n"
            "───────────────────────────────\n"
            " Creator            @Zenithzrx \n"
            " Version            15.0       \n"
            " Type               Main Bot   \n"
            " Mode               Public     \n"
            " Status             🟢 Online  \n"
            "```"
        )
        try:
            bot.edit_message_caption(texto_sucesso, chat_id=cid, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=menu_principal_teclado())
        except:
            bot.edit_message_text(texto_sucesso, chat_id=cid, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=menu_principal_teclado())

@bot.callback_query_handler(func=lambda call: call.data == "verificar_liberacao")
def verificar_liberacao_btn(call):
    uid = call.from_user.id
    if verificar_acesso(uid):
        bot.answer_callback_query(call.id, "✅ Acesso liberado com sucesso!", show_alert=True)
        bot.send_message(call.message.chat.id, "🎉 Seu acesso foi confirmado! Envie /start para abrir o painel.")
    else:
        bot.answer_callback_query(call.id, "❌ Seu acesso ainda não foi aprovado.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('liberar_'))
def callback_liberar_dono(call):
    if call.from_user.id != ID_DONO:
        bot.answer_callback_query(call.id, "❌ Apenas o dono pode fazer isso!", show_alert=True)
        return
    
    partes = call.data.split('_')
    uid_alvo = partes[1]
    dias = int(partes[2])
    
    usuarios = carregar_usuarios()
    nova_validade = datetime.now() + timedelta(days=dias)
    usuarios[uid_alvo] = {"validade": nova_validade.isoformat()}
    salvar_usuarios(usuarios)
    
    bot.answer_callback_query(call.id, f"✅ Liberado por {dias} dias!")
    bot.edit_message_text(f"{call.message.text}\n\n✅ *STATUS: LIBERADO por {dias} dias!*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    
    try:
        bot.send_message(int(uid_alvo), f"🎉 *SEU ACESSO FOI LIBERADO!*\nAproveite por {dias} dias. Envie /start para usar o bot.", parse_mode="Markdown")
    except:
        pass

@bot.message_handler(commands=['paineladmin'])
def painel_admin(message):
    if message.from_user.id != ID_DONO:
        return
    precos = carregar_precos()
    texto = (
        "👑 *PAINEL DE ADMINISTRAÇÃO*\n\n"
        "• Liberar usuário: `/liberar [ID] [DIAS]`\n"
        "• Alterar foto: Mande a foto com a legenda `/foto`\n"
        "• Modificar preços: `/setpreco [10/30/100] [Valor]`\n"
        "• Clonar bot: `/adicionar_bot [TOKEN]`\n"
        "• Notificar todos: `/notificação [Mensagem]`\n\n"
        f"📋 **Preços Atuais:**\n- 10d: {precos.get('10')}\n- 30d: {precos.get('30')}\n- 100d: {precos.get('100')}"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(commands=['setpreco'])
def comando_set_preco(message):
    if message.from_user.id != ID_DONO:
        return
    try:
        partes = message.text.split(maxsplit=2)
        plano = partes[1]
        novo_valor = partes[2]
        
        if plano not in ["10", "30", "100"]:
            bot.send_message(message.chat.id, "⚠️ Use: `/setpreco 10 R$ 15,00`", parse_mode="Markdown")
            return
            
        precos = carregar_precos()
        precos[plano] = novo_valor
        salvar_precos(precos)
        bot.send_message(message.chat.id, f"✅ Preço do plano de {plano} dias atualizado para: `{novo_valor}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "⚠️ Formato incorreto. Use: `/setpreco [10/30/100] [Valor]`", parse_mode="Markdown")

@bot.message_handler(commands=['adicionar_bot'])
def comando_adicionar_bot(message):
    if message.from_user.id != ID_DONO:
        return
    try:
        partes = message.text.split(maxsplit=1)
        token_novo = partes[1].strip()
        
        nome_arquivo_bot = f"bot_cliente_{int(time.time())}.py"
        
        codigo_template = f'''# -*- coding: utf-8 -*-
import telebot
from telebot import types
import os, json, requests, time
from datetime import datetime, timedelta

TOKEN = "{token_novo}"
ID_DONO = {ID_DONO}
LINK_CONTATO = "{LINK_CONTATO}"
LINK_WHATSAPP_CANAL = "{LINK_WHATSAPP_CANAL}"

bot = telebot.TeleBot(TOKEN)
ARQUIVO_USUf = "usuarios_{token_novo[:6]}.json"

def carregar_u():
    if not os.path.exists(ARQUIVO_USUf): return {{}}
    with open(ARQUIVO_USUf, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {{}}

def verificar(uid):
    if int(uid) == ID_DONO: return True
    us = carregar_u()
    if str(uid) in us and us[str(uid)].get("v"):
        return datetime.now() < datetime.fromisoformat(us[str(uid)]["v"])
    return False

@bot.message_handler(commands=['start'])
def start_c(message):
    cid = message.chat.id
    uid = message.from_user.id
    if not verificar(uid):
        txt = "⛔ **ACESSO RESTRITO - PAGO**\\n\\nAdquira seu acesso com @Zenithzrx:"
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("💬 Comprar com @Zenithzrx", url=LINK_CONTATO))
        bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)
        return
    
    txt = (
        "✂️ **Shoyu - Xposed .**\\n\\n"
        "Hello — ═[ **@Zenithzrx** ]═\\n\\n"
        "```text\\n"
        "   Information         Details   \\n"
        "───────────────────────────────\\n"
        " Creator            @Zenithzrx \\n"
        " Status             🟢 Online  \\n"
        "```"
    )
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(
        types.InlineKeyboardButton("💡 all - menu", callback_data="menu"),
        types.InlineKeyboardButton("💰 my - info (Preços)", url=LINK_CONTATO),
        types.InlineKeyboardButton("📢 WhatsApp Canal", url=LINK_WHATSAPP_CANAL)
    )
    bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=mk)

print("Bot cliente rodando...")
bot.infinity_polling()
'''
        with open(nome_arquivo_bot, 'w', encoding='utf-8') as f:
            f.write(codigo_template)
            
        threading.Thread(target=lambda: os.system(f"python {nome_arquivo_bot}"), daemon=True).start()
        bot.send_message(message.chat.id, f"✅ **Bot clonado com sucesso!** Rodando em background.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Erro ao gerar bot: `{str(e)}`", parse_mode="Markdown")

@bot.message_handler(commands=['liberar'])
def comando_liberar_manual(message):
    if message.from_user.id != ID_DONO:
        return
    try:
        partes = message.text.split()
        uid_alvo = partes[1]
        dias = int(partes[2])
        
        usuarios = carregar_usuarios()
        nova_validade = datetime.now() + timedelta(days=dias)
        usuarios[uid_alvo] = {"validade": nova_validade.isoformat()}
        salvar_usuarios(usuarios)
        
        bot.send_message(message.chat.id, f"✅ Usuário `{uid_alvo}` liberado por {dias} dias!", parse_mode="Markdown")
        try:
            bot.send_message(int(uid_alvo), f"🎉 Acesso liberado por {dias} dias! Envie /start.", parse_mode="Markdown")
        except:
            pass
    except:
        bot.send_message(message.chat.id, "⚠️ Uso incorreto. Use: `/liberar [ID] [DIAS]`", parse_mode="Markdown")

@bot.message_handler(commands=['foto'], content_types=['photo', 'text'])
def comando_foto(message):
    if message.from_user.id != ID_DONO:
        return
    
    if message.photo:
        fileID = message.photo[-1].file_id
        config = carregar_config()
        config["foto_url"] = fileID
        salvar_config(config)
        bot.send_message(message.chat.id, "✅ Foto de boas-vindas atualizada com sucesso!")
        return

    try:
        partes = message.text.split(maxsplit=1)
        if len(partes) > 1:
            url_foto = partes[1].strip()
            config = carregar_config()
            config["foto_url"] = url_foto
            salvar_config(config)
            bot.send_message(message.chat.id, "✅ URL da foto atualizada com sucesso!")
        else:
            bot.send_message(message.chat.id, "⚠️ Envie a foto diretamente no chat com a legenda `/foto`.", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "⚠️ Erro ao atualizar a foto.")

@bot.message_handler(commands=['notificação', 'notificacao'])
def comando_notificacao(message):
    if message.from_user.id != ID_DONO:
        return
    
    texto_aviso = message.text.replace("/notificação", "").replace("/notificacao", "").strip()
    if not texto_aviso:
        bot.send_message(message.chat.id, "⚠️ Escreva a mensagem após o comando.", parse_mode="Markdown")
        return
    
    usuarios = carregar_usuarios()
    enviados = 0
    erros = 0
    
    bot.send_message(message.chat.id, "📢 Disparando notificação...")
    
    for uid_str in usuarios.keys():
        try:
            bot.send_message(int(uid_str), f"📢 *AVISO DO ADMIN:*\n\n{texto_aviso}", parse_mode="Markdown")
            enviados += 1
        except:
            erros += 1
            
    bot.send_message(message.chat.id, f"✅ Concluído! Enviados: {enviados} | Falhas: {erros}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cons_'))
def callback_consultas(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    
    if not verificar_acesso(uid):
        bot.answer_callback_query(call.id, "❌ Seu acesso expirou.", show_alert=True)
        return

    tipo = call.data
    instrucoes = {
        "cons_cpf": "📌 Envie o **CPF** (somente números):",
        "cons_tel": "📱 Envie o **Telefone** (com DDD):",
        "cons_email": "📧 Envie o **E-mail**:",
        "cons_rg": "🪪 Envie o **RG**:",
        "cons_nome": "👤 Envie o **Nome completo**:",
        "cons_cep": "📍 Envie o **CEP**:",
        "cons_parente": "👥 Envie o **CPF do Parente**:",
        "cons_spc": "📄 Envie o **Documento ou Nome** para o SPC:"
    }
    
    aguardando_input[cid] = tipo
    bot.answer_callback_query(call.id)
    bot.send_message(cid, instrucoes.get(tipo, "Envie o dado solicitado:"), parse_mode="Markdown")

print("[*] BOT DE CONSULTAS VIP ESTILO SHOYU PERFEITO ONLINE...")
bot.infinity_polling(skip_pending=True)
