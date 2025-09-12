# 🤖 Bot Auge Traders

**Bot Telegram para Gestão de Grupos de Trading e Investimentos**

Um bot completo desenvolvido em Python para automatizar a gestão de grupos de trading, com funcionalidades avançadas de engajamento, notificações e administração.

## 📋 Índice

- [Características](#-características)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Deploy no Railway](#-deploy-no-railway)
- [Comandos Disponíveis](#-comandos-disponíveis)
- [Funcionalidades](#-funcionalidades)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

## ✨ Características

### 🎯 **Funcionalidades Principais**
- ✅ **Mensagens Automáticas**: Boas-vindas, matinais, motivacionais
- ✅ **Sistema de Reuniões**: Agendamento e notificações automáticas
- ✅ **Comandos Administrativos**: Controle total para admins
- ✅ **Estatísticas Avançadas**: Métricas de usuários e engajamento
- ✅ **Banco de Dados SQLite**: Persistência de dados local
- ✅ **Deploy Railway**: Configuração pronta para produção

### 🔧 **Tecnologias Utilizadas**
- **Python 3.11+**
- **python-telegram-bot 20.7**
- **SQLite3** (banco de dados)
- **Flask** (webhook server)
- **Railway** (deploy em nuvem)
- **pytz** (gerenciamento de timezone)

## 🚀 Instalação

### Pré-requisitos
- Python 3.11 ou superior
- Conta no Telegram
- Bot Token do @BotFather

### 1. Clone o Repositório
```bash
git clone https://github.com/seu-usuario/bot-auge-traders.git
cd bot-auge-traders
```

### 2. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as Variáveis de Ambiente
```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:
```env
BOT_TOKEN=seu_token_aqui
ADMIN_IDS=123456789,987654321
GRUPO_PRINCIPAL_ID=-1001234567890
GRUPO_DUVIDAS_ID=-1001234567891
```

### 4. Execute o Bot
```bash
python bot.py
```

## ⚙️ Configuração

### 📝 Variáveis de Ambiente Obrigatórias

| Variável | Descrição | Como Obter |
|----------|-----------|------------|
| `BOT_TOKEN` | Token do bot | @BotFather → /newbot |
| `ADMIN_IDS` | IDs dos administradores | @userinfobot → /start |
| `GRUPO_PRINCIPAL_ID` | ID do grupo principal | Adicionar @userinfobot ao grupo |
| `GRUPO_DUVIDAS_ID` | ID do grupo de dúvidas | Adicionar @userinfobot ao grupo |

### 🔧 Variáveis Opcionais

| Variável | Padrão | Descrição |
|----------|--------|----------|
| `WEBHOOK_URL` | - | URL para webhook (produção) |
| `PORT` | 8000 | Porta do servidor |
| `DATABASE_PATH` | bot_data.db | Caminho do banco SQLite |
| `TIMEZONE` | America/Sao_Paulo | Fuso horário |
| `LOG_LEVEL` | INFO | Nível de log |

## 🚂 Deploy no Railway

### 1. Preparação
O projeto já inclui os arquivos necessários:
- `runtime.txt` - Especifica Python 3.11.7
- `railway.toml` - Configurações do Railway
- `requirements.txt` - Dependências Python

### 2. Deploy
1. Acesse [Railway.app](https://railway.app)
2. Conecte seu repositório GitHub
3. Configure as variáveis de ambiente
4. Deploy automático!

### 3. Configuração Pós-Deploy
```env
WEBHOOK_URL=https://seu-app.railway.app
```

## 🎮 Comandos Disponíveis

### 👥 **Comandos Públicos**
- `/start` - Inicia o bot e registra usuário
- `/help` - Exibe ajuda e comandos disponíveis

### 🔐 **Comandos Administrativos**
- `/stats` - Estatísticas detalhadas do bot
- `/mensagens` - Menu de mensagens predefinidas
- `/morning` - Envia mensagem matinal
- `/alert` - Envia alerta de oportunidade
- `/motivacional` - Envia mensagem motivacional
- `/set_meeting` - Agenda reunião
- `/test_meeting` - Testa notificação de reunião

## 🎯 Funcionalidades

### 📨 **Sistema de Mensagens**

#### Mensagem de Boas-vindas
- Enviada automaticamente para novos membros
- Apresenta o grupo e suas regras
- Direciona para canais específicos

#### Mensagens Matinais (8:00 AM)
- Enviadas automaticamente todos os dias
- Motivação para o dia de trading
- Lembretes importantes

#### Alertas de Oportunidade
- Notificações de oportunidades de mercado
- Enviadas via comando administrativo
- Formatação destacada

### 📅 **Sistema de Reuniões**

#### Agendamento
```
/set_meeting 25/01/2024 20:00 Análise Semanal do Mercado
```

#### Notificações Automáticas
- 1 hora antes da reunião
- 15 minutos antes da reunião
- Lembrete no momento da reunião

### 📊 **Sistema de Estatísticas**

#### Métricas Disponíveis
- Total de usuários registrados
- Novos usuários hoje
- Total de mensagens processadas
- Última atualização

### 🗄️ **Banco de Dados**

#### Tabelas
- **users**: Registro de usuários
- **messages**: Log de mensagens
- **meetings**: Reuniões agendadas

## 📁 Estrutura do Projeto

```
bot-auge-traders/
├── bot.py                 # Arquivo principal do bot
├── requirements.txt       # Dependências Python
├── runtime.txt           # Versão Python para Railway
├── railway.toml          # Configurações Railway
├── .env.example          # Exemplo de variáveis de ambiente
├── .gitignore           # Arquivos ignorados pelo Git
├── README.md            # Documentação (este arquivo)
└── bot_data.db          # Banco SQLite (criado automaticamente)
```

### 🏗️ **Arquitetura do Código**

#### Classes Principais
- `DatabaseManager`: Gerenciamento do banco SQLite
- `MessagesManager`: Mensagens predefinidas
- Handlers de comandos e eventos
- Sistema de jobs automáticos

## 🔒 Segurança

### 🛡️ **Medidas Implementadas**
- Verificação de permissões administrativas
- Validação de IDs de usuários e grupos
- Logs de auditoria para ações administrativas
- Tratamento seguro de erros

### 🔐 **Boas Práticas**
- Nunca commitar tokens ou senhas
- Usar variáveis de ambiente
- Logs sem informações sensíveis
- Validação de entrada de dados

## 🚀 Extensões Futuras

### 📈 **Funcionalidades Planejadas**
- [ ] Sistema de enquetes automáticas
- [ ] Integração com APIs de cotações
- [ ] Dashboard web para administração
- [ ] Sistema de backup automático
- [ ] Integração com Google Analytics

### 🔧 **Melhorias Técnicas**
- [ ] Migração para PostgreSQL
- [ ] Sistema de cache Redis
- [ ] API REST para integração externa
- [ ] Containerização com Docker
- [ ] Sistema de filas assíncronas

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Para suporte e dúvidas:
- 📧 Email: suporte@augetraders.com
- 💬 Telegram: @AugeSupport
- 🐛 Issues: [GitHub Issues](https://github.com/seu-usuario/bot-auge-traders/issues)

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

**Desenvolvido com ❤️ pela equipe Auge Traders**

*Última atualização: Janeiro 2024 | Versão: 1.0.0*