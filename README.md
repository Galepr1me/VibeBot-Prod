# VibeBot - Modular Discord Bot

A feature-rich Discord bot with XP systems, trading card games, and modular architecture following SOLID principles.

## 🚀 Quick Start (Idiot-Proof Setup)

### Prerequisites
- Python 3.8 or higher
- Discord Developer Account
- (Optional) PostgreSQL database for cloud hosting

### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd VibeBot

# Install dependencies
pip install -r requirements.txt
```

### 2. Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to "Bot" section and click "Add Bot"
4. Copy the bot token (keep it secret!)
5. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent (optional, for better username caching)

### 3. Bot Permissions
When inviting your bot, use this permissions calculator:
- **Required Permissions:**
  - Send Messages
  - Use Slash Commands
  - Embed Links
  - Read Message History
  - Add Reactions
- **Admin Permissions (for full features):**
  - Administrator (recommended for ease of use)

### 4. Environment Setup

#### Option A: Local Development (SQLite)
Create a `.env` file in the root directory:
```env
DISCORD_TOKEN=your_bot_token_here
# DATABASE_URL is optional for local development
```

#### Option B: Cloud Hosting (PostgreSQL)
Create a `.env` file with both tokens:
```env
DISCORD_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://username:password@host:port/database
```

### 5. Run the Bot
```bash
# For development
python bot.py

# For production (with auto-restart)
python -u bot.py
```

## 🏗️ Project Structure (SOLID Architecture)

```
VibeBot/
├── src/                          # Main source code
│   ├── __init__.py
│   ├── database/                 # Database layer (Single Responsibility)
│   │   ├── __init__.py
│   │   ├── connection.py         # Database connection management
│   │   ├── models.py             # Data models and schemas
│   │   └── setup.py              # Database initialization and migrations
│   ├── card_game/                # Card game module (Open/Closed Principle)
│   │   ├── __init__.py
│   │   ├── card_library.py       # Card definitions and game rules
│   │   ├── card_manager.py       # Card collection management
│   │   ├── pack_system.py        # Pack opening and token system
│   │   └── daily_rewards.py      # Daily reward system
│   ├── commands/                 # Command handlers (Interface Segregation)
│   │   ├── __init__.py
│   │   ├── admin_commands.py     # Admin-only commands
│   │   ├── card_commands.py      # Card game commands
│   │   ├── xp_commands.py        # XP and leveling commands
│   │   └── utility_commands.py   # General utility commands
│   ├── services/                 # Business logic services (Dependency Inversion)
│   │   ├── __init__.py
│   │   ├── xp_service.py         # XP calculation and management
│   │   ├── user_service.py       # User data management
│   │   └── config_service.py     # Configuration management
│   └── utils/                    # Utility functions and helpers
│       ├── __init__.py
│       ├── formatters.py         # Message and embed formatting
│       ├── validators.py         # Input validation
│       └── constants.py          # Application constants
├── bot.py                        # Main bot entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🎮 Features

### 🔥 Core Features
- **XP System**: Automatic XP gain from chatting with progressive leveling
- **Trading Card Game**: 64+ unique cards with ASCII art and abilities
- **Daily Rewards**: Pack tokens and streak bonuses
- **Admin Controls**: Comprehensive bot configuration without code changes

### 🃏 Card Game Features
- **6 Elements**: Fire, Water, Earth, Air, Light, Dark with rock-paper-scissors mechanics
- **5 Rarities**: Common (60%), Rare (25%), Epic (10%), Legendary (4%), Mythic (1%)
- **Pack Token System**: Earn tokens through daily rewards, spend to open packs
- **Collection Management**: View, search, and organize your card collection

### ⚙️ Admin Features
- **Configuration System**: Change XP rates, messages, and game settings
- **User Management**: Give tokens, cards, and manage user data
- **Database Tools**: Wipe data, check status, and debug issues
- **Real-time Statistics**: Server activity and engagement metrics

## 📋 Commands Reference

### 🎯 User Commands
| Command | Description |
|---------|-------------|
| `/help` | Show all available commands and game guide |
| `/level [user]` | Check your or another user's XP and level |
| `/leaderboard [limit]` | Show top XP earners (default: 10) |
| `/cards [page]` | View your card collection |
| `/pack` | Open a card pack (requires pack tokens) |
| `/daily` | Claim daily pack tokens and rewards |
| `/view <card_name>` | View a specific card in ASCII art |
| `/stats` | Show server bot statistics |

### 🔧 Admin Commands
| Command | Description |
|---------|-------------|
| `/config action:list` | View all bot configuration settings |
| `/config action:get key:<key>` | Get a specific configuration value |
| `/config action:set key:<key> value:<value>` | Change a configuration setting |
| `/give_tokens user:<@user> quantity:<number>` | Give pack tokens to a user |
| `/give_cards user:<@user> card_name:<name> quantity:<number>` | Give specific cards |
| `/check_tokens user:<@user>` | Check a user's pack tokens and collection |
| `/wipe_cards` | Wipe all user card data (with confirmation) |
| `/debug_cards` | Debug card system issues |
| `/status` | Show detailed bot and database status |

## 🔧 Configuration Options

Key configuration settings you can modify with `/config`:

| Setting | Description | Default |
|---------|-------------|---------|
| `xp_per_message` | XP gained per message | 15 |
| `xp_cooldown` | Cooldown between XP gains (seconds) | 60 |
| `level_multiplier` | Base XP required for leveling | 100 |
| `level_scaling_factor` | How much harder each level gets | 1.2 |
| `game_enabled` | Enable/disable card game | True |
| `welcome_message` | Message for new members | Welcome to the server, {user}! |
| `level_up_message` | Message when users level up | Congratulations {user}! You reached level {level}! |

## 🗄️ Database Support

### SQLite (Local Development)
- Automatic setup, no configuration needed
- Perfect for testing and development
- Data stored in `bot_data.db` file

### PostgreSQL (Production)
- Supports cloud hosting (Render, Railway, Heroku, etc.)
- Automatic connection with `DATABASE_URL` environment variable
- Includes connection pooling and error handling
- Falls back to SQLite if PostgreSQL fails

## 🚀 Deployment

### Local Development
```bash
python bot.py
```

### Cloud Hosting (Render/Railway/Heroku)
1. Set environment variables:
   - `DISCORD_TOKEN`: Your bot token
   - `DATABASE_URL`: PostgreSQL connection string (optional)
2. Deploy with `python bot.py` as the start command
3. Bot will automatically detect cloud environment and configure accordingly

## 🔍 Troubleshooting

### Common Issues

**Bot doesn't respond to commands:**
- Check bot permissions in Discord server
- Ensure bot token is correct in `.env` file
- Verify bot is online in Discord Developer Portal

**Database errors:**
- For PostgreSQL: Check `DATABASE_URL` format
- For SQLite: Ensure write permissions in bot directory
- Use `/status` command to check database connection

**Card system not working:**
- Use `/debug_cards` to identify issues
- Check if cards are populated in database
- Verify pack token system with `/check_tokens`

**Slash commands not appearing:**
- Bot needs `applications.commands` scope when invited
- Commands sync automatically on startup
- Re-invite bot with proper permissions if needed

### Debug Commands
- `/status` - Complete system health check
- `/debug_cards` - Card system diagnostics
- `/config action:list` - View all settings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Follow the modular architecture patterns
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs via GitHub Issues
- **Discord**: Use `/reportbug` command in your server
- **Documentation**: Check this README and inline code comments

---

**Made with ❤️ for Discord communities**

*VibeBot - Bringing engagement and fun to your Discord server!*
