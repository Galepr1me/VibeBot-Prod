const { Client, GatewayIntentBits, Collection, Events, ActivityType } = require('discord.js');
const { initializeDatabase, getUser, createUser, updateUserXP, getGuildSettings, createGuildSettings } = require('./database');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

// Create Discord client with necessary intents
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildModeration
  ]
});

// Create collections for commands and cooldowns
client.commands = new Collection();
client.cooldowns = new Collection();

// Load command files
function loadCommands() {
  const commandsPath = path.join(__dirname, 'commands');
  if (!fs.existsSync(commandsPath)) {
    fs.mkdirSync(commandsPath, { recursive: true });
    console.log('📁 Created commands directory');
    return;
  }

  const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));

  for (const file of commandFiles) {
    const filePath = path.join(commandsPath, file);
    const command = require(filePath);

    if ('data' in command && 'execute' in command) {
      client.commands.set(command.data.name, command);
      console.log(`✅ Loaded command: ${command.data.name}`);
    } else {
      console.log(`⚠️ Command at ${filePath} is missing required "data" or "execute" property.`);
    }
  }
}

// XP system cooldown (prevent spam)
const xpCooldowns = new Collection();

// Bot ready event
client.once(Events.ClientReady, async () => {
  console.log(`🤖 ${client.user.tag} is online!`);
  
  // Set bot activity
  client.user.setActivity('your community grow! 🚀', { type: ActivityType.Watching });

  // Initialize database
  try {
    await initializeDatabase();
    console.log('🗄️ Database connection established');
  } catch (error) {
    console.error('❌ Failed to initialize database:', error);
    process.exit(1);
  }

  // Load commands
  loadCommands();

  console.log('🎉 Bot is fully ready!');
});

// Handle slash command interactions
client.on(Events.InteractionCreate, async interaction => {
  if (!interaction.isChatInputCommand()) return;

  const command = client.commands.get(interaction.commandName);

  if (!command) {
    console.error(`❌ No command matching ${interaction.commandName} was found.`);
    return;
  }

  // Check cooldowns
  const { cooldowns } = client;

  if (!cooldowns.has(command.data.name)) {
    cooldowns.set(command.data.name, new Collection());
  }

  const now = Date.now();
  const timestamps = cooldowns.get(command.data.name);
  const defaultCooldownDuration = 3;
  const cooldownAmount = (command.cooldown ?? defaultCooldownDuration) * 1000;

  if (timestamps.has(interaction.user.id)) {
    const expirationTime = timestamps.get(interaction.user.id) + cooldownAmount;

    if (now < expirationTime) {
      const expiredTimestamp = Math.round(expirationTime / 1000);
      return interaction.reply({
        content: `⏰ Please wait, you are on a cooldown for \`${command.data.name}\`. You can use it again <t:${expiredTimestamp}:R>.`,
        ephemeral: true
      });
    }
  }

  timestamps.set(interaction.user.id, now);
  setTimeout(() => timestamps.delete(interaction.user.id), cooldownAmount);

  // Execute command
  try {
    await command.execute(interaction);
  } catch (error) {
    console.error(`❌ Error executing ${interaction.commandName}:`, error);
    
    const errorMessage = {
      content: '❌ There was an error while executing this command!',
      ephemeral: true
    };

    if (interaction.replied || interaction.deferred) {
      await interaction.followUp(errorMessage);
    } else {
      await interaction.reply(errorMessage);
    }
  }
});

// XP system - handle message events
client.on(Events.MessageCreate, async message => {
  // Ignore bots and system messages
  if (message.author.bot || !message.guild) return;

  // Check if XP is enabled for this guild
  let guildSettings = await getGuildSettings(message.guild.id);
  if (!guildSettings) {
    guildSettings = await createGuildSettings(message.guild.id);
  }

  if (!guildSettings.xp_enabled) return;

  // Check XP cooldown (prevent spam)
  const userId = message.author.id;
  const guildId = message.guild.id;
  const cooldownKey = `${userId}-${guildId}`;

  if (xpCooldowns.has(cooldownKey)) return;

  // Set cooldown (60 seconds)
  xpCooldowns.set(cooldownKey, true);
  setTimeout(() => xpCooldowns.delete(cooldownKey), 60000);

  // Get or create user
  let user = await getUser(userId, guildId);
  if (!user) {
    user = await createUser(userId, guildId, message.author.username);
  }

  // Calculate XP gain (random between 10-25, configurable via guild settings)
  const baseXP = guildSettings.xp_rate || 15;
  const xpGain = Math.floor(Math.random() * (baseXP + 10)) + 10;

  // Update user XP
  const result = await updateUserXP(userId, guildId, xpGain);
  
  if (result && result.leveledUp) {
    // Send level up message
    const levelUpChannel = guildSettings.level_up_channel 
      ? message.guild.channels.cache.get(guildSettings.level_up_channel)
      : message.channel;

    if (levelUpChannel) {
      const levelUpEmbed = {
        color: 0x00ff00,
        title: '🎉 Level Up!',
        description: `Congratulations ${message.author}! You've reached **Level ${result.newLevel}**!`,
        fields: [
          {
            name: '📊 Stats',
            value: `**XP:** ${result.newXP}\n**Level:** ${result.oldLevel} → ${result.newLevel}`,
            inline: true
          }
        ],
        thumbnail: {
          url: message.author.displayAvatarURL({ dynamic: true })
        },
        timestamp: new Date().toISOString()
      };

      try {
        await levelUpChannel.send({ embeds: [levelUpEmbed] });
      } catch (error) {
        console.error('Error sending level up message:', error);
      }
    }
  }
});

// Handle guild join
client.on(Events.GuildCreate, async guild => {
  console.log(`📥 Joined new guild: ${guild.name} (${guild.id})`);
  
  // Create guild settings
  await createGuildSettings(guild.id);
});

// Error handling
client.on(Events.Error, error => {
  console.error('❌ Discord client error:', error);
});

process.on('unhandledRejection', error => {
  console.error('❌ Unhandled promise rejection:', error);
});

process.on('uncaughtException', error => {
  console.error('❌ Uncaught exception:', error);
  process.exit(1);
});

// Login to Discord
client.login(process.env.DISCORD_TOKEN);
