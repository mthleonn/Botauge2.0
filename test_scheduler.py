#!/usr/bin/env python3
"""
Script para testar a configuração do scheduler e jobs
"""

import os
import pytz
import logging
from datetime import datetime, time
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Timezone
TIMEZONE = pytz.timezone('America/Sao_Paulo')

async def test_job():
    """Job de teste"""
    now = datetime.now(TIMEZONE)
    logger.info(f"🎯 JOB DE TESTE EXECUTADO ÀS: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

def test_scheduler_configuration():
    """Testa a configuração do scheduler"""
    logger.info("🧪 Testando configuração do scheduler...")
    
    # Cria scheduler
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    
    # Horário atual
    now = datetime.now(TIMEZONE)
    logger.info(f"⏰ Horário atual: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Testa configuração dos jobs como no bot original
    jobs_config = [
        {
            'name': 'daily_morning_message',
            'time': time(7, 0, 0, tzinfo=TIMEZONE),
            'description': 'Mensagem matinal às 7:00'
        },
        {
            'name': 'daily_afternoon_motivational',
            'time': time(14, 0, 0, tzinfo=TIMEZONE),
            'description': 'Primeira mensagem motivacional às 14:00'
        },
        {
            'name': 'daily_evening_motivational',
            'time': time(20, 0, 0, tzinfo=TIMEZONE),
            'description': 'Segunda mensagem motivacional às 20:00'
        },
        {
            'name': 'market_open_message',
            'time': time(10, 0, 0, tzinfo=TIMEZONE),
            'description': 'Abertura do pregão às 10:00 (seg-sex)',
            'days': (0, 1, 2, 3, 4)
        },
        {
            'name': 'market_close_message',
            'time': time(17, 0, 0, tzinfo=TIMEZONE),
            'description': 'Fechamento do pregão às 17:00 (seg-sex)',
            'days': (0, 1, 2, 3, 4)
        }
    ]
    
    logger.info("\n📋 CONFIGURAÇÃO DOS JOBS:")
    logger.info("="*60)
    
    for job_config in jobs_config:
        job_time = job_config['time']
        
        # Adiciona job de teste
        if 'days' in job_config:
            scheduler.add_job(
                test_job,
                trigger='cron',
                hour=job_time.hour,
                minute=job_time.minute,
                second=job_time.second,
                day_of_week=','.join(map(str, job_config['days'])),
                timezone=TIMEZONE,
                id=job_config['name']
            )
        else:
            scheduler.add_job(
                test_job,
                trigger='cron',
                hour=job_time.hour,
                minute=job_time.minute,
                second=job_time.second,
                timezone=TIMEZONE,
                id=job_config['name']
            )
        
        # Calcula próxima execução
        trigger = CronTrigger(
            hour=job_time.hour,
            minute=job_time.minute,
            second=job_time.second,
            day_of_week=','.join(map(str, job_config.get('days', range(7)))),
            timezone=TIMEZONE
        )
        
        next_run = trigger.get_next_fire_time(None, now)
        
        logger.info(f"📅 {job_config['name']}:")
        logger.info(f"   ⏰ Horário: {job_time.strftime('%H:%M:%S')}")
        logger.info(f"   📝 Descrição: {job_config['description']}")
        logger.info(f"   🔄 Próxima execução: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z') if next_run else 'N/A'}")
        
        # Verifica se deveria ter executado hoje
        today_execution = datetime.combine(now.date(), job_time.replace(tzinfo=None)).replace(tzinfo=TIMEZONE)
        if 'days' not in job_config or now.weekday() in job_config['days']:
            if today_execution < now:
                logger.info(f"   ⚠️  DEVERIA TER EXECUTADO HOJE ÀS {today_execution.strftime('%H:%M:%S')}!")
            else:
                logger.info(f"   ✅ Ainda vai executar hoje às {today_execution.strftime('%H:%M:%S')}")
        else:
            logger.info(f"   ℹ️  Não executa hoje (dia da semana: {now.strftime('%A')})")
        
        logger.info("")
    
    # Lista jobs ativos
    logger.info("🔍 JOBS ATIVOS NO SCHEDULER:")
    for job in scheduler.get_jobs():
        logger.info(f"   • {job.id}")
    
    logger.info("="*60)
    
    # Verifica timezone
    logger.info(f"\n🌍 TIMEZONE CONFIGURADO: {TIMEZONE}")
    logger.info(f"🕐 HORÁRIO LOCAL: {datetime.now()}")
    logger.info(f"🕐 HORÁRIO BRASIL: {datetime.now(TIMEZONE)}")

if __name__ == "__main__":
    test_scheduler_configuration()