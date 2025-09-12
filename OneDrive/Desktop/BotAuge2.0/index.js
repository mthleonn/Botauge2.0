require('dotenv').config();
const { Telegraf } = require('telegraf');

// Verificar se o token do bot foi fornecido
const BOT_TOKEN = process.env.BOT_TOKEN;

if (!BOT_TOKEN) {
  console.error('❌ Erro: BOT_TOKEN não encontrado nas variáveis de ambiente!');
  console.log('💡 Dica: Crie um arquivo .env com BOT_TOKEN=seu_token_aqui');
  process.exit(1);
}

// Inicializar o bot
const bot = new Telegraf(BOT_TOKEN);

// Comando /start
bot.start((ctx) => {
  ctx.reply('Bot online 🚀');
});

// Middleware para log de mensagens (opcional)
bot.use((ctx, next) => {
  console.log(`📨 Mensagem recebida de ${ctx.from.first_name}: ${ctx.message?.text || 'Mídia/Comando'}`);
  return next();
});

// Tratamento de erros
bot.catch((err, ctx) => {
  console.error('❌ Erro no bot:', err);
});

// Iniciar o bot
bot.launch()
  .then(() => {
    console.log('🤖 Bot iniciado com sucesso!');
    console.log('🔗 Pressione Ctrl+C para parar o bot');
  })
  .catch((err) => {
    console.error('❌ Erro ao iniciar o bot:', err);
    process.exit(1);
  });

// Graceful shutdown
process.once('SIGINT', () => {
  console.log('\n🛑 Parando o bot...');
  bot.stop('SIGINT');
});

process.once('SIGTERM', () => {
  console.log('\n🛑 Parando o bot...');
  bot.stop('SIGTERM');
});

// Manter o processo ativo no Railway
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);
  process.exit(1);
});