const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { pool, getGuildSettings, createGuildSettings } = require('../database');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('xp-config')
    .setDescription('Configure XP system settings for this server')
    .addSubcommand(subcommand =>
      subcommand
        .setName('toggle')
        .setDescription('Enable or disable the XP system')
        .addBooleanOption(option =>
          option.setName('enabled')
            .setDescription('Enable or disable XP system')
            .setRequired(true)
        )
    )
    .addSubcommand(subcommand =>
      subcommand
        .setName('rate')
        .setDescription('Set the base XP rate per message')
        .addIntegerOption(option =>
          option.setName('amount')
            .setDescription('Base XP amount (10-50)')
            .setMinValue(10)
            .setMaxValue(50)
            .setRequired(true)
        )
    )
    .addSubcommand(subcommand =>
      subcommand
        .setName('channel')
        .setDescription('Set the level-up notification channel')
        .addChannelOption(option =>
          option.setName('channel')
            .setDescription('Channel for level-up notifications (leave empty to use current channel)')
            .setRequired(false)
        )
    )
    .addSubcommand(subcommand =>
      subcommand
        .setName('view')
        .setDescription('View current XP system settings')
    )
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild),
  
  cooldown: 5,
  
  async execute(interaction) {
    const guildId = interaction.guild.id;
    const subcommand = interaction.options.getSubcommand();
    
    // Get or create guild settings
    let guildSettings = await getGuildSettings(guildId);
    if (!guildSettings) {
      guildSettings = await createGuildSettings(guildId);
    }
    
    try {
      switch (subcommand) {
        case 'toggle':
          const enabled = interaction.options.getBoolean('enabled');
          
          await pool.query(
            'UPDATE guild_settings SET xp_enabled = $1, updated_at = CURRENT_TIMESTAMP WHERE guild_id = $2',
            [enabled, guildId]
          );
          
          const toggleEmbed = {
            color: enabled ? 0x57f287 : 0xff6b6b,
            title: '⚙️ XP System Updated',
            description: `XP system has been **${enabled ? 'enabled' : 'disabled'}** for this server.`,
            timestamp: new Date().toISOString(),
            footer: {
              text: `Updated by ${interaction.user.username}`,
              icon_url: interaction.user.displayAvatarURL({ dynamic: true })
            }
          };
          
          await interaction.reply({ embeds: [toggleEmbed] });
          break;
          
        case 'rate':
          const rate = interaction.options.getInteger('amount');
          
          await pool.query(
            'UPDATE guild_settings SET xp_rate = $1, updated_at = CURRENT_TIMESTAMP WHERE guild_id = $2',
            [rate, guildId]
          );
          
          const rateEmbed = {
            color: 0x5865f2,
            title: '📊 XP Rate Updated',
            description: `Base XP rate has been set to **${rate} XP** per message.\n\n*Note: Users will receive ${rate}-${rate + 15} XP per message (randomized)*`,
            timestamp: new Date().toISOString(),
            footer: {
              text: `Updated by ${interaction.user.username}`,
              icon_url: interaction.user.displayAvatarURL({ dynamic: true })
            }
          };
          
          await interaction.reply({ embeds: [rateEmbed] });
          break;
          
        case 'channel':
          const channel = interaction.options.getChannel('channel');
          const channelId = channel ? channel.id : null;
          
          await pool.query(
            'UPDATE guild_settings SET level_up_channel = $1, updated_at = CURRENT_TIMESTAMP WHERE guild_id = $2',
            [channelId, guildId]
          );
          
          const channelEmbed = {
            color: 0x5865f2,
            title: '📢 Level-up Channel Updated',
            description: channelId 
              ? `Level-up notifications will now be sent to ${channel}.`
              : 'Level-up notifications will now be sent in the same channel where users level up.',
            timestamp: new Date().toISOString(),
            footer: {
              text: `Updated by ${interaction.user.username}`,
              icon_url: interaction.user.displayAvatarURL({ dynamic: true })
            }
          };
          
          await interaction.reply({ embeds: [channelEmbed] });
          break;
          
        case 'view':
          // Refresh settings
          guildSettings = await getGuildSettings(guildId);
          
          const levelUpChannel = guildSettings.level_up_channel 
            ? `<#${guildSettings.level_up_channel}>`
            : 'Same channel as level-up';
          
          const viewEmbed = {
            color: 0x5865f2,
            title: '⚙️ Current XP Settings',
            fields: [
              {
                name: '🔄 XP System Status',
                value: guildSettings.xp_enabled ? '✅ Enabled' : '❌ Disabled',
                inline: true
              },
              {
                name: '📊 Base XP Rate',
                value: `${guildSettings.xp_rate || 15} XP per message`,
                inline: true
              },
              {
                name: '📢 Level-up Channel',
                value: levelUpChannel,
                inline: true
              },
              {
                name: '⏱️ XP Cooldown',
                value: '60 seconds',
                inline: true
              },
              {
                name: '📈 Level Formula',
                value: '100 × level^1.5',
                inline: true
              },
              {
                name: '🎲 XP Range',
                value: `${guildSettings.xp_rate || 15}-${(guildSettings.xp_rate || 15) + 15} XP`,
                inline: true
              }
            ],
            timestamp: new Date().toISOString(),
            footer: {
              text: `Requested by ${interaction.user.username}`,
              icon_url: interaction.user.displayAvatarURL({ dynamic: true })
            }
          };
          
          await interaction.reply({ embeds: [viewEmbed] });
          break;
      }
    } catch (error) {
      console.error('Error updating guild settings:', error);
      await interaction.reply({
        content: '❌ An error occurred while updating the settings. Please try again.',
        ephemeral: true
      });
    }
  }
};
