const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { pool, getUser, createUser, calculateLevelFromXP } = require('../database');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('xp-manage')
    .setDescription('Manage user XP and levels (Admin only)')
    .addSubcommand(subcommand =>
      subcommand
        .setName('add')
        .setDescription('Add XP to a user')
        .addUserOption(option =>
          option.setName('user')
            .setDescription('The user to add XP to')
            .setRequired(true)
        )
        .addIntegerOption(option =>
          option.setName('amount')
            .setDescription('Amount of XP to add (1-10000)')
            .setMinValue(1)
            .setMaxValue(10000)
            .setRequired(true)
        )
    )
    .addSubcommand(subcommand =>
      subcommand
        .setName('remove')
        .setDescription('Remove XP from a user')
        .addUserOption(option =>
          option.setName('user')
            .setDescription('The user to remove XP from')
            .setRequired(true)
        )
        .addIntegerOption(option =>
          option.setName('amount')
            .setDescription('Amount of XP to remove (1-10000)')
            .setMinValue(1)
            .setMaxValue(10000)
            .setRequired(true)
        )
    )
    .addSubcommand(subcommand =>
      subcommand
        .setName('set')
        .setDescription('Set a user\'s XP to a specific amount')
        .addUserOption(option =>
          option.setName('user')
            .setDescription('The user to set XP for')
            .setRequired(true)
        )
        .addIntegerOption(option =>
          option.setName('amount')
            .setDescription('XP amount to set (0-100000)')
            .setMinValue(0)
            .setMaxValue(100000)
            .setRequired(true)
        )
    )
    .addSubcommand(subcommand =>
      subcommand
        .setName('reset')
        .setDescription('Reset a user\'s XP and level to 0')
        .addUserOption(option =>
          option.setName('user')
            .setDescription('The user to reset')
            .setRequired(true)
        )
    )
    .addSubcommand(subcommand =>
      subcommand
        .setName('reset-all')
        .setDescription('Reset ALL users\' XP and levels in this server (DANGEROUS!)')
    )
    .setDefaultMemberPermissions(PermissionFlagsBits.Administrator),
  
  cooldown: 3,
  
  async execute(interaction) {
    const guildId = interaction.guild.id;
    const subcommand = interaction.options.getSubcommand();
    
    try {
      switch (subcommand) {
        case 'add':
          const addUser = interaction.options.getUser('user');
          const addAmount = interaction.options.getInteger('amount');
          
          if (addUser.bot) {
            return interaction.reply({
              content: '❌ Cannot modify XP for bots!',
              ephemeral: true
            });
          }
          
          // Get or create user
          let userData = await getUser(addUser.id, guildId);
          if (!userData) {
            userData = await createUser(addUser.id, guildId, addUser.username);
          }
          
          const newXP = userData.xp + addAmount;
          const newLevel = calculateLevelFromXP(newXP);
          
          await pool.query(
            'UPDATE users SET xp = $1, level = $2, updated_at = CURRENT_TIMESTAMP WHERE user_id = $3 AND guild_id = $4',
            [newXP, newLevel, addUser.id, guildId]
          );
          
          const addEmbed = {
            color: 0x57f287,
            title: '➕ XP Added Successfully',
            fields: [
              {
                name: '👤 User',
                value: addUser.username,
                inline: true
              },
              {
                name: '📊 XP Added',
                value: `+${addAmount.toLocaleString()}`,
                inline: true
              },
              {
                name: '⭐ New Total',
                value: `${newXP.toLocaleString()} XP`,
                inline: true
              },
              {
                name: '🏆 Level Change',
                value: userData.level !== newLevel 
                  ? `${userData.level} → ${newLevel}` 
                  : `${newLevel} (no change)`,
                inline: true
              }
            ],
            timestamp: new Date().toISOString(),
            footer: {
              text: `Modified by ${interaction.user.username}`,
              icon_url: interaction.user.displayAvatarURL({ dynamic: true })
            }
          };
          
          await interaction.reply({ embeds: [addEmbed] });
          break;
          
        case 'remove':
          const removeUser = interaction.options.getUser('user');
          const removeAmount = interaction.options.getInteger('amount');
          
          if (removeUser.bot) {
            return interaction.reply({
              content: '❌ Cannot modify XP for bots!',
              ephemeral: true
            });
          }
          
          let removeUserData = await getUser(removeUser.id, guildId);
          if (!removeUserData) {
            return interaction.reply({
              content: '❌ User not found in the database!',
              ephemeral: true
            });
          }
          
          const newRemoveXP = Math.max(0, removeUserData.xp - removeAmount);
          const newRemoveLevel = calculateLevelFromXP(newRemoveXP);
          
          await pool.query(
            'UPDATE users SET xp = $1, level = $2, updated_at = CURRENT_TIMESTAMP WHERE user_id = $3 AND guild_id = $4',
            [newRemoveXP, newRemoveLevel, removeUser.id, guildId]
          );
          
          const removeEmbed = {
            color: 0xff6b6b,
            title: '➖ XP Removed Successfully',
            fields: [
              {
                name: '👤 User',
                value: removeUser.username,
                inline: true
              },
              {
                name: '📊 XP Removed',
                value: `-${removeAmount.toLocaleString()}`,
                inline: true
              },
              {
                name: '⭐ New Total',
                value: `${newRemoveXP.toLocaleString()} XP`,
                inline: true
              },
              {
                name: '🏆 Level Change',
                value: removeUserData.level !== newRemoveLevel 
                  ? `${removeUserData.level} → ${newRemoveLevel}` 
                  : `${newRemoveLevel} (no change)`,
                inline: true
              }
            ],
            timestamp: new Date().toISOString(),
            footer: {
              text: `Modified by ${interaction.user.username}`,
              icon_url: interaction.user.displayAvatarURL({ dynamic: true })
            }
          };
          
          await interaction.reply({ embeds: [removeEmbed] });
          break;
          
        case 'set':
          const setUser = interaction.options.getUser('user');
          const setAmount = interaction.options.getInteger('amount');
          
          if (setUser.bot) {
            return interaction.reply({
              content: '❌ Cannot modify XP for bots!',
              ephemeral: true
            });
          }
          
          // Get or create user
          let setUserData = await getUser(setUser.id, guildId);
          if (!setUserData) {
            setUserData = await createUser(setUser.id, guildId, setUser.username);
          }
          
          const setLevel = calculateLevelFromXP(setAmount);
          
          await pool.query(
            'UPDATE users SET xp = $1, level = $2, updated_at = CURRENT_TIMESTAMP WHERE user_id = $3 AND guild_id = $4',
            [setAmount, setLevel, setUser.id, guildId]
          );
          
          const setEmbed = {
            color: 0x5865f2,
            title: '🎯 XP Set Successfully',
            fields: [
              {
                name: '👤 User',
                value: setUser.username,
                inline: true
              },
              {
                name: '📊 Previous XP',
                value: `${setUserData.xp.toLocaleString()}`,
                inline: true
              },
              {
                name: '⭐ New XP',
                value: `${setAmount.toLocaleString()}`,
                inline: true
              },
              {
                name: '🏆 Level Change',
                value: setUserData.level !== setLevel 
                  ? `${setUserData.level} → ${setLevel}` 
                  : `${setLevel} (no change)`,
                inline: true
              }
            ],
            timestamp: new Date().toISOString(),
            footer: {
              text: `Modified by ${interaction.user.username}`,
              icon_url: interaction.user.displayAvatarURL({ dynamic: true })
            }
          };
          
          await interaction.reply({ embeds: [setEmbed] });
          break;
          
        case 'reset':
          const resetUser = interaction.options.getUser('user');
          
          if (resetUser.bot) {
            return interaction.reply({
              content: '❌ Cannot modify XP for bots!',
              ephemeral: true
            });
          }
          
          let resetUserData = await getUser(resetUser.id, guildId);
          if (!resetUserData) {
            return interaction.reply({
              content: '❌ User not found in the database!',
              ephemeral: true
            });
          }
          
          await pool.query(
            'UPDATE users SET xp = 0, level = 1, updated_at = CURRENT_TIMESTAMP WHERE user_id = $1 AND guild_id = $2',
            [resetUser.id, guildId]
          );
          
          const resetEmbed = {
            color: 0xff9500,
            title: '🔄 User XP Reset',
            description: `${resetUser.username}'s XP and level have been reset to 0.`,
            fields: [
              {
                name: '📊 Previous Stats',
                value: `Level ${resetUserData.level} • ${resetUserData.xp.toLocaleString()} XP`,
                inline: true
              },
              {
                name: '⭐ New Stats',
                value: 'Level 1 • 0 XP',
                inline: true
              }
            ],
            timestamp: new Date().toISOString(),
            footer: {
              text: `Reset by ${interaction.user.username}`,
              icon_url: interaction.user.displayAvatarURL({ dynamic: true })
            }
          };
          
          await interaction.reply({ embeds: [resetEmbed] });
          break;
          
        case 'reset-all':
          // This is a dangerous operation, so we'll ask for confirmation
          const confirmEmbed = {
            color: 0xff0000,
            title: '⚠️ DANGER: Reset All Users',
            description: '**This will reset ALL users\' XP and levels in this server to 0!**\n\nThis action cannot be undone. Are you absolutely sure?',
            fields: [
              {
                name: '🚨 Warning',
                value: 'This will affect every user who has earned XP in this server.',
                inline: false
              }
            ]
          };
          
          const response = await interaction.reply({ 
            embeds: [confirmEmbed], 
            ephemeral: true,
            fetchReply: true
          });
          
          // Add reaction buttons for confirmation
          await response.react('✅');
          await response.react('❌');
          
          const filter = (reaction, user) => {
            return ['✅', '❌'].includes(reaction.emoji.name) && user.id === interaction.user.id;
          };
          
          try {
            const collected = await response.awaitReactions({ filter, max: 1, time: 30000, errors: ['time'] });
            const reaction = collected.first();
            
            if (reaction.emoji.name === '✅') {
              // Perform the reset
              const result = await pool.query(
                'UPDATE users SET xp = 0, level = 1, updated_at = CURRENT_TIMESTAMP WHERE guild_id = $1',
                [guildId]
              );
              
              const successEmbed = {
                color: 0x57f287,
                title: '✅ Server XP Reset Complete',
                description: `Successfully reset XP and levels for **${result.rowCount}** users in this server.`,
                timestamp: new Date().toISOString(),
                footer: {
                  text: `Reset by ${interaction.user.username}`,
                  icon_url: interaction.user.displayAvatarURL({ dynamic: true })
                }
              };
              
              await interaction.followUp({ embeds: [successEmbed], ephemeral: true });
            } else {
              await interaction.followUp({ content: '❌ Server XP reset cancelled.', ephemeral: true });
            }
          } catch (error) {
            await interaction.followUp({ content: '⏰ Confirmation timed out. Server XP reset cancelled.', ephemeral: true });
          }
          break;
      }
    } catch (error) {
      console.error('Error managing XP:', error);
      await interaction.reply({
        content: '❌ An error occurred while managing XP. Please try again.',
        ephemeral: true
      });
    }
  }
};
