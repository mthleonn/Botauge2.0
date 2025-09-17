#!/usr/bin/env python3
"""
Script para testar a integração da verificação de mensagens perdidas no bot
"""

import os
import sys
import asyncio
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Importa as classes necessárias
from missed_messages_checker import MissedMessagesChecker

async def test_integration():
    """Testa a integração da verificação de mensagens perdidas"""
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    GRUPO_PRINCIPAL_ID = int(os.getenv('GRUPO_PRINCIPAL_ID', 0))
    TIMEZONE = pytz.timezone('America/Sao_Paulo')
    
    if not BOT_TOKEN or not GRUPO_PRINCIPAL_ID:
        logger.error("❌ BOT_TOKEN ou GRUPO_PRINCIPAL_ID não configurados")
        return
    
    logger.info("🧪 Testando integração da verificação de mensagens perdidas...")
    logger.info(f"📱 Bot Token: {'*' * 10}")
    logger.info(f"👥 Grupo Principal ID: {GRUPO_PRINCIPAL_ID}")
    logger.info("-" * 50)
    
    try:
        # Simula a verificação que seria feita no bot
        logger.info("🔍 Simulando verificação de mensagens perdidas...")
        checker = MissedMessagesChecker(BOT_TOKEN, GRUPO_PRINCIPAL_ID, TIMEZONE)
        
        # Executa a verificação
        results = await checker.check_and_send_missed_messages()
        
        # Relatório
        logger.info("📊 Relatório da integração:")
        logger.info(f"   ✅ Mensagens enviadas: {results['sent']}")
        logger.info(f"   ❌ Falhas: {results['failed']}")
        logger.info(f"   ⏭️ Mensagens puladas: {results['skipped']}")
        
        if results['sent'] > 0:
            logger.info("✅ Integração funcionando! Mensagens perdidas foram enviadas.")
        elif results['failed'] > 0:
            logger.warning("⚠️ Houve falhas no envio de mensagens.")
        else:
            logger.info("✅ Integração funcionando! Nenhuma mensagem perdida encontrada.")
            
    except Exception as e:
        logger.error(f"❌ Erro na integração: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    logger.info("🚀 Iniciando teste de integração...")
    asyncio.run(test_integration())
    logger.info("🏁 Teste de integração concluído!")