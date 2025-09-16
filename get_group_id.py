#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para capturar ID de grupos do Telegram
Use este script para descobrir o ID correto dos seus grupos
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')

async def capture_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura e exibe o ID do grupo quando recebe uma mensagem"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type in ['group', 'supergroup']:
        print("\n" + "="*60)
        print("🎯 GRUPO DETECTADO!")
        print("="*60)
        print(f"📋 Nome do Grupo: {chat.title}")
        print(f"🆔 ID do Grupo: {chat.id}")
        print(f"📝 Tipo: {chat.type}")
        print(f"👤 Usuário que enviou: {user.first_name} (@{user.username})")
        print(f"💬 Mensagem: {update.message.text[:50]}...")
        print("="*60)
        print(f"✅ COPIE ESTE ID: {chat.id}")
        print("="*60 + "\n")
        
        # Log também no arquivo
        logger.info(f"GRUPO DETECTADO - Nome: {chat.title}, ID: {chat.id}, Tipo: {chat.type}")
        
        # Responde no grupo (opcional)
        try:
            await update.message.reply_text(
                f"🤖 **ID CAPTURADO!**\n\n"
                f"📋 **Grupo:** {chat.title}\n"
                f"🆔 **ID:** `{chat.id}`\n\n"
                f"✅ Use este ID nas suas configurações!",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Erro ao responder no grupo: {e}")
    
    elif chat.type == 'private':
        await update.message.reply_text(
            "🤖 **Bot Capturador de ID de Grupos**\n\n"
            "📋 **Como usar:**\n"
            "1. Adicione este bot ao seu grupo\n"
            "2. Envie qualquer mensagem no grupo\n"
            "3. O bot mostrará o ID do grupo\n\n"
            "💡 **Dica:** Dê permissões de administrador ao bot para garantir que funcione!"
        )

def main():
    """Função principal"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN não encontrado no arquivo .env!")
        return
    
    print("🚀 Iniciando Bot Capturador de ID de Grupos...")
    print("📋 Instruções:")
    print("1. Adicione o bot aos grupos que deseja capturar o ID")
    print("2. Envie qualquer mensagem no grupo")
    print("3. O ID será exibido aqui no terminal e no próprio grupo")
    print("4. Pressione Ctrl+C para parar\n")
    
    # Cria a aplicação
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Adiciona handler para todas as mensagens
    application.add_handler(MessageHandler(filters.ALL, capture_group_id))
    
    # Inicia o bot
    try:
        application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n🛑 Bot parado pelo usuário.")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()