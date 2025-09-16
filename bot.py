#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Auge Traders - Sistema de Automação para Grupos de Trading
Versão: 1.0.0
Data: Janeiro 2024
"""

import os
import logging
import sqlite3
import pytz
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    JobQueue
)
from telegram.constants import ParseMode
from dotenv import load_dotenv
from flask import Flask, request

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurações do bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 8000))
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
GRUPO_PRINCIPAL_ID = int(os.getenv('GRUPO_PRINCIPAL_ID', 0))
GRUPO_DUVIDAS_ID = int(os.getenv('GRUPO_DUVIDAS_ID', 0))
TIMEZONE = pytz.timezone('America/Sao_Paulo')

# Debug das variáveis de ambiente
logger.info(f"BOT_TOKEN: {'*' * 10 if BOT_TOKEN else 'NÃO DEFINIDO'}")
logger.info(f"ADMIN_IDS: {ADMIN_IDS}")
logger.info(f"GRUPO_PRINCIPAL_ID: {GRUPO_PRINCIPAL_ID}")
logger.info(f"GRUPO_DUVIDAS_ID: {GRUPO_DUVIDAS_ID}")
logger.info(f"TIMEZONE: {TIMEZONE}")
logger.info(f"PORT: {PORT}")

# Flask app para webhook
app = Flask(__name__)

class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = 'bot_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de usuários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabela de mensagens
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    message_text TEXT,
                    message_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Tabela de reuniões
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    scheduled_time TIMESTAMP NOT NULL,
                    created_by INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Adiciona ou atualiza um usuário"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
    
    def log_message(self, user_id: int, chat_id: int, message_text: str, message_type: str = 'user'):
        """Registra uma mensagem no banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (user_id, chat_id, message_text, message_type)
                VALUES (?, ?, ?, ?)
            ''', (user_id, chat_id, message_text, message_type))
            conn.commit()
    
    def get_user_stats(self) -> Dict:
        """Retorna estatísticas dos usuários"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total de usuários
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            total_users = cursor.fetchone()[0]
            
            # Usuários hoje
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(join_date) = DATE('now') AND is_active = 1
            ''')
            users_today = cursor.fetchone()[0]
            
            # Total de mensagens
            cursor.execute('SELECT COUNT(*) FROM messages')
            total_messages = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'users_today': users_today,
                'total_messages': total_messages
            }
    
    def add_meeting(self, title: str, description: str, scheduled_time: datetime, created_by: int) -> int:
        """Adiciona uma nova reunião"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO meetings (title, description, scheduled_time, created_by)
                VALUES (?, ?, ?, ?)
            ''', (title, description, scheduled_time.isoformat(), created_by))
            conn.commit()
            return cursor.lastrowid
    
    def get_upcoming_meetings(self) -> List[Dict]:
        """Retorna reuniões futuras"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, description, scheduled_time, created_by
                FROM meetings 
                WHERE scheduled_time > datetime('now') AND is_active = 1
                ORDER BY scheduled_time ASC
            ''')
            
            meetings = []
            for row in cursor.fetchall():
                meetings.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'scheduled_time': datetime.fromisoformat(row[3]),
                    'created_by': row[4]
                })
            return meetings
    
    def get_meetings_for_notification(self, minutes_ahead: int = 30) -> List[Dict]:
        """Retorna reuniões que devem ser notificadas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now()
            notification_time = now + timedelta(minutes=minutes_ahead)
            
            cursor.execute('''
                SELECT id, title, description, scheduled_time
                FROM meetings 
                WHERE scheduled_time BETWEEN ? AND ? 
                AND is_active = 1
            ''', (now.isoformat(), notification_time.isoformat()))
            
            meetings = []
            for row in cursor.fetchall():
                meetings.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'scheduled_time': datetime.fromisoformat(row[3])
                })
            return meetings

class MessagesManager:
    """Gerenciador de mensagens predefinidas"""
    
    @staticmethod
    def get_welcome_message(group_type: str = 'principal') -> str:
        """Retorna mensagem de boas-vindas"""
        if group_type == 'principal':
            return (
                "🎯 **BEM-VINDO AO AUGE TRADERS!** 🎯\n\n"
                "Olá! Seja muito bem-vindo(a) ao nosso grupo de trading! 📈\n\n"
                "🔥 **AQUI VOCÊ VAI ENCONTRAR:**\n"
                "• Análises técnicas detalhadas\n"
                "• Estratégias comprovadas\n"
                "• Comunidade ativa e engajada\n\n"
                "📋 **REGRAS IMPORTANTES:**\n"
                "• Respeite todos os membros\n"
                "• Não faça spam\n"
                "• Mantenha o foco em trading\n"
                "• Siga as orientações dos admins\n\n"
                "💰 **VAMOS JUNTOS RUMO AO SUCESSO!** 💰\n\n"
            )
        else:  # grupo de dúvidas
            return (
                "❓ **BEM-VINDO AO GRUPO DE DÚVIDAS!** ❓\n\n"
                "Este é o espaço para tirar suas dúvidas sobre trading! 🤔\n\n"
                "📚 **AQUI VOCÊ PODE:**\n"
                "• Fazer perguntas sobre análise técnica\n"
                "• Esclarecer dúvidas sobre estratégias\n"
                "• Pedir ajuda com plataformas\n"
                "• Compartilhar experiências\n\n"
                "🎯 **DICAS PARA BOAS PERGUNTAS:**\n"
                "• Seja específico\n"
                "• Compartilhe prints quando necessário\n"
                "• Use as hashtags: #duvida #ajuda #analise\n\n"
                "👥 **Nossa comunidade está aqui para ajudar!**\n\n"
            )
    
    @staticmethod
    def get_morning_message() -> str:
        """Mensagem motivacional matinal"""
        return (
            "🌅 **BOM DIA, TRADERS!** 🌅\n\n"
            "Mais um dia de oportunidades nos mercados! 📈\n\n"
            "💪 **LEMBRE-SE:**\n"
            "• Disciplina é a chave do sucesso\n"
            "• Gerencie sempre o risco\n"
            "• Mantenha a calma nas operações\n"
            "• Foque na consistência, não na sorte\n\n"
            "🎯 **HOJE É DIA DE LUCRAR COM INTELIGÊNCIA!**\n\n"
            "Bom trading a todos! 🚀"
        )
    
    @staticmethod
    def get_alert_message() -> str:
        """Mensagem de alerta para oportunidades"""
        return (
            "🚨 **ATENÇÃO TRADERS!** 🚨\n\n"
            "📊 Oportunidade identificada nos mercados!\n\n"
            "⚡ **AÇÃO NECESSÁRIA:**\n"
            "• Verifique suas análises\n"
            "• Confirme as análises técnicas\n"
            "• Prepare suas estratégias\n"
            "• Gerencie o risco adequadamente\n\n"
            "💰 **VAMOS APROVEITAR ESTA OPORTUNIDADE!** 💰\n\n"
            "Fiquem atentos às próximas análises técnicas! 👀"
        )
    
    @staticmethod
    def get_motivational_message() -> str:
        """Mensagem motivacional"""
        messages = [
            (
                "💎 **MINDSET DE TRADER VENCEDOR** 💎\n\n"
                "🧠 O sucesso no trading começa na mente!\n\n"
                "✅ **CARACTERÍSTICAS DO TRADER DE SUCESSO:**\n"
                "• Disciplina inabalável\n"
                "• Gestão de risco rigorosa\n"
                "• Paciência para aguardar setups\n"
                "• Capacidade de aceitar perdas\n"
                "• Foco na consistência\n\n"
                "🚀 **VOCÊ TEM TUDO PARA SER UM VENCEDOR!** 🚀"
            ),
            (
                "📈 **FOCO NO PROCESSO, NÃO NO RESULTADO** 📈\n\n"
                "🎯 Traders consistentes focam no processo!\n\n"
                "⭐ **PROCESSO VENCEDOR:**\n"
                "• Análise técnica criteriosa\n"
                "• Entrada apenas em setups válidos\n"
                "• Stop loss sempre definido\n"
                "• Take profit planejado\n"
                "• Revisão constante das operações\n\n"
                "💪 **CONFIE NO SEU PROCESSO!** 💪"
            ),
            (
                "🎯 **PACIÊNCIA É A VIRTUDE DO TRADER** 🎯\n\n"
                "⏰ Os melhores setups exigem paciência!\n\n"
                "🔑 **LIÇÕES DE PACIÊNCIA:**\n"
                "• Aguarde o setup perfeito\n"
                "• Não force operações\n"
                "• Qualidade > Quantidade\n"
                "• O mercado sempre oferece novas chances\n"
                "• Pressa é inimiga do lucro\n\n"
                "⏳ **SEJA PACIENTE, SEJA LUCRATIVO!** ⏳"
            ),
            (
                "🛡️ **GESTÃO DE RISCO É TUDO** 🛡️\n\n"
                "💰 Proteger o capital é prioridade número 1!\n\n"
                "🔒 **REGRAS DE OURO:**\n"
                "• Nunca arrisque mais de 2% por trade\n"
                "• Stop loss é obrigatório\n"
                "• Diversifique suas operações\n"
                "• Tamanho da posição calculado\n"
                "• Preserve capital para operar amanhã\n\n"
                "🏆 **QUEM PROTEGE O CAPITAL, VENCE!** 🏆"
            ),
            (
                "📚 **EDUCAÇÃO CONTÍNUA** 📚\n\n"
                "🎓 O mercado está sempre evoluindo!\n\n"
                "📖 **SEMPRE APRENDENDO:**\n"
                "• Estude novas estratégias\n"
                "• Analise seus trades passados\n"
                "• Acompanhe traders experientes\n"
                "• Leia sobre psicologia do trading\n"
                "• Pratique em conta demo\n\n"
                "🧠 **CONHECIMENTO É PODER!** 🧠"
            ),
            (
                "⚖️ **EQUILÍBRIO EMOCIONAL** ⚖️\n\n"
                "😌 Controle emocional = Sucesso garantido!\n\n"
                "🧘 **MENTE EQUILIBRADA:**\n"
                "• Não opere com raiva\n"
                "• Aceite perdas como parte do jogo\n"
                "• Comemore vitórias com moderação\n"
                "• Mantenha a calma em volatilidade\n"
                "• Tome decisões racionais\n\n"
                "🎯 **EMOÇÃO CONTROLADA, LUCRO GARANTIDO!** 🎯"
            ),
            (
                "🔄 **CONSISTÊNCIA VENCE SORTE** 🔄\n\n"
                "📊 Pequenos ganhos consistentes > Grandes apostas!\n\n"
                "🎯 **FÓRMULA DA CONSISTÊNCIA:**\n"
                "• Siga sempre seu plano\n"
                "• Mantenha rotina de análise\n"
                "• Opere apenas setups conhecidos\n"
                "• Registre todos os trades\n"
                "• Melhore 1% a cada dia\n\n"
                "🏅 **CONSISTÊNCIA É O CAMINHO!** 🏅"
            ),
            (
                "💪 **RESILIÊNCIA DO TRADER** 💪\n\n"
                "🔥 Grandes traders se levantam após quedas!\n\n"
                "🛡️ **SEJA RESILIENTE:**\n"
                "• Perdas fazem parte do jogo\n"
                "• Aprenda com cada erro\n"
                "• Não desista nos momentos difíceis\n"
                "• Foque no longo prazo\n"
                "• Cada dia é uma nova oportunidade\n\n"
                "🌟 **VOCÊ É MAIS FORTE QUE PENSA!** 🌟"
            ),
            (
                "🎪 **ADAPTABILIDADE NO MERCADO** 🎪\n\n"
                "🌊 O mercado muda, você deve se adaptar!\n\n"
                "🔄 **SEJA FLEXÍVEL:**\n"
                "• Ajuste estratégias conforme mercado\n"
                "• Reconheça mudanças de tendência\n"
                "• Não se apegue a uma única abordagem\n"
                "• Esteja aberto a novas ideias\n"
                "• Evolua constantemente\n\n"
                "🦎 **ADAPTAÇÃO = SOBREVIVÊNCIA!** 🦎"
            ),
            (
                "🎯 **FOCO E DETERMINAÇÃO** 🎯\n\n"
                "🔍 Foco total = Resultados excepcionais!\n\n"
                "⚡ **MANTENHA O FOCO:**\n"
                "• Elimine distrações durante trades\n"
                "• Concentre-se em poucos ativos\n"
                "• Defina metas claras\n"
                "• Mantenha disciplina férrea\n"
                "• Persista nos seus objetivos\n\n"
                "🏹 **FOCO LASER, LUCROS PRECISOS!** 🏹"
            ),
            (
                "🌅 **CADA DIA É UMA NOVA CHANCE** 🌅\n\n"
                "✨ Ontem passou, hoje é sua oportunidade!\n\n"
                "🆕 **NOVO DIA, NOVA MENTALIDADE:**\n"
                "• Esqueça os erros de ontem\n"
                "• Foque nas oportunidades de hoje\n"
                "• Mantenha expectativas realistas\n"
                "• Celebre pequenas vitórias\n"
                "• Construa seu sucesso gradualmente\n\n"
                "🌟 **HOJE É SEU DIA DE BRILHAR!** 🌟"
            ),
            (
                "🏆 **MENTALIDADE DE CAMPEÃO** 🏆\n\n"
                "👑 Pense como um campeão, aja como um campeão!\n\n"
                "🥇 **ATITUDE VENCEDORA:**\n"
                "• Acredite no seu potencial\n"
                "• Prepare-se como um profissional\n"
                "• Mantenha padrões elevados\n"
                "• Nunca se conforme com mediocridade\n"
                "• Inspire outros com sua dedicação\n\n"
                "👑 **VOCÊ NASCEU PARA VENCER!** 👑"
            )
        ]
        import random
        return random.choice(messages)
    
    @staticmethod
    def get_market_open_message() -> str:
        """Mensagem de abertura do pregão"""
        return (
            "🟢 **PREGÃO ABERTO** 🟢\n\n"
            "Ei, pessoal! 🚀\n"
            "O pregão já começou, bora pra cima!\n\n"
            "Lembrem-se: estratégia e análise de mercado são a chave do lucro. 🔑"
        )
    
    @staticmethod
    def get_market_close_message() -> str:
        """Mensagem de fechamento do pregão"""
        return (
            "🔴 **PREGÃO ENCERRADO** 🔴\n\n"
            "Valeu, galera! ✅\n"
            "Pregão de hoje encerrado.\n"
            "Parabéns a todos!\n\n"
            "Se quiserem compartilhar seus resultados, entrem no nosso grupo de dúvidas para conversarmos. 💬"
        )
    
    @staticmethod
    def get_error_message(error_type: str = 'generic') -> str:
        """Mensagens de erro"""
        errors = {
            'permission': "❌ Você não tem permissão para executar este comando.",
            'invalid_command': "❌ Comando inválido. Use /help para ver os comandos disponíveis.",
            'generic': "❌ Ocorreu um erro. Tente novamente ou contate um administrador.",
            'meeting_format': "❌ Formato inválido. Use: /set_meeting DD/MM/AAAA HH:MM Título da Reunião"
        }
        return errors.get(error_type, errors['generic'])

# Instância global do gerenciador de banco
db_manager = DatabaseManager()

# Funções de verificação
def is_admin(user_id: int) -> bool:
    """Verifica se o usuário é administrador"""
    return user_id in ADMIN_IDS

def is_group_chat(chat_id: int) -> bool:
    """Verifica se é um chat de grupo"""
    return chat_id in [GRUPO_PRINCIPAL_ID, GRUPO_DUVIDAS_ID]

# Handlers de comandos
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Adiciona usuário ao banco
    db_manager.add_user(user.id, user.username, user.first_name, user.last_name)
    
    if chat.type == 'private':
        message = (
            "🤖 **Bot Auge Traders** 🤖\n\n"
            "Olá! Eu sou o bot oficial do Auge Traders.\n\n"
            "📋 **Comandos disponíveis:**\n"
            "/help - Lista todos os comandos\n"
            "/stats - Estatísticas do grupo (admins)\n\n"
            "Para mais informações, entre em contato com os administradores."
        )
    else:
        # Mensagem de boas-vindas para grupos
        group_type = 'principal' if chat.id == GRUPO_PRINCIPAL_ID else 'duvidas'
        message = MessagesManager.get_welcome_message(group_type)
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        message = (
            "🔧 **COMANDOS ADMINISTRATIVOS** 🔧\n\n"
            "📊 **Estatísticas:**\n"
            "/stats - Estatísticas do bot\n\n"
            "📝 **Mensagens:**\n"
            "/mensagens - Menu de mensagens\n"
            "/morning - Mensagem matinal\n"
            "/alert - Mensagem de alerta\n"
            "/motivacional - Mensagem motivacional\n\n"
            "📅 **Reuniões:**\n"
            "/set_meeting - Agendar reunião\n"
            "/test_meeting - Testar notificação\n\n"
            "👥 **Usuários:**\n"
            "/start - Comando inicial"
        )
    else:
        message = (
            "📋 **COMANDOS DISPONÍVEIS** 📋\n\n"
            "🤖 **Básicos:**\n"
            "/start - Iniciar bot\n"
            "/help - Esta mensagem\n\n"
            "💬 **Para mais comandos, contate os administradores.**"
        )
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats - apenas para admins"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(MessagesManager.get_error_message('permission'))
        return
    
    stats = db_manager.get_user_stats()
    now = datetime.now(TIMEZONE)
    
    message = (
        f"📊 **ESTATÍSTICAS DO BOT** 📊\n\n"
        f"👥 **Usuários:**\n"
        f"• Total: {stats['total_users']}\n"
        f"• Novos hoje: {stats['users_today']}\n\n"
        f"💬 **Mensagens:**\n"
        f"• Total processadas: {stats['total_messages']}\n\n"
        f"🕐 **Última atualização:**\n"
        f"{now.strftime('%d/%m/%Y às %H:%M')}"
    )
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

# Comandos administrativos de mensagens
async def mensagens_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /mensagens - menu de mensagens para admins"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(MessagesManager.get_error_message('permission'))
        return
    
    keyboard = [
        [InlineKeyboardButton("🌅 Mensagem Matinal", callback_data="select_group_morning")],
        [InlineKeyboardButton("🚨 Alerta de Oportunidade", callback_data="select_group_alert")],
        [InlineKeyboardButton("💪 Mensagem Motivacional", callback_data="select_group_motivational")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 **MENU DE MENSAGENS**\n\nEscolha o tipo de mensagem para enviar:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /morning - envia mensagem matinal"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(MessagesManager.get_error_message('permission'))
        return
    
    keyboard = [
        [InlineKeyboardButton("🎯 Grupo Principal", callback_data="send_morning_principal")],
        [InlineKeyboardButton("❓ Grupo de Dúvidas", callback_data="send_morning_duvidas")],
        [InlineKeyboardButton("📢 Ambos os Grupos", callback_data="send_morning_both")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌅 **MENSAGEM MATINAL**\n\nPara onde deseja enviar?",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /alert - envia mensagem de alerta"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(MessagesManager.get_error_message('permission'))
        return
    
    keyboard = [
        [InlineKeyboardButton("🎯 Grupo Principal", callback_data="send_alert_principal")],
        [InlineKeyboardButton("❓ Grupo de Dúvidas", callback_data="send_alert_duvidas")],
        [InlineKeyboardButton("📢 Ambos os Grupos", callback_data="send_alert_both")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🚨 **ALERTA DE OPORTUNIDADE**\n\nPara onde deseja enviar?",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def motivacional_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /motivacional - envia mensagem motivacional"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(MessagesManager.get_error_message('permission'))
        return
    
    keyboard = [
        [InlineKeyboardButton("🎯 Grupo Principal", callback_data="send_motivational_principal")],
        [InlineKeyboardButton("❓ Grupo de Dúvidas", callback_data="send_motivational_duvidas")],
        [InlineKeyboardButton("📢 Ambos os Grupos", callback_data="send_motivational_both")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "💪 **MENSAGEM MOTIVACIONAL**\n\nPara onde deseja enviar?",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

# Handler para callbacks dos botões inline
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para callbacks dos botões inline"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.edit_message_text(MessagesManager.get_error_message('permission'))
        return
    
    # Seleção de grupo para mensagens
    if query.data.startswith("select_group_"):
        message_type = query.data.replace("select_group_", "")
        keyboard = [
            [InlineKeyboardButton("🎯 Grupo Principal", callback_data=f"send_{message_type}_principal")],
            [InlineKeyboardButton("❓ Grupo de Dúvidas", callback_data=f"send_{message_type}_duvidas")],
            [InlineKeyboardButton("📢 Ambos os Grupos", callback_data=f"send_{message_type}_both")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_names = {
            "morning": "Matinal",
            "alert": "Alerta de Oportunidade", 
            "motivational": "Motivacional"
        }
        
        await query.edit_message_text(
            f"📍 **SELECIONE O GRUPO DE DESTINO**\n\nMensagem: {message_names.get(message_type, message_type)}\n\nPara onde deseja enviar?",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Voltar ao menu principal
    if query.data == "back_to_menu":
        keyboard = [
            [InlineKeyboardButton("🌅 Mensagem Matinal", callback_data="select_group_morning")],
            [InlineKeyboardButton("🚨 Alerta de Oportunidade", callback_data="select_group_alert")],
            [InlineKeyboardButton("💪 Mensagem Motivacional", callback_data="select_group_motivational")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📝 **MENU DE MENSAGENS**\n\nEscolha o tipo de mensagem para enviar:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Envio de mensagens para grupos específicos
    if query.data.startswith("send_"):
        parts = query.data.split("_")
        if len(parts) >= 3:
            message_type = parts[1]
            target_group = "_".join(parts[2:])
            
            # Obter a mensagem correta
            if message_type == "morning":
                message = MessagesManager.get_morning_message()
                type_name = "matinal"
            elif message_type == "alert":
                message = MessagesManager.get_alert_message()
                type_name = "de alerta"
            elif message_type == "motivational":
                message = MessagesManager.get_motivational_message()
                type_name = "motivacional"
            else:
                await query.edit_message_text("❌ Tipo de mensagem não reconhecido.")
                return
            
            # Determinar grupos de destino
            target_chats = []
            group_names = []
            
            if target_group == "principal" and GRUPO_PRINCIPAL_ID:
                target_chats.append(GRUPO_PRINCIPAL_ID)
                group_names.append("Grupo Principal")
            elif target_group == "duvidas" and GRUPO_DUVIDAS_ID:
                target_chats.append(GRUPO_DUVIDAS_ID)
                group_names.append("Grupo de Dúvidas")
            elif target_group == "both":
                if GRUPO_PRINCIPAL_ID:
                    target_chats.append(GRUPO_PRINCIPAL_ID)
                    group_names.append("Grupo Principal")
                if GRUPO_DUVIDAS_ID:
                    target_chats.append(GRUPO_DUVIDAS_ID)
                    group_names.append("Grupo de Dúvidas")
            
            if not target_chats:
                await query.edit_message_text("❌ Nenhum grupo configurado para envio.")
                return
            
            # Enviar mensagens
            success_count = 0
            for chat_id in target_chats:
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem {type_name} para {chat_id}: {e}")
            
            if success_count == len(target_chats):
                groups_text = " e ".join(group_names)
                await query.edit_message_text(f"✅ Mensagem {type_name} enviada com sucesso para: {groups_text}!")
            elif success_count > 0:
                await query.edit_message_text(f"⚠️ Mensagem {type_name} enviada parcialmente. Verifique os logs.")
            else:
                await query.edit_message_text(f"❌ Erro ao enviar mensagem {type_name}. Verifique as configurações.")
        else:
            await query.edit_message_text("❌ Formato de callback inválido.")
    else:
        await query.edit_message_text("❌ Ação não reconhecida.")

# Comandos de reunião
async def set_meeting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /set_meeting - agenda uma reunião"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(MessagesManager.get_error_message('permission'))
        return
    
    if len(context.args) < 3:
        await update.message.reply_text(MessagesManager.get_error_message('meeting_format'))
        return
    
    try:
        # Parse da data e hora: DD/MM/AAAA HH:MM
        date_str = context.args[0]
        time_str = context.args[1]
        title = ' '.join(context.args[2:])
        
        # Converte para datetime
        datetime_str = f"{date_str} {time_str}"
        meeting_time = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M")
        meeting_time = TIMEZONE.localize(meeting_time)
        
        # Verifica se a data é futura
        if meeting_time <= datetime.now(TIMEZONE):
            await update.message.reply_text("❌ A data da reunião deve ser futura.")
            return
        
        # Adiciona reunião ao banco
        meeting_id = db_manager.add_meeting(
            title=title,
            description=f"Reunião agendada por {update.effective_user.first_name}",
            scheduled_time=meeting_time,
            created_by=update.effective_user.id
        )
        
        # Agenda job para notificação
        context.job_queue.run_once(
            meeting_notification_job,
            when=meeting_time - timedelta(minutes=30),
            data={'meeting_id': meeting_id, 'title': title, 'time': meeting_time},
            name=f"meeting_notification_{meeting_id}"
        )
        
        formatted_time = meeting_time.strftime("%d/%m/%Y às %H:%M")
        message = (
            f"✅ **REUNIÃO AGENDADA** ✅\n\n"
            f"📅 **Data:** {formatted_time}\n"
            f"📋 **Título:** {title}\n\n"
            f"🔔 Os membros serão notificados 30 minutos antes da reunião."
        )
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
    except ValueError:
        await update.message.reply_text(MessagesManager.get_error_message('meeting_format'))
    except Exception as e:
        logger.error(f"Erro ao agendar reunião: {e}")
        await update.message.reply_text("❌ Erro ao agendar reunião. Tente novamente.")

async def test_meeting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /test_meeting - testa notificação de reunião"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(MessagesManager.get_error_message('permission'))
        return
    
    # Cria uma reunião de teste para 1 minuto no futuro
    test_time = datetime.now(TIMEZONE) + timedelta(minutes=1)
    
    message = (
        f"🧪 **TESTE DE REUNIÃO** 🧪\n\n"
        f"📅 **Data:** {test_time.strftime('%d/%m/%Y às %H:%M')}\n"
        f"📋 **Título:** Reunião de Teste\n\n"
        f"🔔 Notificação será enviada em 30 segundos."
    )
    
    # Agenda notificação para 30 segundos
    context.job_queue.run_once(
        meeting_notification_job,
        when=30,  # 30 segundos
        data={'meeting_id': 0, 'title': 'Reunião de Teste', 'time': test_time},
        name="test_meeting_notification"
    )
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

# Job para notificações de reunião
async def meeting_notification_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que envia notificações de reunião"""
    job_data = context.job.data
    title = job_data['title']
    meeting_time = job_data['time']
    
    formatted_time = meeting_time.strftime("%d/%m/%Y às %H:%M")
    
    message = (
        f"🔔 **LEMBRETE DE REUNIÃO** 🔔\n\n"
        f"📅 **Data:** {formatted_time}\n"
        f"📋 **Título:** {title}\n\n"
        f"⏰ **A reunião começará em 30 minutos!**\n\n"
        f"🎯 Preparem-se e não percam esta oportunidade de aprendizado!"
    )
    
    # Envia para o grupo principal
    if GRUPO_PRINCIPAL_ID:
        try:
            await context.bot.send_message(
                chat_id=GRUPO_PRINCIPAL_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"Notificação de reunião enviada: {title}")
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de reunião: {e}")

# Job para mensagens automáticas diárias
async def daily_morning_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que envia mensagem matinal automaticamente"""
    message = MessagesManager.get_morning_message()
    
    if GRUPO_PRINCIPAL_ID:
        try:
            await context.bot.send_message(
                chat_id=GRUPO_PRINCIPAL_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Mensagem matinal automática enviada")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem matinal automática: {e}")

async def daily_afternoon_motivational_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que envia primeira mensagem motivacional da tarde automaticamente"""
    message = MessagesManager.get_motivational_message()
    
    if GRUPO_PRINCIPAL_ID:
        try:
            await context.bot.send_message(
                chat_id=GRUPO_PRINCIPAL_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Primeira mensagem motivacional automática enviada (tarde)")
        except Exception as e:
            logger.error(f"Erro ao enviar primeira mensagem motivacional automática: {e}")

async def daily_evening_motivational_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que envia segunda mensagem motivacional da noite automaticamente"""
    message = MessagesManager.get_motivational_message()
    
    if GRUPO_PRINCIPAL_ID:
        try:
            await context.bot.send_message(
                chat_id=GRUPO_PRINCIPAL_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Segunda mensagem motivacional automática enviada (noite)")
        except Exception as e:
            logger.error(f"Erro ao enviar segunda mensagem motivacional automática: {e}")

async def market_open_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que envia mensagem de abertura do pregão (segunda a sexta às 10:00)"""
    message = MessagesManager.get_market_open_message()
    
    if GRUPO_PRINCIPAL_ID:
        try:
            await context.bot.send_message(
                chat_id=GRUPO_PRINCIPAL_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Mensagem de abertura do pregão enviada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de abertura do pregão: {e}")

async def market_close_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que envia mensagem de fechamento do pregão (segunda a sexta às 17:00)"""
    message = MessagesManager.get_market_close_message()
    
    if GRUPO_PRINCIPAL_ID:
        try:
            await context.bot.send_message(
                chat_id=GRUPO_PRINCIPAL_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Mensagem de fechamento do pregão enviada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de fechamento do pregão: {e}")

# Handler para novos membros
async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para novos membros do grupo"""
    for member in update.message.new_chat_members:
        # Adiciona usuário ao banco
        db_manager.add_user(member.id, member.username, member.first_name, member.last_name)
        
        # Debug: Log dos IDs para verificar
        chat_id = update.effective_chat.id
        logger.info(f"Novo membro no chat {chat_id}. GRUPO_PRINCIPAL_ID: {GRUPO_PRINCIPAL_ID}, GRUPO_DUVIDAS_ID: {GRUPO_DUVIDAS_ID}")
        
        # Determina tipo do grupo
        if chat_id == GRUPO_PRINCIPAL_ID:
            group_type = 'principal'
            logger.info(f"Identificado como grupo principal")
        elif chat_id == GRUPO_DUVIDAS_ID:
            group_type = 'duvidas'
            logger.info(f"Identificado como grupo de dúvidas")
        else:
            group_type = 'principal'  # Default para grupo principal
            logger.warning(f"Chat ID {chat_id} não reconhecido, usando grupo principal como padrão")
        
        welcome_msg = MessagesManager.get_welcome_message(group_type)
        
        # Adiciona botões inline apenas para o grupo principal
        if group_type == 'principal':
            keyboard = [
                [InlineKeyboardButton("📚 Mentoria Completa", url="https://www.mentoriaaugetraders.com.br/")],
                [InlineKeyboardButton("❓ Grupo de Dúvidas", url="https://t.me/+5ueqV0IGf7NlODIx")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"👋 Olá {member.first_name}!\n\n{welcome_msg}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"👋 Olá {member.first_name}!\n\n{welcome_msg}",
                parse_mode=ParseMode.MARKDOWN
            )

# Handler para mensagens gerais
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para todas as mensagens"""
    user = update.effective_user
    chat = update.effective_chat
    message_text = update.message.text or ""
    
    # Log da mensagem
    db_manager.log_message(user.id, chat.id, message_text, 'user')
    
    # Adiciona/atualiza usuário
    db_manager.add_user(user.id, user.username, user.first_name, user.last_name)

# Função principal
def main():
    """Função principal do bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN não encontrado nas variáveis de ambiente")
        return
    
    # Cria a aplicação
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Adiciona handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("mensagens", mensagens_command))
    application.add_handler(CommandHandler("morning", morning_command))
    application.add_handler(CommandHandler("alert", alert_command))
    application.add_handler(CommandHandler("motivacional", motivacional_command))
    application.add_handler(CommandHandler("set_meeting", set_meeting_command))
    application.add_handler(CommandHandler("test_meeting", test_meeting_command))
    
    # Handler para callbacks dos botões inline
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Configura jobs diários para mensagens automáticas
    job_queue = application.job_queue
    
    # Mensagem matinal (7:00 AM)
    job_queue.run_daily(
        daily_morning_job,
        time=time(7, 0, 0, tzinfo=TIMEZONE),
        name="daily_morning_message"
    )
    logger.info("Job agendado: Mensagem matinal às 7:00 AM")
    
    # Primeira mensagem motivacional (14:00 PM - 2:00 PM)
    job_queue.run_daily(
        daily_afternoon_motivational_job,
        time=time(14, 0, 0, tzinfo=TIMEZONE),
        name="daily_afternoon_motivational"
    )
    logger.info("Job agendado: Primeira mensagem motivacional às 14:00 PM")
    
    # Segunda mensagem motivacional (20:00 PM - 8:00 PM)
    job_queue.run_daily(
        daily_evening_motivational_job,
        time=time(20, 0, 0, tzinfo=TIMEZONE),
        name="daily_evening_motivational"
    )
    logger.info("Job agendado: Segunda mensagem motivacional às 20:00 PM")
    
    # Jobs do pregão (segunda a sexta-feira)
    job_queue.run_daily(
        market_open_job,
        time=time(10, 0, 0, tzinfo=TIMEZONE),
        days=(0, 1, 2, 3, 4),
        name="market_open_message"
    )
    logger.info("Job agendado: Abertura do pregão às 10:00 AM (segunda a sexta)")
    
    job_queue.run_daily(
        market_close_job,
        time=time(17, 0, 0, tzinfo=TIMEZONE),
        days=(0, 1, 2, 3, 4),
        name="market_close_message"
    )
    logger.info("Job agendado: Fechamento do pregão às 17:00 PM (segunda a sexta)")
    
    # Handler para novos membros
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
    
    # Handler para mensagens gerais
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Configuração para Railway (webhook) ou desenvolvimento (polling)
    if WEBHOOK_URL:
        # Modo webhook para produção
        @app.route(f'/{BOT_TOKEN}', methods=['POST'])
        def webhook():
            update = Update.de_json(request.get_json(), application.bot)
            application.update_queue.put_nowait(update)
            return 'OK'
        
        @app.route('/')
        def index():
            return 'Bot Auge Traders está rodando!'
        
        @app.route('/health')
        def health():
            return 'OK'
        
        # Configura webhook
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )
    else:
        # Modo polling para desenvolvimento - Railway também pode usar polling
        logger.info("Iniciando bot em modo polling...")
        
        # Adiciona endpoint básico para Railway
        @app.route('/')
        def index():
            return 'Bot Auge Traders está rodando em modo polling!'
        
        @app.route('/health')
        def health():
            return 'OK'
        
        # Inicia Flask em thread separada para Railway
        import threading
        def run_flask():
            app.run(host="0.0.0.0", port=PORT)
        
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Inicia polling
        application.run_polling()

if __name__ == '__main__':
    main()