const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('ban')
    .setDescription('Ban a user from the server')
    .addUserOption(option =>
      option.setName('user')
        .setDescription('The user to ban')
        .setRequired(true)
    )
    .addStringOption(option =>
      option.setName('reason')
        .setDescription('Reason for the ban')
        .setRequired(false)
    )
    .addIntegerOption(option =>
      option.setName('delete_days')
        .setDescription('Number of days of messages to delete (0-7, default: 0)')
        .setMinValue(0)
        .setMaxValue(7)
        .setRequired(false)
    )
    .setDefaultMemberPermissions(PermissionFlagsBits.BanMembers),
  
  cooldown: 5,
  
  async execute(interaction) {
    const targetUser = interaction.options.getUser('user');
    const reason = interaction.options.getString('reason') || 'No reason provided';
    const deleteDays = interaction.options.getInteger('delete_days') || 0;
    
    // Check if user is trying to ban themselves
    if (targetUser.id === interaction.user.id) {
      return interaction.reply({
        content: '❌ You cannot ban yourself!',
        ephemeral: true
      });
    }
    
    // Check if user is trying to ban the bot
    if (targetUser.id === interaction.client.user.id) {
      return interaction.reply({
        content: '❌ I cannot ban myself!',
        ephemeral: true
      });
    }
    
    // Check if target is server owner
    if (targetUser.id === interaction.guild.ownerId) {
      return interaction.reply({
        content: '❌ You cannot ban the server owner!',
        ephemeral: true
      });
    }
    
    // Get the member object (might not exist if user already left)
    const targetMember = await interaction.guild.members.fetch(targetUser.id).catch(() => null);
    
    if (targetMember) {
      // Check role hierarchy
      if (targetMember.roles.highest.position >= interaction.member.roles.highest.position) {
        return interaction.reply({
          content: '❌ You cannot ban someone with a higher or equal role!',
          ephemeral: true
        });
      }
      
      // Check if bot can ban the user
      if (!targetMember.bannable) {
        return interaction.reply({
          content: '❌ I cannot ban this user! They may have a higher role than me.',
          ephemeral: true
        });
      }
    }
    
    // Check if user is already banned
    try {
      const existingBan = await interaction.guild.bans.fetch(targetUser.id);
      if (existingBan) {
        return interaction.reply({
          content: '❌ This user is already banned!',
          ephemeral: true
        });
      }
    } catch (error) {
      // User is not banned, continue
    }
    
    try {
      // Try to DM the user before banning (only if they're still in the server)
      if (targetMember) {
        try {
          const dmEmbed = {
            color: 0xff0000,
            title: '🔨 You have been banned',
            fields: [
              {
                name: '🏠 Server',
                value: interaction.guild.name,
                inline: true
              },
              {
                name: '👮 Moderator',
                value: interaction.user.username,
                inline: true
              },
              {
                name: '📝 Reason',
                value: reason,
                inline: false
              }
            ],
            timestamp: new Date().toISOString()
          };
          
          await targetUser.send({ embeds: [dmEmbed] });
        } catch (error) {
          // User has DMs disabled or blocked the bot
          console.log(`Could not DM ${targetUser.username} about ban`);
        }
      }
      
      // Ban the user
      await interaction.guild.members.ban(targetUser, {
        reason: reason,
        deleteMessageDays: deleteDays
      });
      
      // Log the action
      console.log(`${interaction.user.username} banned ${targetUser.username} from ${interaction.guild.name}. Reason: ${reason}`);
      
      // Send confirmation
      const successEmbed = {
        color: 0xff0000,
        title: '🔨 User Banned Successfully',
        fields: [
          {
            name: '👤 User',
            value: `${targetUser.username} (${targetUser.id})`,
            inline: true
          },
          {
            name: '👮 Moderator',
            value: interaction.user.username,
            inline: true
          },
          {
            name: '📝 Reason',
            value: reason,
            inline: false
          },
          {
            name: '🗑️ Messages Deleted',
            value: deleteDays > 0 ? `${deleteDays} day(s)` : 'None',
            inline: true
          }
        ],
        timestamp: new Date().toISOString(),
        footer: {
          text: `Banned by ${interaction.user.username}`,
          icon_url: interaction.user.displayAvatarURL({ dynamic: true })
        }
      };
      
      await interaction.reply({ embeds: [successEmbed] });
      
    } catch (error) {
      console.error('Error banning user:', error);
      await interaction.reply({
        content: '❌ An error occurred while trying to ban the user.',
        ephemeral: true
      });
    }
  }
};
