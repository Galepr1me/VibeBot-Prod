const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('kick')
    .setDescription('Kick a user from the server')
    .addUserOption(option =>
      option.setName('user')
        .setDescription('The user to kick')
        .setRequired(true)
    )
    .addStringOption(option =>
      option.setName('reason')
        .setDescription('Reason for the kick')
        .setRequired(false)
    )
    .setDefaultMemberPermissions(PermissionFlagsBits.KickMembers),
  
  cooldown: 5,
  
  async execute(interaction) {
    const targetUser = interaction.options.getUser('user');
    const reason = interaction.options.getString('reason') || 'No reason provided';
    
    // Get the member object
    const targetMember = await interaction.guild.members.fetch(targetUser.id).catch(() => null);
    
    if (!targetMember) {
      return interaction.reply({
        content: '❌ User not found in this server!',
        ephemeral: true
      });
    }
    
    // Check if user is trying to kick themselves
    if (targetUser.id === interaction.user.id) {
      return interaction.reply({
        content: '❌ You cannot kick yourself!',
        ephemeral: true
      });
    }
    
    // Check if user is trying to kick the bot
    if (targetUser.id === interaction.client.user.id) {
      return interaction.reply({
        content: '❌ I cannot kick myself!',
        ephemeral: true
      });
    }
    
    // Check if target is server owner
    if (targetUser.id === interaction.guild.ownerId) {
      return interaction.reply({
        content: '❌ You cannot kick the server owner!',
        ephemeral: true
      });
    }
    
    // Check role hierarchy
    if (targetMember.roles.highest.position >= interaction.member.roles.highest.position) {
      return interaction.reply({
        content: '❌ You cannot kick someone with a higher or equal role!',
        ephemeral: true
      });
    }
    
    // Check if bot can kick the user
    if (!targetMember.kickable) {
      return interaction.reply({
        content: '❌ I cannot kick this user! They may have a higher role than me.',
        ephemeral: true
      });
    }
    
    try {
      // Try to DM the user before kicking
      try {
        const dmEmbed = {
          color: 0xff6b6b,
          title: '👢 You have been kicked',
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
        console.log(`Could not DM ${targetUser.username} about kick`);
      }
      
      // Kick the user
      await targetMember.kick(reason);
      
      // Log the action (you could save this to database)
      console.log(`${interaction.user.username} kicked ${targetUser.username} from ${interaction.guild.name}. Reason: ${reason}`);
      
      // Send confirmation
      const successEmbed = {
        color: 0x57f287,
        title: '✅ User Kicked Successfully',
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
          }
        ],
        timestamp: new Date().toISOString(),
        footer: {
          text: `Kicked by ${interaction.user.username}`,
          icon_url: interaction.user.displayAvatarURL({ dynamic: true })
        }
      };
      
      await interaction.reply({ embeds: [successEmbed] });
      
    } catch (error) {
      console.error('Error kicking user:', error);
      await interaction.reply({
        content: '❌ An error occurred while trying to kick the user.',
        ephemeral: true
      });
    }
  }
};
