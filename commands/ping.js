const { SlashCommandBuilder } = require('discord.js');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('ping')
    .setDescription('Replies with Pong! and shows bot latency'),
  
  cooldown: 5,
  
  async execute(interaction) {
    const sent = await interaction.reply({ 
      content: '🏓 Pinging...', 
      fetchReply: true 
    });
    
    const latency = sent.createdTimestamp - interaction.createdTimestamp;
    const apiLatency = Math.round(interaction.client.ws.ping);
    
    const embed = {
      color: 0x0099ff,
      title: '🏓 Pong!',
      fields: [
        {
          name: '📡 Bot Latency',
          value: `${latency}ms`,
          inline: true
        },
        {
          name: '🌐 API Latency',
          value: `${apiLatency}ms`,
          inline: true
        },
        {
          name: '📊 Status',
          value: latency < 100 ? '🟢 Excellent' : latency < 200 ? '🟡 Good' : '🔴 Poor',
          inline: true
        }
      ],
      timestamp: new Date().toISOString(),
      footer: {
        text: `Requested by ${interaction.user.username}`,
        icon_url: interaction.user.displayAvatarURL({ dynamic: true })
      }
    };
    
    await interaction.editReply({ 
      content: '', 
      embeds: [embed] 
    });
  }
};
