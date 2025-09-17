#!/usr/bin/env python3
"""
Script para testar se o scheduler funciona agendando uma mensagem em 1 minuto
"""

import os
import asyncio
import pytz
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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

# Bot instance
bot = Bot(token=BOT_TOKEN)

async def test_scheduled_message():
    """Mensagem de teste agendada"""
    try:
        now = datetime.now(TIMEZONE)
        message = f"🧪 **TESTE DE MENSAGEM AGENDADA** 🧪\n\n⏰ Executada às: {now.strftime('%H:%M:%S')}\n\n✅ O scheduler está funcionando corretamente!"
        
        result = await bot.send_message(
            chat_id=GRUPO_PRINCIPAL_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"✅ Mensagem de teste enviada com sucesso! ID: {result.message_id}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem de teste: {e}")

async def main():
    """Função principal"""
    logger.info("🧪 Testando scheduler com mensagem em 1 minuto...")
    
    now = datetime.now(TIMEZONE)
    test_time = now + timedelta(minutes=1)
    
    logger.info(f"⏰ Horário atual: {now.strftime('%H:%M:%S')}")
    logger.info(f"🎯 Mensagem agendada para: {test_time.strftime('%H:%M:%S')}")
    
    # Cria scheduler
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    
    # Agenda mensagem de teste
    scheduler.add_job(
        test_scheduled_message,
        'date',
        run_date=test_time,
        id='test_message'
    )
    
    # Inicia scheduler
    scheduler.start()
    logger.info("🚀 Scheduler iniciado!")
    
    # Aguarda execução
    logger.info("⏳ Aguardando execução da mensagem...")
    await asyncio.sleep(70)  # Aguarda 70 segundos
    
    # Para scheduler
    scheduler.shutdown()
    logger.info("🛑 Scheduler parado!")

if __name__ == "__main__":
    asyncio.run(main())