# VibeBot - Discord Community Bot

A feature-rich Discord bot with XP levelling system and comprehensive admin controls, designed for community servers.

## 🚀 Features

### 📊 XP & Leveling System
- **Automatic XP tracking** - Users earn XP by chatting (with spam protection)
- **Scaling level system** - Progressive XP requirements for higher levels
- **Level-up notifications** - Automatic announcements with customizable channels
- **Leaderboards** - Server-wide XP rankings
- **User profiles** - Check your own or others' levels and progress

### 🔨 Moderation Tools
- **Kick & Ban commands** - Full moderation control with reason logging
- **Permission-based access** - Commands respect Discord's permission system
- **Role hierarchy protection** - Prevents abuse of moderation commands
- **DM notifications** - Users receive notifications about moderation actions

### 🛠️ Utility Commands
- **Ping command** - Check bot latency and status
- **Help system** - Comprehensive command documentation
- **Error handling** - Robust error management and user feedback

## 🏗️ Tech Stack

- **Node.js** - Runtime environment
- **Discord.js v14** - Discord API wrapper
- **PostgreSQL** - Database (Neon.Tech)
- **Render** - Cloud hosting platform

## 📋 Prerequisites

Before setting up the bot, you'll need:

1. **Node.js 18+** installed on your system
2. **Discord Application** created at [Discord Developer Portal](https://discord.com/developers/applications)
3. **Neon.Tech PostgreSQL database** (or any PostgreSQL database)
4. **Render account** for hosting (optional, for production)

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Galepr1me/VibeBot-Prod.git
cd VibeBot-Prod
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Fill in your environment variables in `.env`:
```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
CLIENT_ID=your_discord_application_client_id_here

# Database Configuration (Neon.Tech PostgreSQL)
DATABASE_URL=postgresql://username:password@hostname:port/database_name

# Bot Configuration
PREFIX=/
NODE_ENV=production
```

### 4. Database Setup

The bot will automatically create the necessary tables when it starts. The database schema includes:
- `users` - XP and level tracking
- `guild_settings` - Server-specific configurations
- `mod_logs` - Moderation action logging

### 5. Deploy Slash Commands

Before running the bot, deploy the slash commands to Discord:

```bash
node deploy-commands.js
```

### 6. Run the Bot

For development:
```bash
npm run dev
```

For production:
```bash
npm start
```

## 🌐 Deployment on Render

### 1. Create a New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository

### 2. Configure Build Settings

- **Build Command**: `npm install`
- **Start Command**: `npm start`
- **Node Version**: 18 or higher

### 3. Environment Variables

Add the following environment variables in Render:
- `DISCORD_TOKEN`
- `CLIENT_ID`
- `DATABASE_URL`
- `NODE_ENV=production`

### 4. Deploy

Render will automatically deploy your bot. The first deployment may take a few minutes.

## 📚 Commands

### XP & Leveling
- `/level [user]` - Check level and XP stats
- `/leaderboard [limit]` - View server XP leaderboard

### Moderation (Requires Permissions)
- `/kick <user> [reason]` - Kick a user from the server
- `/ban <user> [reason] [delete_days]` - Ban a user from the server

### Utility
- `/ping` - Check bot latency and status
- `/help` - Show all available commands

## 🔧 Configuration

### XP System Settings
- **XP Rate**: 15 base XP per message (configurable)
- **Cooldown**: 60 seconds between XP gains
- **Level Formula**: `100 * level^1.5` XP required per level

### Database Schema

The bot uses three main tables:

#### Users Table
```sql
- user_id (VARCHAR) - Discord user ID
- guild_id (VARCHAR) - Discord server ID
- username (VARCHAR) - User's display name
- xp (INTEGER) - Total XP earned
- level (INTEGER) - Current level
- total_messages (INTEGER) - Message count
- timestamps for tracking
```

#### Guild Settings Table
```sql
- guild_id (VARCHAR) - Discord server ID
- xp_enabled (BOOLEAN) - XP system toggle
- xp_rate (INTEGER) - XP per message
- level_up_channel (VARCHAR) - Channel for level notifications
- admin/mod roles configuration
```

## 🛡️ Security Features

- **Permission validation** - All moderation commands check Discord permissions
- **Role hierarchy respect** - Users can't moderate higher-ranked members
- **Input sanitization** - All user inputs are properly validated
- **Error handling** - Comprehensive error management prevents crashes

## 🔄 Auto-Updates

The bot is configured for easy updates:
1. Push changes to your GitHub repository
2. Render automatically redeploys the updated code
3. Database migrations run automatically if needed

## 📊 Monitoring

The bot includes comprehensive logging:
- **Console logs** for all major events
- **Error tracking** with detailed stack traces
- **Moderation logs** stored in database
- **Performance metrics** via ping command

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:
1. Check the console logs for error messages
2. Verify your environment variables are correct
3. Ensure the bot has proper permissions in your Discord server
4. Check that your database is accessible

## 🔮 Future Features

Planned enhancements:
- **Role rewards** - Automatic role assignment based on levels
- **Custom XP multipliers** - Per-channel XP rate configuration
- **Advanced moderation** - Temporary bans, mute system
- **Statistics dashboard** - Web interface for server stats
- **Custom commands** - User-defined command system

---

**Made with ❤️ for Discord communities**
