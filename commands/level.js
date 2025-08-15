const { SlashCommandBuilder } = require('discord.js');
const { getUser, createUser, calculateXPForLevel } = require('../database');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('level')
    .setDescription('Check your or another user\'s level and XP')
    .addUserOption(option =>
      option.setName('user')
        .setDescription('The user to check (leave empty for yourself)')
        .setRequired(false)
    ),
  
  cooldown: 5,
  
  async execute(interaction) {
    const targetUser = interaction.options.getUser('user') || interaction.user;
    const guildId = interaction.guild.id;
    
    // Don't allow checking bot levels
    if (targetUser.bot) {
      return interaction.reply({
        content: '🤖 Bots don\'t have levels!',
        ephemeral: true
      });
    }
    
    // Get user data from database
    let userData = await getUser(targetUser.id, guildId);
    
    if (!userData) {
      if (targetUser.id === interaction.user.id) {
        // Create user if checking own stats
        userData = await createUser(targetUser.id, guildId, targetUser.username);
      } else {
        return interaction.reply({
          content: `❌ ${targetUser.username} hasn't earned any XP yet!`,
          ephemeral: true
        });
      }
    }
    
    // Calculate XP needed for next level
    const currentLevelXP = calculateXPForLevel(userData.level);
    const nextLevelXP = calculateXPForLevel(userData.level + 1);
    const xpProgress = userData.xp - currentLevelXP;
    const xpNeeded = nextLevelXP - currentLevelXP;
    const progressPercentage = Math.round((xpProgress / xpNeeded) * 100);
    
    // Create progress bar
    const progressBarLength = 20;
    const filledBars = Math.round((progressPercentage / 100) * progressBarLength);
    const emptyBars = progressBarLength - filledBars;
    const progressBar = '█'.repeat(filledBars) + '░'.repeat(emptyBars);
    
    const embed = {
      color: 0x7289da,
      title: `📊 ${targetUser.username}'s Level Stats`,
      thumbnail: {
        url: targetUser.displayAvatarURL({ dynamic: true })
      },
      fields: [
        {
          name: '🏆 Current Level',
          value: `**${userData.level}**`,
          inline: true
        },
        {
          name: '⭐ Total XP',
          value: `**${userData.xp.toLocaleString()}**`,
          inline: true
        },
        {
          name: '💬 Messages Sent',
          value: `**${userData.total_messages.toLocaleString()}**`,
          inline: true
        },
        {
          name: '📈 Progress to Next Level',
          value: `\`${progressBar}\` ${progressPercentage}%\n**${xpProgress.toLocaleString()}** / **${xpNeeded.toLocaleString()}** XP`,
          inline: false
        }
      ],
      timestamp: new Date().toISOString(),
      footer: {
        text: `Requested by ${interaction.user.username}`,
        icon_url: interaction.user.displayAvatarURL({ dynamic: true })
      }
    };
    
    await interaction.reply({ embeds: [embed] });
  }
};
