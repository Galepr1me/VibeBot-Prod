"""
VibeBot - Modular Discord Bot
Main entry point using SOLID architecture
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import threading
from flask import Flask

# Import our modular components
from src.database.setup import db_setup
from src.database.connection import db_manager
from src.card_game.card_library import CardLibrary
from src.card_game.card_manager import card_manager
from src.card_game.pack_system import pack_system

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Initialize components
card_library = CardLibrary()

# Configuration functions
def get_config(key):
    """Get configuration value"""
    try:
        result = db_manager.fetch_one('SELECT value FROM config WHERE key = ?', (key,))
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting config {key}: {e}")
        return None

def set_config(key, value):
    """Set configuration value"""
    try:
        if db_manager.db_type == 'postgresql':
            db_manager.execute_query('INSERT INTO config (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value', (key, value))
        else:
            db_manager.execute_query('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', (key, value))
        return True
    except Exception as e:
        print(f"Error setting config {key}: {e}")
        return False

# User management functions
def get_user_data(user_id):
    """Get user data with automatic creation"""
    try:
        result = db_manager.fetch_one('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if not result:
            db_manager.execute_query('INSERT INTO users (user_id) VALUES (?)', (user_id,))
            result = (user_id, 0, 1, None, 0, None, None)
        return result
    except Exception as e:
        print(f"Error getting user data: {e}")
        return (user_id, 0, 1, None, 0, None, None)

def calculate_level_from_xp(total_xp):
    """Calculate level based on progressive XP requirements"""
    base_xp = int(get_config('level_multiplier') or '100')
    scaling_factor = float(get_config('level_scaling_factor') or '1.2')
    level = 1
    xp_needed = 0
    
    while total_xp >= xp_needed:
        level_xp_requirement = int(base_xp * level * (scaling_factor ** (level - 1)))
        xp_needed += level_xp_requirement
        
        if total_xp >= xp_needed:
            level += 1
        else:
            break
    
    return level

def update_user_xp(user_id, xp_gain, username=None, display_name=None):
    """Update user XP and level"""
    try:
        user_data = get_user_data(user_id)
        current_xp = user_data[1]
        current_level = user_data[2]
        total_messages = user_data[4]
        
        new_xp = current_xp + xp_gain
        new_level = calculate_level_from_xp(new_xp)
        
        from datetime import datetime
        now_str = datetime.now().isoformat()
        
        db_manager.execute_query('''UPDATE users SET xp = ?, level = ?, last_message = ?, total_messages = ?, 
                                   username = ?, display_name = ? WHERE user_id = ?''', 
                               (new_xp, new_level, now_str, total_messages + 1, username, display_name, user_id))
        
        return new_level > current_level, new_level
    except Exception as e:
        print(f"Error updating user XP: {e}")
        return False, 1  # Return default level on error

# Bot Events
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # Initialize database
    db_setup.initialize_database()
    
    # Sync slash commands
    try:
        print("🔄 Syncing slash commands...")
        synced = await bot.tree.sync()
        print(f"✅ Successfully synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # XP System
    user_data = get_user_data(message.author.id)
    last_message = user_data[3]
    cooldown = int(get_config('xp_cooldown') or '60')
    
    if last_message:
        try:
            from datetime import datetime, timedelta
            last_time = datetime.fromisoformat(last_message)
            if datetime.now() - last_time < timedelta(seconds=cooldown):
                await bot.process_commands(message)
                return
        except (ValueError, TypeError):
            pass
    
    # Award XP
    xp_gain = int(get_config('xp_per_message') or '15')
    username = message.author.name
    display_name = message.author.display_name
    
    level_up, new_level = update_user_xp(message.author.id, xp_gain, username, display_name)
    
    if level_up:
        level_up_msg = get_config('level_up_message') or 'Congratulations {user}! You reached level {level}!'
        formatted_msg = level_up_msg.format(user=message.author.mention, level=new_level)
        
        xp_channel = get_config('xp_channel')
        if xp_channel and xp_channel != 'None':
            channel = bot.get_channel(int(xp_channel))
            if channel and hasattr(channel, 'send'):
                await channel.send(formatted_msg)
        else:
            await message.channel.send(formatted_msg)
    
    await bot.process_commands(message)

# Slash Commands
@bot.tree.command(name='pack', description='Open a card pack using pack tokens')
async def pack_slash(interaction: discord.Interaction):
    """Open a card pack using pack tokens"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    # Use the modular pack system
    pack_cards = pack_system.open_pack(interaction.user.id)
    
    if pack_cards is None:
        # No tokens available
        user_tokens = pack_system.get_user_pack_tokens(interaction.user.id)
        token_count = user_tokens.get('standard', 0)
        
        embed = discord.Embed(
            title="❌ No Pack Tokens!",
            description=f"You need pack tokens to open packs!\n\n🎫 **Current Tokens:** {token_count}",
            color=0xff0000
        )
        embed.add_field(
            name="How to Get Pack Tokens",
            value="🎁 Use `/daily` to claim daily pack tokens\n⏰ Come back every day for more tokens!",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Get remaining tokens
    remaining_tokens = pack_system.get_user_pack_tokens(interaction.user.id).get('standard', 0)
    
    # Display the pack opening
    embed = discord.Embed(
        title="🎁 Card Pack Opened!", 
        description=f"You used 1 pack token and received {len(pack_cards)} new cards!\n🎫 **Remaining Tokens:** {remaining_tokens}",
        color=0xffd700
    )
    
    for i, card in enumerate(pack_cards, 1):
        element_info = card_library.elements[card['element']]
        rarity_text = card['rarity'].title()
        if card['rarity'] in ['epic', 'legendary', 'mythic']:
            rarity_text = f"**{rarity_text}**"
        
        embed.add_field(
            name=f"Card {i}: {card['name']}", 
            value=f"{element_info['emoji']} {card['element'].title()} • {rarity_text}\n"
                  f"⚔️ {card['attack']} ATK • ❤️ {card['health']} HP • 💎 {card['cost']} Cost",
            inline=False
        )
    
    embed.set_footer(text="Use /cards to view your full collection • Use /daily for more tokens!")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='cards', description='View your card collection')
@app_commands.describe(page='Page number to view (default: 1)')
async def cards_slash(interaction: discord.Interaction, page: int = 1):
    """View your card collection"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    # Use the modular card manager
    collection = card_manager.get_user_collection(interaction.user.id)
    
    if not collection:
        embed = discord.Embed(
            title="🃏 Your Card Collection", 
            description="Your collection is empty! Use `/pack` to get your first cards.",
            color=0x95a5a6
        )
        embed.add_field(
            name="Getting Started", 
            value="🎁 Use `/pack` to open card packs\n🎴 Collect all unique cards\n⚔️ Battles coming soon!",
            inline=False
        )
        await interaction.response.send_message(embed=embed)
        return
    
    # Get collection stats using modular system
    stats = card_manager.get_collection_stats(interaction.user.id)
    
    # Pagination
    cards_per_page = 5
    total_pages = (len(collection) + cards_per_page - 1) // cards_per_page
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * cards_per_page
    end_idx = start_idx + cards_per_page
    page_cards = collection[start_idx:end_idx]
    
    embed = discord.Embed(
        title="🃏 Your Card Collection", 
        description=f"**Page {page}/{total_pages}** • Showing {len(page_cards)} cards",
        color=0x3498db
    )
    
    # Add collection stats
    embed.add_field(
        name="📊 Collection Stats", 
        value=f"📦 **{stats['total_cards']}** total cards\n🎴 **{stats['unique_cards']}** unique cards\n💎 **{stats['rare_cards']}** rare+ cards", 
        inline=True
    )
    
    # Add cards on this page
    for card_data in page_cards:
        card_id, name, element, rarity, attack, health, cost, ability, ascii_art, quantity = card_data
        
        element_info = card_library.elements[element]
        quantity_text = f" x{quantity}" if quantity > 1 else ""
        
        embed.add_field(
            name=f"{name}{quantity_text}", 
            value=f"{element_info['emoji']} {element.title()} • {rarity.title()}\n"
                  f"⚔️ {attack} ATK • ❤️ {health} HP • 💎 {cost} Cost\n"
                  f"🎯 {ability if ability != 'None' else 'No special ability'}",
            inline=False
        )
    
    embed.set_footer(text="Use /pack to get more cards")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='daily', description='Claim your daily pack tokens')
async def daily_slash(interaction: discord.Interaction):
    """Claim daily pack tokens"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    from src.card_game.daily_rewards import DailyRewards
    daily_system = DailyRewards()
    
    reward_result = daily_system.claim_daily_reward(interaction.user.id)
    
    if not reward_result:
        await interaction.response.send_message("❌ Something went wrong with your daily reward. Please try again.", ephemeral=True)
        return
    
    if reward_result['already_claimed']:
        embed = discord.Embed(
            title="🎁 Daily Reward Already Claimed!",
            description=f"You've already claimed your daily reward today!\n\n🔥 **Current Streak:** {reward_result['streak']} days",
            color=0xffa500
        )
        embed.add_field(
            name="⏰ Come Back Tomorrow!",
            value="Your next daily reward will be available in less than 24 hours.",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Display successful reward claim
    rewards = reward_result['rewards']
    streak = reward_result['streak']
    
    embed = discord.Embed(
        title="🎁 Daily Reward Claimed!",
        description=f"🔥 **{streak} Day Streak!**\n\nYou received:",
        color=0x00ff00
    )
    
    pack_tokens = rewards['pack_tokens']
    embed.add_field(
        name="🎁 Reward Received",
        value=f"🎫 **{pack_tokens} Pack Token{'s' if pack_tokens != 1 else ''}**",
        inline=False
    )
    
    embed.add_field(
        name="📊 Streak Stats", 
        value=f"🔥 **Current Streak:** {streak} days\n🏆 **Best Streak:** {reward_result['best_streak']} days",
        inline=False
    )
    
    embed.set_footer(text="Use /cards to view your collection • Come back tomorrow for more rewards!")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='level', description='Check your level or another user\'s level')
@app_commands.describe(user='User to check level for (optional)')
async def level_slash(interaction: discord.Interaction, user: discord.Member | None = None):
    """Check your level or another user's level"""
    target = user if user is not None else interaction.user
    user_data = get_user_data(target.id)
    
    current_level = user_data[2]
    current_xp = user_data[1]
    
    embed = discord.Embed(title=f"{target.display_name}'s Level", color=0x3498db)
    embed.add_field(name="Level", value=current_level, inline=True)
    embed.add_field(name="Total XP", value=f"{current_xp:,}", inline=True)
    embed.add_field(name="Messages", value=user_data[4], inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='help', description='Show all available commands')
async def help_slash(interaction: discord.Interaction):
    """Show all available commands"""
    try:
        embed = discord.Embed(
            title="🤖 VibeBot Commands v1.2.1", 
            description="Your modular Discord bot with card games and XP systems!",
            color=0x00d4ff
        )
        
        # User Commands
        embed.add_field(
            name="🃏 Card Game Commands", 
            value="🔹 `/pack` - Open card packs using tokens\n🔹 `/cards [page]` - View your collection\n🔹 `/daily` - Claim daily pack tokens",
            inline=False
        )
        
        embed.add_field(
            name="📊 XP System Commands", 
            value="🔹 `/level [user]` - Check your or another user's level\n🔹 💬 Chat to gain XP automatically!",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Information Commands", 
            value="🔹 `/help` - Show this help menu",
            inline=False
        )
        
        # Admin Commands (show to admins and specific roles)
        is_admin = False
        
        # Check if user is server owner
        if interaction.guild and interaction.guild.owner_id == interaction.user.id:
            is_admin = True
        
        # Check if user has administrator permissions
        elif hasattr(interaction.user, 'guild_permissions') and interaction.user.guild_permissions.administrator:
            is_admin = True
        
        # Check for specific admin roles (you can customize these role names)
        elif interaction.guild and hasattr(interaction.user, 'roles'):
            admin_role_names = ['Admin', 'Moderator', 'Bot Admin', 'Staff']  # Add your role names here
            user_roles = [role.name for role in interaction.user.roles]
            if any(role in admin_role_names for role in user_roles):
                is_admin = True
        
        if is_admin:
            embed.add_field(
                name="🔧 Admin Commands", 
                value="🔹 `/give_tokens <user> [quantity]` - Give pack tokens to user\n🔹 `/debug_bot` - System diagnostics and troubleshooting",
                inline=False
            )
            embed.set_footer(text="🔐 Admin commands visible to administrators only • Version 1.2.1")
        else:
            embed.set_footer(text="💡 Tip: Use /daily every day for streak bonuses! • Version 1.2.1")
        
        # Check if interaction has already been responded to
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        print(f"Help command error: {e}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Error displaying help menu. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Error displaying help menu. Please try again.", ephemeral=True)
        except:
            pass

# Admin Commands (simplified for now)
@bot.tree.command(name='give_tokens', description='Give pack tokens to a user (Admin only)')
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user='User to give tokens to', quantity='Number of tokens (default: 5)')
async def give_tokens_slash(interaction: discord.Interaction, user: discord.Member, quantity: int = 5):
    """Give pack tokens to a user - Admin only"""
    success = pack_system.add_pack_tokens(user.id, 'standard', quantity)
    
    if success:
        embed = discord.Embed(
            title="✅ Pack Tokens Given",
            description=f"Successfully gave **{quantity}** pack tokens to {user.mention}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Failed to give tokens", ephemeral=True)

@bot.tree.command(name='debug_bot', description='Debug bot status and enable game (Admin only)')
@app_commands.default_permissions(administrator=True)
async def debug_bot_slash(interaction: discord.Interaction):
    """Debug bot status and enable game - Admin only"""
    try:
        # Check game status
        game_enabled = get_config('game_enabled')
        
        # Force enable the game if not enabled
        if game_enabled != 'True':
            set_config('game_enabled', 'True')
            game_enabled = 'True'
        
        # Get some stats
        try:
            user_tokens = pack_system.get_user_pack_tokens(interaction.user.id)
            collection_stats = card_manager.get_collection_stats(interaction.user.id)
        except Exception as e:
            user_tokens = {}
            collection_stats = {'total_cards': 0, 'unique_cards': 0, 'rare_cards': 0}
            print(f"Stats error: {e}")
        
        embed = discord.Embed(
            title="🔧 Bot Debug Status",
            description="Debug information and system status",
            color=0x00ff00
        )
        
        embed.add_field(
            name="🎮 Game Status",
            value=f"**Game Enabled:** {game_enabled}\n**Database Type:** {db_manager.db_type}",
            inline=True
        )
        
        embed.add_field(
            name="🎫 Your Tokens",
            value=f"**Standard Tokens:** {user_tokens.get('standard', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="🃏 Your Collection",
            value=f"**Total Cards:** {collection_stats['total_cards']}\n**Unique Cards:** {collection_stats['unique_cards']}\n**Rare+ Cards:** {collection_stats['rare_cards']}",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Actions Taken",
            value="✅ Game enabled\n✅ Database connection verified\n✅ Modular systems loaded",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Debug Error",
            description=f"Error during debug: {str(e)}",
            color=0xff0000
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)

# Flask web server for cloud hosting
app = Flask(__name__)

@app.route('/')
def home():
    return "VibeBot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "online"}

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Please set the DISCORD_TOKEN environment variable")
    else:
        # Start Flask server in a separate thread for cloud hosting
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        print("Flask server started")
        print("Starting VibeBot with modular architecture...")
        
        try:
            bot.run(token)
        except Exception as e:
            print(f"Bot error: {e}")
            flask_thread.join()
