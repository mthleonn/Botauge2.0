#!/usr/bin/env python3
"""
Script para testar o verificador de mensagens perdidas
"""

import os
import asyncio
import pytz
import logging
from dotenv import load_dotenv
from telegram import Bot
from missed_messages_checker import MissedMessagesChecker

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
TIMEZONE = pytz.timezone('America/Sao_Paulo')

async def main():
    """Função principal de teste"""
    logger.info("🧪 Testando verificador de mensagens perdidas...")
    
    if not BOT_TOKEN or not GRUPO_PRINCIPAL_ID:
        logger.error("❌ BOT_TOKEN ou GRUPO_PRINCIPAL_ID não configurados!")
        return
    
    # Cria bot e verificador
    bot = Bot(token=BOT_TOKEN)
    checker = MissedMessagesChecker(bot, GRUPO_PRINCIPAL_ID, TIMEZONE)
    
    # Verifica mensagens perdidas
    results = await checker.check_and_send_missed_messages(max_delay_hours=12)
    
    logger.info("="*50)
    logger.info("📊 RESULTADO FINAL:")
    logger.info(f"✅ Mensagens enviadas: {results['sent']}")
    logger.info(f"❌ Mensagens falharam: {results['failed']}")
    logger.info(f"⏭️ Mensagens puladas: {results['skipped']}")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(main())