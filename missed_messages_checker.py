#!/usr/bin/env python3
"""
Módulo para verificar e enviar mensagens perdidas quando o bot reinicia
"""

import os
import pytz
import logging
from datetime import datetime, time, date
from typing import List, Dict
from telegram import Bot
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

class MissedMessagesChecker:
    """Classe para verificar e enviar mensagens perdidas"""
    
    def __init__(self, bot_token: str, grupo_principal_id: int, timezone: pytz.BaseTzInfo):
        self.bot = Bot(token=bot_token)
        self.grupo_principal_id = grupo_principal_id
        self.timezone = timezone
        
        # Configuração das mensagens programadas
        self.scheduled_messages = [
            {
                'name': 'daily_morning_message',
                'time': time(7, 0, 0),
                'function': 'get_morning_message',
                'description': 'Mensagem matinal',
                'days': list(range(7))  # Todos os dias
            },
            {
                'name': 'daily_afternoon_motivational',
                'time': time(14, 0, 0),
                'function': 'get_motivational_message',
                'description': 'Primeira mensagem motivacional',
                'days': list(range(7))  # Todos os dias
            },
            {
                'name': 'daily_evening_motivational',
                'time': time(20, 0, 0),
                'function': 'get_motivational_message',
                'description': 'Segunda mensagem motivacional',
                'days': list(range(7))  # Todos os dias
            },
            {
                'name': 'market_open_message',
                'time': time(10, 0, 0),
                'function': 'get_market_open_message',
                'description': 'Abertura do pregão',
                'days': [0, 1, 2, 3, 4]  # Segunda a sexta
            },
            {
                'name': 'market_close_message',
                'time': time(17, 0, 0),
                'function': 'get_market_close_message',
                'description': 'Fechamento do pregão',
                'days': [0, 1, 2, 3, 4]  # Segunda a sexta
            }
        ]
    
    def get_missed_messages_today(self) -> List[Dict]:
        """Retorna lista de mensagens que deveriam ter sido enviadas hoje"""
        now = datetime.now(self.timezone)
        today = now.date()
        current_weekday = now.weekday()
        
        missed_messages = []
        
        for msg_config in self.scheduled_messages:
            # Verifica se a mensagem deveria ser enviada hoje
            if current_weekday not in msg_config['days']:
                continue
            
            # Calcula horário da mensagem hoje
            msg_time = datetime.combine(today, msg_config['time']).replace(tzinfo=self.timezone)
            
            # Se o horário já passou, considera como perdida
            if msg_time < now:
                missed_messages.append({
                    'config': msg_config,
                    'scheduled_time': msg_time,
                    'minutes_late': int((now - msg_time).total_seconds() / 60)
                })
        
        return missed_messages
    
    async def send_missed_message(self, msg_config: Dict, minutes_late: int) -> bool:
        """Envia uma mensagem perdida"""
        try:
            # Importa MessagesManager dinamicamente para evitar import circular
            from bot import MessagesManager
            
            # Obtém a mensagem baseada na função
            if msg_config['function'] == 'get_morning_message':
                message = MessagesManager.get_morning_message()
            elif msg_config['function'] == 'get_motivational_message':
                message = MessagesManager.get_motivational_message()
            elif msg_config['function'] == 'get_market_open_message':
                message = MessagesManager.get_market_open_message()
            elif msg_config['function'] == 'get_market_close_message':
                message = MessagesManager.get_market_close_message()
            else:
                logger.error(f"Função desconhecida: {msg_config['function']}")
                return False
            
            # Adiciona nota sobre atraso se for significativo (mais de 30 minutos)
            if minutes_late > 30:
                message += f"\n\n⚠️ _Mensagem enviada com {minutes_late} minutos de atraso devido a reinicialização do sistema._"
            
            # Envia mensagem
            result = await self.bot.send_message(
                chat_id=self.grupo_principal_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"✅ Mensagem perdida enviada: {msg_config['description']} (ID: {result.message_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem perdida {msg_config['description']}: {e}")
            return False
    
    async def check_and_send_missed_messages(self, max_delay_hours: int = 4) -> Dict:
        """Verifica e envia mensagens perdidas"""
        logger.info("🔍 Verificando mensagens perdidas...")
        
        missed_messages = self.get_missed_messages_today()
        
        if not missed_messages:
            logger.info("✅ Nenhuma mensagem perdida encontrada")
            return {'sent': 0, 'failed': 0, 'skipped': 0}
        
        results = {'sent': 0, 'failed': 0, 'skipped': 0}
        
        for missed in missed_messages:
            config = missed['config']
            minutes_late = missed['minutes_late']
            hours_late = minutes_late / 60
            
            logger.info(f"📋 Mensagem perdida: {config['description']} ({minutes_late} min de atraso)")
            
            # Pula mensagens muito antigas (mais de X horas)
            if hours_late > max_delay_hours:
                logger.info(f"⏭️ Pulando {config['description']} - muito antiga ({hours_late:.1f}h)")
                results['skipped'] += 1
                continue
            
            # Envia mensagem
            success = await self.send_missed_message(config, minutes_late)
            
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
        
        logger.info(f"📊 Resultado: {results['sent']} enviadas, {results['failed']} falharam, {results['skipped']} puladas")
        return results