# -*- coding: utf-8 -*-
import telebot
from telebot import types
import os
import json
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SERVIDOR WEB PARA O RENDER NÃO DERRUBAR O BOT ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot de Consultas Rodando 24h!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# ----------------------------------------------------

TOKEN = "8718117505:AAHNsfkL5U4K9vRnjISyIx7PgfRt81RP7lw"
bot = telebot.TeleBot(TOKEN)
aguardando_input = {}

def menu_principal_teclado():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔍 Consulta CPF", callback_data="cons_cpf"),
        types.InlineKeyboardButton("📱 Consulta Telefone", callback_data="cons_tel"),
        types.InlineKeyboardButton("📧 Consulta E-mail", callback_data="cons_email"),
        types.InlineKeyboardButton("🪪 Consulta RG", callback_data="cons_rg"),
        types.InlineKeyboardButton("👤 Consulta Nome", callback_data="cons_nome"),
        types.InlineKeyboardButton("📍 Consulta CEP", callback_data="cons_cep"),
        types.InlineKeyboardButton("👥 Consulta Parente", callback_data="cons_parente"),
        types.InlineKeyboardButton("📄 Consulta SPC (Doc/Nome)", callback_data="cons_spc")
    )
    return markup

@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    cid = message.chat.id
    texto = (
        "🤖 *CENTRAL DE CONSULTAS DE DADOS*\n\n"
        "Selecione abaixo o tipo de consulta que deseja realizar através dos botões:"
    )
    bot.send_message(cid, texto, parse_mode="Markdown", reply_markup=menu_principal_teclado())

@bot.callback_query_handler(func=lambda call: call.data.startswith('cons_'))
def callback_consultas(call):
    cid = call.message.chat.id
    tipo = call.data
    
    instrucoes = {
        "cons_cpf": "📌 Envie o **CPF** (somente números) para realizar a consulta:",
        "cons_tel": "📱 Envie o **Telefone** (com DDD) para realizar a consulta:",
        "cons_email": "📧 Envie o **E-mail** para realizar a consulta:",
        "cons_rg": "🪪 Envie o **RG** para realizar a consulta:",
        "cons_nome": "👤 Envie o **Nome completo** para realizar a consulta:",
        "cons_cep": "📍 Envie o **CEP** para realizar a consulta:",
        "cons_parente": "👥 Envie o **CPF do Parente** para consulta:",
        "cons_spc": "📄 Envie o **Documento ou Nome** para a consulta SPC:"
    }
    
    aguardando_input[cid] = tipo
    bot.answer_callback_query(call.id)
    bot.send_message(cid, instrucoes.get(tipo, "Envie o dado solicitado:"), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.chat.id in aguardando_input)
def processar_consulta(message):
    cid = message.chat.id
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
            conteudo = resposta.text
            
            # Limita o tamanho caso a resposta seja muito longa para o Telegram
            if len(conteudo) > 4000:
                conteudo = conteudo[:4000] + "\n\n... (Resultado cortado por excesso de caracteres)"
            
            if not conteudo.strip():
                conteudo = "Nenhum dado encontrado para esta consulta."

            bot.send_message(cid, f"📋 *Resultado da Consulta:*\n\n`{conteudo}`", parse_mode="Markdown")
        else:
            bot.send_message(cid, "⚠️ Tipo de consulta inválido.")
            
    except Exception as e:
        bot.send_message(cid, f"❌ Erro ao conectar com a API: `{str(e)}`", parse_mode="Markdown")
    
    # Retorna o menu principal após a consulta
    bot.send_message(cid, "Deseja realizar outra consulta?", reply_markup=menu_principal_teclado())

print("[*] BOT DE CONSULTAS ONLINE...")
bot.infinity_polling()
