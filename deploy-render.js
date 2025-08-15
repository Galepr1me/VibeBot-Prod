// This script deploys commands and then starts the bot for Render
const { REST, Routes } = require('discord.js');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const commands = [];

// Load all command files
const commandsPath = path.join(__dirname, 'commands');
const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));

for (const file of commandFiles) {
  const filePath = path.join(commandsPath, file);
  const command = require(filePath);
  
  if ('data' in command && 'execute' in command) {
    commands.push(command.data.toJSON());
    console.log(`✅ Loaded command: ${command.data.name}`);
  } else {
    console.log(`⚠️ Command at ${filePath} is missing required "data" or "execute" property.`);
  }
}

// Deploy commands function
async function deployCommands() {
  const rest = new REST().setToken(process.env.DISCORD_TOKEN);

  try {
    console.log(`🚀 Started refreshing ${commands.length} application (/) commands.`);

    const data = await rest.put(
      Routes.applicationCommands(process.env.CLIENT_ID),
      { body: commands },
    );

    console.log(`✅ Successfully reloaded ${data.length} application (/) commands globally.`);
    console.log('🎉 Commands deployed successfully!');
    
    // List deployed commands
    console.log('\n📋 Deployed commands:');
    data.forEach(command => {
      console.log(`   • /${command.name} - ${command.description}`);
    });
    
    return true;
  } catch (error) {
    console.error('❌ Error deploying commands:', error);
    return false;
  }
}

// Deploy commands and start bot
(async () => {
  console.log('🔄 Attempting to deploy slash commands...');
  const deployed = await deployCommands();
  
  if (deployed) {
    console.log('✅ Commands deployed successfully!');
  } else {
    console.warn('⚠️ Command deployment failed, but starting bot anyway...');
    console.warn('💡 You will need to deploy commands manually once CLIENT_ID is fixed.');
  }
  
  console.log('🤖 Starting bot...');
  // Start the main bot regardless of command deployment status
  require('./index.js');
})();
