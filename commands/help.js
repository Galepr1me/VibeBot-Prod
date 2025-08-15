const { SlashCommandBuilder } = require('discord.js');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('help')
    .setDescription('Shows all available commands and their descriptions'),
  
  cooldown: 10,
  
  async execute(interaction) {
    const embed = {
      color: 0x5865f2,
      title: '🤖 VibeBot Commands',
      description: 'Here are all the available commands you can use:',
      fields: [
        {
          name: '📊 **XP & Leveling Commands**',
          value: '`/level [user]` - Check your or another user\'s level and XP\n`/leaderboard [limit]` - View the server XP leaderboard',
          inline: false
        },
        {
          name: '🛠️ **Utility Commands**',
          value: '`/ping` - Check bot latency and status\n`/help` - Show this help message',
          inline: false
        },
        {
          name: '🔨 **Moderation Commands**',
          value: '`/kick <user> [reason]` - Kick a user from the server\n`/ban <user> [reason] [delete_days]` - Ban a user from the server',
          inline: false
        },
        {
          name: '⚙️ **Admin Configuration Commands**',
          value: '`/xp-config toggle <enabled>` - Enable/disable XP system\n`/xp-config rate <amount>` - Set base XP rate per message\n`/xp-config channel [channel]` - Set level-up notification channel\n`/xp-config view` - View current XP settings',
          inline: false
        },
        {
          name: '🎛️ **XP Management Commands**',
          value: '`/xp-manage add <user> <amount>` - Add XP to a user\n`/xp-manage remove <user> <amount>` - Remove XP from a user\n`/xp-manage set <user> <amount>` - Set user\'s XP to specific amount\n`/xp-manage reset <user>` - Reset a user\'s XP to 0\n`/xp-manage reset-all` - Reset ALL users\' XP (dangerous!)',
          inline: false
        },
        {
          name: '⚙️ **XP System Info**',
          value: '• Earn XP by chatting in the server\n• XP is gained every 60 seconds to prevent spam\n• Level up notifications are sent automatically\n• XP rates can be configured by admins',
          inline: false
        },
        {
          name: '🔐 **Permissions**',
          value: '• Moderation commands require appropriate Discord permissions\n• XP commands are available to everyone\n• Some commands may be restricted by server settings',
          inline: false
        }
      ],
      thumbnail: {
        url: interaction.client.user.displayAvatarURL({ dynamic: true })
      },
      timestamp: new Date().toISOString(),
      footer: {
        text: `Requested by ${interaction.user.username} • VibeBot v1.0.0`,
        icon_url: interaction.user.displayAvatarURL({ dynamic: true })
      }
    };
    
    await interaction.reply({ embeds: [embed] });
  }
};
