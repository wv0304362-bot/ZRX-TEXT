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

# --- SERVIDOR WEB PARA O RENDER NÃO DERRUBAR O BOT ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot de Consultas VIP Rodando 24h!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# ----------------------------------------------------

TOKEN = "8718117505:AAHNsfkL5U4K9vRnjISyIx7PgfRt81RP7lw"
ID_DONO = 7714802499
LINK_CONTATO = "https://t.me/Zenithzrx"

# Força o encerramento de qualquer conexão anterior presa na API do Telegram antes de iniciar
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

def menu_planos_pagamento():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💎 10 Dias - R$ 15,00", url=LINK_CONTATO),
        types.InlineKeyboardButton("💎 30 Dias - R$ 25,00", url=LINK_CONTATO),
        types.InlineKeyboardButton("💎 100 Dias - R$ 40,00", url=LINK_CONTATO),
        types.InlineKeyboardButton("🔄 Já paguei / Verificar Acesso", callback_data="verificar_liberacao")
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

# --- PROCESSADOR DE CONSULTAS (PRIMEIRO NA ORDEM DE TEXTO) ---
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
    
    bot.send_message(cid, "Deseja realizar outra consulta?", reply_markup=menu_principal_teclado())

@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    cid = message.chat.id
    uid = message.from_user.id
    nome = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Sem username"

    if message.chat.type != 'private':
        try:
            membros = bot.get_chat_member_count(cid)
            if membros >= 200:
                bot.send_message(cid, f"🚀 Grupo com {membros} membros detectado! Bot liberado para uso no grupo.")
            else:
                bot.send_message(cid, "🤖 *Bot de Consultas Online!*\nPara usar livremente, o grupo precisa ter pelo menos 200 membros ou você pode assinar no privado.")
        except:
            pass
        return

    registrar_usuario_ativo(uid)

    if not verificar_acesso(uid):
        texto_bloqueio = (
            "⛔ *ACESSO RESTRITO / PLANO EXPIRADO*\n\n"
            "Este bot é pago. Escolha um dos planos abaixo para adquirir seu acesso:\n\n"
            "​💎 *10 Dias:* R$ 15,00\n"
            "​💎 *30 Dias:* R$ 25,00\n"
            "​💎 *100 Dias:* R$ 40,00\n\n"
            "Clique no botão abaixo para falar com o dono e comprar:"
        )
        bot.send_message(cid, texto_bloqueio, parse_mode="Markdown", reply_markup=menu_planos_pagamento())

        notificacao_dono = (
            "🚨 *NOVO USUÁRIO TENTOU USAR O BOT*\n\n"
            f"👤 *Nome:* {nome}\n"
            f"🆔 *ID:* `{uid}`\n"
            f"🔗 *User:* {username}\n\n"
            "Deseja liberar o acesso rapidamente?"
        )
        markup_dono = types.InlineKeyboardMarkup(row_width=3)
        markup_dono.add(
            types.InlineKeyboardButton("➕ 10 Dias", callback_data=f"liberar_{uid}_10"),
            types.InlineKeyboardButton("➕ 30 Dias", callback_data=f"liberar_{uid}_30"),
            types.InlineKeyboardButton("➕ 100 Dias", callback_data=f"liberar_{uid}_100")
        )
        try:
            bot.send_message(ID_DONO, notificacao_dono, parse_mode="Markdown", reply_markup=markup_dono)
        except:
            pass
        return

    texto_sucesso = (
        f"👋 Bem-vindo, *{nome}*!\n"
        f"👤 *Perfil:* {nome}\n"
        f"🆔 *ID:* `{uid}`\n\n"
        "⚡ *PAINEL DE PUXAR DADOS VIP*\n\n"
        "📋 *VALORES:*\n"
        "​💎 *10 Dias:* R$ 15,00\n"
        "​💎 *30 Dias:* R$ 25,00\n"
        "​💎 *100 Dias:* R$ 40,00\n\n"
        "Selecione abaixo o tipo de consulta que deseja realizar:"
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

@bot.callback_query_handler(func=lambda call: call.data == "verificar_liberacao")
def verificar_liberacao_btn(call):
    uid = call.from_user.id
    if verificar_acesso(uid):
        bot.answer_callback_query(call.id, "✅ Acesso liberado com sucesso!", show_alert=True)
        bot.send_message(call.message.chat.id, "🎉 Seu acesso foi confirmado! Envie /start para abrir o painel.", reply_markup=menu_principal_teclado())
    else:
        bot.answer_callback_query(call.id, "❌ Seu acesso ainda não foi aprovado pelo dono.", show_alert=True)

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
    texto = (
        "👑 *PAINEL DE ADMINISTRAÇÃO*\n\n"
        "• Para liberar usuário: `/liberar [ID] [DIAS]`\n"
        "• Para alterar foto de boas-vindas: Mande a foto no chat com a legenda `/foto`\n"
        "• Para mandar notificação geral: `/notificação [Sua Mensagem]`"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

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
        
        bot.send_message(message.chat.id, f"✅ Usuário `{uid_alvo}` liberado com sucesso por {dias} dias!", parse_mode="Markdown")
        try:
            bot.send_message(int(uid_alvo), f"🎉 Seu acesso foi liberado por {dias} dias! Envie /start.", parse_mode="Markdown")
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
        bot.send_message(message.chat.id, "✅ Foto de boas-vindas atualizada com sucesso! Agora envie /start para testar.")
        return

    try:
        partes = message.text.split(maxsplit=1)
        if len(partes) > 1:
            url_foto = partes[1].strip()
            config = carregar_config()
            config["foto_url"] = url_foto
            salvar_config(config)
            bot.send_message(message.chat.id, "✅ URL da foto de boas-vindas atualizada com sucesso!")
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
        bot.send_message(message.chat.id, "⚠️ Escreva a mensagem após o comando. Ex: `/notificação Olá a todos!`", parse_mode="Markdown")
        return
    
    usuarios = carregar_usuarios()
    enviados = 0
    erros = 0
    
    bot.send_message(message.chat.id, "📢 Disparando notificação para os usuários...")
    
    for uid_str in usuarios.keys():
        try:
            bot.send_message(int(uid_str), f"📢 *AVISO IMPORTANTE DO ADMIN:*\n\n{texto_aviso}", parse_mode="Markdown")
            enviados += 1
        except:
            erros += 1
            
    bot.send_message(message.chat.id, f"✅ Disparo concluído!\n• Enviados com sucesso: {enviados}\n• Falhas (bloquearam o bot): {erros}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cons_'))
def callback_consultas(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    
    if not verificar_acesso(uid):
        bot.answer_callback_query(call.id, "❌ Seu acesso expirou ou não foi pago.", show_alert=True)
        return

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

print("[*] BOT DE CONSULTAS VIP COMPLETO ONLINE...")
bot.infinity_polling(skip_pending=True)
