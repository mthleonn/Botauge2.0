#!/usr/bin/env python3
"""
Script de teste para verificar se as mensagens programadas funcionam
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variáveis de ambiente
BOT_TOKEN = os.getenv('BOT_TOKEN')
GRUPO_PRINCIPAL_ID = int(os.getenv('GRUPO_PRINCIPAL_ID', 0))

# Importa as classes necessárias do bot principal
import sys
sys.path.append('.')
from bot import MessagesManager

async def test_morning_message():
    """Testa o envio da mensagem matinal"""
    try:
        bot = Bot(token=BOT_TOKEN)
        message = MessagesManager.get_morning_message()
        
        logger.info(f"Mensagem matinal gerada: {message[:100]}...")
        logger.info(f"Enviando para grupo: {GRUPO_PRINCIPAL_ID}")
        
        result = await bot.send_message(
            chat_id=GRUPO_PRINCIPAL_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"✅ Mensagem matinal enviada com sucesso! ID: {result.message_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem matinal: {e}")
        return False

async def test_motivational_message():
    """Testa o envio da mensagem motivacional"""
    try:
        bot = Bot(token=BOT_TOKEN)
        message = MessagesManager.get_motivational_message()
        
        logger.info(f"Mensagem motivacional gerada: {message[:100]}...")
        logger.info(f"Enviando para grupo: {GRUPO_PRINCIPAL_ID}")
        
        result = await bot.send_message(
            chat_id=GRUPO_PRINCIPAL_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"✅ Mensagem motivacional enviada com sucesso! ID: {result.message_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem motivacional: {e}")
        return False

async def main():
    """Função principal de teste"""
    logger.info("🧪 Iniciando teste das mensagens programadas...")
    logger.info(f"BOT_TOKEN: {'*' * 10 if BOT_TOKEN else 'NÃO DEFINIDO'}")
    logger.info(f"GRUPO_PRINCIPAL_ID: {GRUPO_PRINCIPAL_ID}")
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN não definido!")
        return
    
    if not GRUPO_PRINCIPAL_ID:
        logger.error("❌ GRUPO_PRINCIPAL_ID não definido!")
        return
    
    # Testa mensagem matinal
    logger.info("\n📅 Testando mensagem matinal...")
    morning_success = await test_morning_message()
    
    # Aguarda um pouco
    await asyncio.sleep(2)
    
    # Testa mensagem motivacional
    logger.info("\n💪 Testando mensagem motivacional...")
    motivational_success = await test_motivational_message()
    
    # Resultado final
    logger.info("\n" + "="*50)
    logger.info("📊 RESULTADO DOS TESTES:")
    logger.info(f"Mensagem matinal: {'✅ SUCESSO' if morning_success else '❌ FALHOU'}")
    logger.info(f"Mensagem motivacional: {'✅ SUCESSO' if motivational_success else '❌ FALHOU'}")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(main())