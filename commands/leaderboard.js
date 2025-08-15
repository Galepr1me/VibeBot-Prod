const { SlashCommandBuilder } = require('discord.js');
const { getLeaderboard } = require('../database');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('leaderboard')
    .setDescription('Shows the XP leaderboard for this server')
    .addIntegerOption(option =>
      option.setName('limit')
        .setDescription('Number of users to show (1-25, default: 10)')
        .setMinValue(1)
        .setMaxValue(25)
        .setRequired(false)
    ),
  
  cooldown: 10,
  
  async execute(interaction) {
    const limit = interaction.options.getInteger('limit') || 10;
    const guildId = interaction.guild.id;
    
    await interaction.deferReply();
    
    try {
      const leaderboard = await getLeaderboard(guildId, limit);
      
      if (leaderboard.length === 0) {
        return interaction.editReply({
          content: '📊 No users found in the leaderboard yet! Start chatting to earn XP!'
        });
      }
      
      // Create leaderboard description
      let description = '';
      const medals = ['🥇', '🥈', '🥉'];
      
      for (let i = 0; i < leaderboard.length; i++) {
        const user = leaderboard[i];
        const position = i + 1;
        const medal = medals[i] || `**${position}.**`;
        
        description += `${medal} **${user.username}**\n`;
        description += `   Level ${user.level} • ${user.xp.toLocaleString()} XP\n\n`;
      }
      
      const embed = {
        color: 0xffd700,
        title: `🏆 ${interaction.guild.name} Leaderboard`,
        description: description,
        thumbnail: {
          url: interaction.guild.iconURL({ dynamic: true }) || null
        },
        fields: [
          {
            name: '📈 Stats',
            value: `Showing top **${leaderboard.length}** users`,
            inline: true
          },
          {
            name: '💡 Tip',
            value: 'Keep chatting to climb the ranks!',
            inline: true
          }
        ],
        timestamp: new Date().toISOString(),
        footer: {
          text: `Requested by ${interaction.user.username}`,
          icon_url: interaction.user.displayAvatarURL({ dynamic: true })
        }
      };
      
      await interaction.editReply({ embeds: [embed] });
      
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
      await interaction.editReply({
        content: '❌ An error occurred while fetching the leaderboard. Please try again later.'
      });
    }
  }
};
