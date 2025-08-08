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
from src.card_game.abilities import ability_system
from src.card_game.battle_system import battle_manager
from src.card_game.battle_ui import CardSelectionView, BattleView, ChallengeView

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
    print(f'[BOT_STARTUP] {bot.user} has connected to Discord!')
    
    # Initialize database
    try:
        print("[BOT_STARTUP] Initializing database...")
        db_setup.initialize_database()
        print("[BOT_STARTUP] Database initialization complete")
    except Exception as e:
        print(f"[BOT_STARTUP] Database initialization failed: {e}")
    
    # Sync slash commands
    try:
        print("[BOT_STARTUP] 🔄 Syncing slash commands...")
        synced = await bot.tree.sync()
        print(f"[BOT_STARTUP] ✅ Successfully synced {len(synced)} slash command(s)")
        
        # List the synced commands
        for cmd in synced:
            print(f"[BOT_STARTUP] - Synced command: /{cmd.name}")
            
    except Exception as e:
        print(f"[BOT_STARTUP] ❌ Failed to sync slash commands: {e}")

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

# Card Collection View with Navigation Buttons
class CardCollectionView(discord.ui.View):
    def __init__(self, user_id: int, collection: list, stats: dict):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
        self.collection = collection
        self.stats = stats
        self.current_page = 1
        self.cards_per_page = 3
        self.total_pages = (len(collection) + self.cards_per_page - 1) // self.cards_per_page
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        # Update button states based on current page
        self.first_page.disabled = (self.current_page == 1)
        self.prev_page.disabled = (self.current_page == 1)
        self.next_page.disabled = (self.current_page == self.total_pages)
        self.last_page.disabled = (self.current_page == self.total_pages)
    
    def create_embed(self):
        start_idx = (self.current_page - 1) * self.cards_per_page
        end_idx = start_idx + self.cards_per_page
        page_cards = self.collection[start_idx:end_idx]
        
        embed = discord.Embed(
            title="🃏 Your Card Collection", 
            description=f"**Page {self.current_page}/{self.total_pages}** • Showing {len(page_cards)} of {len(self.collection)} cards",
            color=0x3498db
        )
        
        # Add collection stats
        embed.add_field(
            name="📊 Collection Stats", 
            value=f"📦 **{self.stats['total_cards']}** total cards\n🎴 **{self.stats['unique_cards']}** unique cards\n💎 **{self.stats['rare_cards']}** rare+ cards", 
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
        
        embed.set_footer(text="Use the buttons below to navigate • Use /pack to get more cards")
        return embed
    
    @discord.ui.button(label='⏪', style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only navigate your own collection!", ephemeral=True)
            return
        
        self.current_page = 1
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='◀️', style=discord.ButtonStyle.primary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only navigate your own collection!", ephemeral=True)
            return
        
        self.current_page = max(1, self.current_page - 1)
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='▶️', style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only navigate your own collection!", ephemeral=True)
            return
        
        self.current_page = min(self.total_pages, self.current_page + 1)
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='⏩', style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only navigate your own collection!", ephemeral=True)
            return
        
        self.current_page = self.total_pages
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='🗑️', style=discord.ButtonStyle.danger)
    async def close_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only close your own collection!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🃏 Card Collection Closed",
            description="Collection view has been closed. Use `/cards` to view again.",
            color=0x95a5a6
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

@bot.tree.command(name='cards', description='View your card collection with navigation')
async def cards_slash(interaction: discord.Interaction):
    """View your card collection with navigation buttons"""
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
    
    # Create the view with navigation buttons
    view = CardCollectionView(interaction.user.id, collection, stats)
    embed = view.create_embed()
    
    await interaction.response.send_message(embed=embed, view=view)

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

@bot.tree.command(name='view', description='View a specific card with full details and ASCII art')
@app_commands.describe(card_name='Name of the card to view')
async def view_slash(interaction: discord.Interaction, card_name: str):
    """View a specific card with full details and ASCII art"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    try:
        # Search for the card in the user's collection
        user_collection = card_manager.get_user_collection(interaction.user.id)
        
        # Find the card (case-insensitive search)
        found_card = None
        for card_data in user_collection:
            card_id, name, element, rarity, attack, health, cost, ability, ascii_art, quantity = card_data
            if name.lower() == card_name.lower():
                found_card = card_data
                break
        
        if not found_card:
            # Check if the card exists in the library but user doesn't own it
            all_cards = card_library.get_all_cards()
            library_card = None
            for card in all_cards:
                if card['name'].lower() == card_name.lower():
                    library_card = card
                    break
            
            if library_card:
                embed = discord.Embed(
                    title="❌ Card Not in Collection",
                    description=f"You don't own **{library_card['name']}** yet!\n\nUse `/pack` to open packs and collect this card.",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="❌ Card Not Found",
                    description=f"No card named **{card_name}** exists.\n\nUse `/cards` to see your collection.",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Display the card with full details
        card_id, name, element, rarity, attack, health, cost, ability, ascii_art, quantity = found_card
        
        element_info = card_library.elements[element]
        rarity_info = card_library.rarities[rarity]
        
        # Create embed with card details
        embed = discord.Embed(
            title=f"🃏 {name}",
            description=f"{element_info['emoji']} **{element.title()}** • **{rarity.title()}**",
            color=rarity_info['color']
        )
        
        # Add card stats
        embed.add_field(
            name="⚔️ Combat Stats",
            value=f"**Attack:** {attack}\n**Health:** {health}\n**Cost:** {cost}",
            inline=True
        )
        
        # Add ability
        embed.add_field(
            name="🎯 Ability",
            value=ability if ability != 'None' else 'No special ability',
            inline=True
        )
        
        # Add collection info
        embed.add_field(
            name="📦 Collection",
            value=f"**Owned:** {quantity}x\n**Rarity:** {rarity_info['drop_rate']}% drop rate",
            inline=True
        )
        
        # Add ASCII art if available
        if ascii_art and ascii_art != 'None':
            embed.add_field(
                name="🎨 Card Art",
                value=f"```\n{ascii_art}\n```",
                inline=False
            )
        
        embed.set_footer(text="Use /cards to browse your full collection")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        print(f"View card error: {e}")
        await interaction.response.send_message("❌ Error viewing card. Please try again.", ephemeral=True)

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

@bot.tree.command(name='xp_table', description='View XP requirements for each level')
@app_commands.describe(start_level='Starting level to display (default: 1)', levels='Number of levels to show (default: 20)')
async def xp_table_slash(interaction: discord.Interaction, start_level: int = 1, levels: int = 20):
    """View XP requirements for each level"""
    try:
        # Validate inputs
        start_level = max(1, start_level)
        levels = max(1, min(levels, 50))  # Limit to 50 levels max
        
        base_xp = int(get_config('level_multiplier') or '100')
        scaling_factor = float(get_config('level_scaling_factor') or '1.2')
        
        embed = discord.Embed(
            title="📊 XP Level Requirements",
            description=f"XP needed for levels {start_level} to {start_level + levels - 1}",
            color=0x3498db
        )
        
        # Calculate XP requirements
        xp_table_text = ""
        total_xp = 0
        
        # Calculate total XP up to start_level - 1
        for level in range(1, start_level):
            level_xp_requirement = int(base_xp * level * (scaling_factor ** (level - 1)))
            total_xp += level_xp_requirement
        
        # Display the requested levels
        for level in range(start_level, start_level + levels):
            level_xp_requirement = int(base_xp * level * (scaling_factor ** (level - 1)))
            total_xp += level_xp_requirement
            
            xp_table_text += f"**Level {level}:** {level_xp_requirement:,} XP (Total: {total_xp:,})\n"
        
        embed.add_field(
            name="Level Requirements",
            value=xp_table_text,
            inline=False
        )
        
        embed.add_field(
            name="📈 XP System Info",
            value=f"**Base XP:** {base_xp}\n**Scaling Factor:** {scaling_factor}\n**XP per Message:** {get_config('xp_per_message') or '15'}",
            inline=True
        )
        
        embed.add_field(
            name="💡 Tips",
            value="• XP requirements increase exponentially\n• Chat regularly to level up faster\n• Use `/level` to check your progress",
            inline=True
        )
        
        embed.set_footer(text="💬 Keep chatting to earn XP and level up!")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        print(f"XP table error: {e}")
        await interaction.response.send_message("❌ Error displaying XP table. Please try again.", ephemeral=True)

# Leaderboard View with Navigation Buttons
class LeaderboardView(discord.ui.View):
    def __init__(self, top_users: list):
        super().__init__(timeout=300)  # 5 minute timeout
        self.top_users = top_users
        self.current_page = 1
        self.users_per_page = 10
        self.total_pages = (len(top_users) + self.users_per_page - 1) // self.users_per_page
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        # Update button states based on current page
        self.first_page.disabled = (self.current_page == 1)
        self.prev_page.disabled = (self.current_page == 1)
        self.next_page.disabled = (self.current_page == self.total_pages)
        self.last_page.disabled = (self.current_page == self.total_pages)
    
    def create_embed(self):
        start_idx = (self.current_page - 1) * self.users_per_page
        end_idx = start_idx + self.users_per_page
        page_users = self.top_users[start_idx:end_idx]
        
        embed = discord.Embed(
            title="🏆 XP Leaderboard",
            description=f"**Page {self.current_page}/{self.total_pages}** • Top {len(self.top_users)} users",
            color=0xffd700
        )
        
        leaderboard_text = ""
        for i, user_data in enumerate(page_users, start=start_idx + 1):
            user_id, xp, level, username, display_name, total_messages = user_data
            
            # Try to get the user from Discord
            try:
                discord_user = bot.get_user(user_id)
                if discord_user:
                    user_name = discord_user.display_name
                elif display_name:
                    user_name = display_name
                elif username:
                    user_name = username
                else:
                    user_name = f"User {user_id}"
            except:
                user_name = display_name or username or f"User {user_id}"
            
            # Add medal emojis for top 3
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"**{i}.**"
            
            leaderboard_text += f"{medal} **{user_name}**\n"
            leaderboard_text += f"    📊 Level {level} • {xp:,} XP • {total_messages} messages\n\n"
        
        embed.add_field(
            name="Rankings",
            value=leaderboard_text,
            inline=False
        )
        
        embed.set_footer(text=f"💬 Chat to gain XP and climb the leaderboard! • Page {self.current_page}/{self.total_pages}")
        return embed
    
    @discord.ui.button(label='⏪', style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 1
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='◀️', style=discord.ButtonStyle.primary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(1, self.current_page - 1)
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='▶️', style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.total_pages, self.current_page + 1)
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='⏩', style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.total_pages
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='🗑️', style=discord.ButtonStyle.danger)
    async def close_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏆 Leaderboard Closed",
            description="Leaderboard view has been closed. Use `/leaderboard` to view again.",
            color=0x95a5a6
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

@bot.tree.command(name='leaderboard', description='View the XP leaderboard with navigation')
async def leaderboard_slash(interaction: discord.Interaction):
    """View the XP leaderboard with navigation buttons"""
    try:
        # Get top users by XP
        top_users = db_manager.fetch_all('''SELECT user_id, xp, level, username, display_name, total_messages 
                                           FROM users 
                                           WHERE xp > 0 
                                           ORDER BY xp DESC 
                                           LIMIT 50''')
        
        if not top_users:
            embed = discord.Embed(
                title="🏆 XP Leaderboard",
                description="No users found with XP yet! Start chatting to gain XP!",
                color=0x95a5a6
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Create the view with navigation buttons
        view = LeaderboardView(top_users)
        embed = view.create_embed()
        
        await interaction.response.send_message(embed=embed, view=view)
        
    except Exception as e:
        print(f"Leaderboard error: {e}")
        await interaction.response.send_message("❌ Error loading leaderboard. Please try again.", ephemeral=True)

@bot.tree.command(name='help', description='Show all available commands')
async def help_slash(interaction: discord.Interaction):
    """Show all available commands"""
    try:
        embed = discord.Embed(
            title="🤖 VibeBot Commands v1.2.22", 
            description="Your modular Discord bot with card games and interactive battles!",
            color=0x00d4ff
        )
        
        # User Commands
        embed.add_field(
            name="🃏 Card Game Commands", 
            value="🔹 `/pack` - Open card packs using tokens\n🔹 `/cards` - View your collection with navigation\n🔹 `/view <card_name>` - View a specific card with ASCII art\n🔹 `/daily` - Claim daily pack tokens",
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Battle System Commands", 
            value="🔹 `/challenge @user` - Challenge another player to battle\n🔹 `/battle_select` - Interactive card selection for battles\n🔹 `/battle_attack` - Attack during your turn (or use buttons!)\n🔹 `/battle_status` - View detailed battle information\n🔹 `/battle_forfeit` - Surrender your current battle",
            inline=False
        )
        
        embed.add_field(
            name="📊 XP System Commands", 
            value="🔹 `/level [user]` - Check your or another user's level\n🔹 `/leaderboard` - View the XP leaderboard with navigation\n🔹 `/xp_table [start] [levels]` - View XP requirements for levels\n🔹 💬 Chat to gain XP automatically!",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Information Commands", 
            value="🔹 `/help` - Show this help menu",
            inline=False
        )
        
        # Check if user has Staff role (admin access)
        is_staff = False
        if interaction.guild and hasattr(interaction.user, 'roles'):
            user_roles = [role.name for role in interaction.user.roles]
            if 'Staff' in user_roles:
                is_staff = True
        
        # Server owner always has access
        if interaction.guild and interaction.guild.owner_id == interaction.user.id:
            is_staff = True
        
        if is_staff:
            embed.add_field(
                name="🔧 Bot Management Commands", 
                value="🔹 `/give_tokens <user> [quantity]` - Give pack tokens to user\n🔹 `/wipe_user <user>` - Wipe user's card data\n🔹 `/set_config <key> <value>` - Configure bot settings",
                inline=False
            )
            embed.add_field(
                name="🛠️ System Commands", 
                value="🔹 `/debug_bot` - System diagnostics and troubleshooting\n🔹 `/bot_stats` - View bot statistics\n🔹 `/reload_cards` - Reload card library\n🔹 `/list_config` - View all configuration settings",
                inline=False
            )
            embed.set_footer(text="🔐 Staff commands visible to Staff role only • Version 1.2.22")
        else:
            embed.set_footer(text="💡 Tip: Use interactive buttons for battles! • Version 1.2.22")
        
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
    print(f"[GIVE_TOKENS] Command called! User: {user.id}, Quantity: {quantity}")
    
    # Respond immediately to avoid Discord timeout
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Ensure user exists in database first
        print(f"[GIVE_TOKENS] Creating user data for {user.id}")
        get_user_data(user.id)
        
        # Use the modular pack system
        print(f"[GIVE_TOKENS] Calling pack_system.add_pack_tokens({user.id}, 'standard', {quantity})")
        success = pack_system.add_pack_tokens(user.id, 'standard', quantity)
        print(f"[GIVE_TOKENS] pack_system.add_pack_tokens returned: {success}")
        
        if success:
            # Get current token count
            user_tokens = pack_system.get_user_pack_tokens(user.id)
            current_tokens = user_tokens.get('standard', 0)
            print(f"[GIVE_TOKENS] Current tokens after adding: {current_tokens}")
            
            embed = discord.Embed(
                title="✅ Pack Tokens Given",
                description=f"Successfully gave **{quantity}** pack tokens to {user.mention}",
                color=0x00ff00
            )
            embed.add_field(
                name="📊 Token Status",
                value=f"🎫 **Current Tokens:** {current_tokens}\n✅ **Added:** {quantity} tokens",
                inline=False
            )
            await interaction.followup.send(embed=embed)
        else:
            print(f"[GIVE_TOKENS] pack_system.add_pack_tokens returned False - checking why")
            await interaction.followup.send("❌ Failed to give tokens. Check Render logs for details.", ephemeral=True)
            
    except Exception as e:
        error_msg = f"❌ Error giving tokens: {str(e)}"
        print(f"[GIVE_TOKENS] Exception: {e}")
        await interaction.followup.send(error_msg, ephemeral=True)

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

@bot.tree.command(name='wipe_user', description='Wipe a user\'s card data (Staff only)')
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user='User whose data to wipe')
async def wipe_user_slash(interaction: discord.Interaction, user: discord.Member):
    """Wipe a user's card data - Staff only"""
    try:
        # Wipe user's cards and pack tokens
        card_success = card_manager.wipe_user_collection(user.id)
        pack_success = pack_system.wipe_user_pack_tokens(user.id)
        
        if card_success and pack_success:
            embed = discord.Embed(
                title="✅ User Data Wiped",
                description=f"Successfully wiped all card data for {user.mention}\n\n🗑️ **Removed:**\n• All cards from collection\n• All pack tokens\n• Daily reward streak",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Failed to wipe user data", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error wiping user data: {str(e)}", ephemeral=True)

@bot.tree.command(name='set_config', description='Configure bot settings (Staff only)')
@app_commands.default_permissions(administrator=True)
@app_commands.describe(key='Configuration key', value='Configuration value')
async def set_config_slash(interaction: discord.Interaction, key: str, value: str):
    """Set bot configuration - Staff only"""
    try:
        success = set_config(key, value)
        
        if success:
            embed = discord.Embed(
                title="✅ Configuration Updated",
                description=f"Successfully updated configuration",
                color=0x00ff00
            )
            embed.add_field(name="Key", value=f"`{key}`", inline=True)
            embed.add_field(name="Value", value=f"`{value}`", inline=True)
            embed.add_field(name="Status", value="✅ Applied", inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Failed to update configuration", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error updating config: {str(e)}", ephemeral=True)

@bot.tree.command(name='bot_stats', description='View bot statistics (Staff only)')
@app_commands.default_permissions(administrator=True)
async def bot_stats_slash(interaction: discord.Interaction):
    """View bot statistics - Staff only"""
    try:
        # Get pack system stats
        pack_stats = pack_system.get_pack_system_stats()
        
        # Get user count
        user_count_result = db_manager.fetch_one('SELECT COUNT(*) FROM users')
        user_count = user_count_result[0] if user_count_result else 0
        
        # Get total XP
        total_xp_result = db_manager.fetch_one('SELECT SUM(xp) FROM users')
        total_xp = total_xp_result[0] if total_xp_result and total_xp_result[0] else 0
        
        embed = discord.Embed(
            title="📊 Bot Statistics",
            description="Comprehensive bot usage statistics",
            color=0x3498db
        )
        
        embed.add_field(
            name="👥 User Statistics",
            value=f"**Total Users:** {user_count:,}\n**Total XP Earned:** {total_xp:,}\n**Users with Tokens:** {pack_stats.get('users_with_tokens', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="🎫 Pack System",
            value=f"**Tokens in Circulation:** {pack_stats.get('total_tokens_in_circulation', 0)}\n**Estimated Packs Opened:** {pack_stats.get('estimated_packs_opened', 0)}\n**Total Cards Collected:** {pack_stats.get('total_cards_collected', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Game Statistics",
            value=f"**Cards in Library:** {pack_stats.get('cards_in_library', 0)}\n**Database Type:** {db_manager.db_type}\n**Game Status:** {get_config('game_enabled')}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(f"❌ Error getting bot stats: {str(e)}", ephemeral=True)

@bot.tree.command(name='reload_cards', description='Reload card library (Staff only)')
@app_commands.default_permissions(administrator=True)
async def reload_cards_slash(interaction: discord.Interaction):
    """Reload card library - Staff only"""
    try:
        # Reinitialize card library
        global card_library
        card_library = CardLibrary()
        
        # Get card count
        total_cards = len(card_library.get_all_cards())
        
        embed = discord.Embed(
            title="🔄 Card Library Reloaded",
            description=f"Successfully reloaded the card library",
            color=0x00ff00
        )
        embed.add_field(name="Total Cards", value=f"{total_cards} cards loaded", inline=True)
        embed.add_field(name="Status", value="✅ Ready", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(f"❌ Error reloading cards: {str(e)}", ephemeral=True)

@bot.tree.command(name='list_config', description='List all configuration keys and values (Staff only)')
@app_commands.default_permissions(administrator=True)
async def list_config_slash(interaction: discord.Interaction):
    """List all configuration keys and values - Staff only"""
    try:
        # Get all config values
        all_config = db_manager.fetch_all('SELECT key, value FROM config ORDER BY key')
        
        embed = discord.Embed(
            title="⚙️ Bot Configuration",
            description="All available configuration keys and their current values",
            color=0x3498db
        )
        
        if not all_config:
            embed.add_field(
                name="No Configuration Found",
                value="No configuration keys are currently set.",
                inline=False
            )
        else:
            # Group configs by category
            xp_configs = []
            game_configs = []
            message_configs = []
            other_configs = []
            
            for key, value in all_config:
                config_line = f"**{key}:** `{value}`"
                
                if 'xp' in key.lower() or 'level' in key.lower():
                    xp_configs.append(config_line)
                elif 'game' in key.lower() or 'quest' in key.lower() or 'event' in key.lower():
                    game_configs.append(config_line)
                elif 'message' in key.lower() or 'welcome' in key.lower():
                    message_configs.append(config_line)
                else:
                    other_configs.append(config_line)
            
            if xp_configs:
                embed.add_field(
                    name="📊 XP System Settings",
                    value="\n".join(xp_configs),
                    inline=False
                )
            
            if game_configs:
                embed.add_field(
                    name="🎮 Game Settings",
                    value="\n".join(game_configs),
                    inline=False
                )
            
            if message_configs:
                embed.add_field(
                    name="💬 Message Settings",
                    value="\n".join(message_configs),
                    inline=False
                )
            
            if other_configs:
                embed.add_field(
                    name="🔧 Other Settings",
                    value="\n".join(other_configs),
                    inline=False
                )
        
        embed.add_field(
            name="📝 Usage",
            value="Use `/set_config <key> <value>` to modify any setting\nExample: `/set_config xp_per_message 20`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(f"❌ Error listing config: {str(e)}", ephemeral=True)

@bot.tree.command(name='test_ability', description='Test a card ability (Staff only)')
@app_commands.default_permissions(administrator=True)
@app_commands.describe(card_name='Name of the card to test ability for')
async def test_ability_slash(interaction: discord.Interaction, card_name: str):
    """Test a card ability - Staff only"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    try:
        # Find the card in the library
        card = card_library.get_card_by_name(card_name)
        if not card:
            embed = discord.Embed(
                title="❌ Card Not Found",
                description=f"No card named **{card_name}** exists in the library.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get the ability
        ability_text = card['ability']
        if ability_text == 'None' or not ability_text:
            embed = discord.Embed(
                title="❌ No Ability",
                description=f"**{card['name']}** has no special ability to test.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create mock card data for testing
        caster_data = {
            'card_id': 1,
            'name': card['name'],
            'attack': card['attack'],
            'health': card['health'],
            'element': card['element']
        }
        
        target_data = {
            'card_id': 2,
            'name': 'Test Target',
            'attack': 3,
            'health': 3,
            'element': 'fire'
        }
        
        # Test the ability
        print(f"[TEST_ABILITY] Testing ability: {ability_text}")
        result = ability_system.execute_ability(ability_text, caster_data, target_data)
        print(f"[TEST_ABILITY] Result: {result}")
        
        # Create response embed
        embed = discord.Embed(
            title=f"🧪 Ability Test: {card['name']}",
            description=f"Testing ability: **{ability_text}**",
            color=0x00ff00 if result['success'] else 0xff0000
        )
        
        # Add card info
        element_info = card_library.elements[card['element']]
        embed.add_field(
            name="🃏 Card Info",
            value=f"{element_info['emoji']} **{card['name']}**\n⚔️ {card['attack']} ATK • ❤️ {card['health']} HP • 💎 {card['cost']} Cost",
            inline=True
        )
        
        # Add ability details
        if result['success']:
            ability_effect = ability_system.get_ability_effect(ability_text)
            embed.add_field(
                name="✨ Ability Details",
                value=f"**Type:** {ability_effect.effect_type}\n**Value:** {ability_effect.value}\n**Target:** {ability_effect.target}\n**Trigger:** {ability_effect.condition}",
                inline=True
            )
            
            # Add execution result
            execution_result = result['result']
            if execution_result.get('applied', False):
                result_text = execution_result.get('message', 'Effect applied successfully')
                embed.add_field(
                    name="🎯 Test Result",
                    value=f"✅ **Success!**\n{result_text}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎯 Test Result",
                    value=f"❌ **Failed**\n{execution_result.get('message', 'Unknown error')}",
                    inline=False
                )
        else:
            embed.add_field(
                name="❌ Error",
                value=result['message'],
                inline=False
            )
        
        embed.set_footer(text="This is a test execution - no actual game effects applied")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"Test ability error: {e}")
        await interaction.response.send_message(f"❌ Error testing ability: {str(e)}", ephemeral=True)

@bot.tree.command(name='fix_cards', description='Fix card database issues (Staff only)')
@app_commands.default_permissions(administrator=True)
async def fix_cards_slash(interaction: discord.Interaction):
    """Fix card database issues - Staff only"""
    try:
        await interaction.response.defer(ephemeral=True)
        
        # Check current card count in database
        card_count_result = db_manager.fetch_one('SELECT COUNT(*) FROM cards')
        current_card_count = card_count_result[0] if card_count_result else 0
        
        # Get expected card count from library
        expected_card_count = len(card_library.get_all_cards())
        
        embed = discord.Embed(
            title="🔧 Card Database Diagnostics",
            description="Checking and fixing card database issues...",
            color=0x3498db
        )
        
        embed.add_field(
            name="📊 Current Status",
            value=f"**Cards in Database:** {current_card_count}\n**Cards in Library:** {expected_card_count}\n**Database Type:** {db_manager.db_type}",
            inline=False
        )
        
        # If card counts don't match, repopulate
        if current_card_count != expected_card_count:
            embed.add_field(
                name="🔄 Fixing Database",
                value="Card count mismatch detected. Safely repopulating card database...",
                inline=False
            )
            
            # Safely handle foreign key constraints
            try:
                # First, disable foreign key checks if possible
                if db_manager.db_type == 'postgresql':
                    # For PostgreSQL, we need to be more careful with foreign keys
                    # Instead of deleting, let's add missing cards
                    existing_cards = db_manager.fetch_all('SELECT name FROM cards')
                    existing_card_names = {card[0] for card in existing_cards}
                    
                    # Add any missing cards
                    for card in card_library.get_all_cards():
                        if card['name'] not in existing_card_names:
                            db_manager.execute_query('''INSERT INTO cards (name, element, rarity, attack, health, cost, ability, ascii_art) 
                                                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                                                    (card['name'], card['element'], card['rarity'], card['attack'], 
                                                     card['health'], card['cost'], card['ability'], card['ascii']))
                else:
                    # For SQLite, temporarily disable foreign keys
                    db_manager.execute_query('PRAGMA foreign_keys = OFF')
                    
                    # Clear existing cards and repopulate
                    db_manager.execute_query('DELETE FROM cards')
                    
                    # Repopulate cards
                    for card in card_library.get_all_cards():
                        db_manager.execute_query('''INSERT INTO cards (name, element, rarity, attack, health, cost, ability, ascii_art) 
                                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                                (card['name'], card['element'], card['rarity'], card['attack'], 
                                                 card['health'], card['cost'], card['ability'], card['ascii']))
                    
                    # Re-enable foreign keys
                    db_manager.execute_query('PRAGMA foreign_keys = ON')
                    
            except Exception as fix_error:
                embed.add_field(
                    name="⚠️ Fix Warning",
                    value=f"Could not fully repopulate due to foreign key constraints. Adding missing cards instead.\nError: {str(fix_error)[:100]}...",
                    inline=False
                )
                
                # Fallback: just add missing cards
                existing_cards = db_manager.fetch_all('SELECT name FROM cards')
                existing_card_names = {card[0] for card in existing_cards}
                
                added_count = 0
                for card in card_library.get_all_cards():
                    if card['name'] not in existing_card_names:
                        try:
                            if db_manager.db_type == 'postgresql':
                                db_manager.execute_query('''INSERT INTO cards (name, element, rarity, attack, health, cost, ability, ascii_art) 
                                                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                                                        (card['name'], card['element'], card['rarity'], card['attack'], 
                                                         card['health'], card['cost'], card['ability'], card['ascii']))
                            else:
                                db_manager.execute_query('''INSERT INTO cards (name, element, rarity, attack, health, cost, ability, ascii_art) 
                                                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                                        (card['name'], card['element'], card['rarity'], card['attack'], 
                                                         card['health'], card['cost'], card['ability'], card['ascii']))
                            added_count += 1
                        except Exception as add_error:
                            print(f"Failed to add card {card['name']}: {add_error}")
                
                if added_count > 0:
                    embed.add_field(
                        name="✅ Partial Fix",
                        value=f"Added {added_count} missing cards to database.",
                        inline=False
                    )
            
            # Verify fix
            new_card_count_result = db_manager.fetch_one('SELECT COUNT(*) FROM cards')
            new_card_count = new_card_count_result[0] if new_card_count_result else 0
            
            embed.add_field(
                name="✅ Fix Complete",
                value=f"**New Card Count:** {new_card_count}\n**Status:** {'✅ Fixed' if new_card_count == expected_card_count else '❌ Still Issues'}",
                inline=False
            )
        else:
            embed.add_field(
                name="✅ Database OK",
                value="Card database is properly populated. No fixes needed.",
                inline=False
            )
        
        # Show sample cards
        sample_cards = db_manager.fetch_all('SELECT name, rarity FROM cards ORDER BY rarity DESC, name LIMIT 5')
        if sample_cards:
            sample_text = "\n".join([f"• {name} ({rarity})" for name, rarity in sample_cards])
            embed.add_field(
                name="🃏 Sample Cards in Database",
                value=sample_text,
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Fix Cards Error",
            description=f"Error fixing card database: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed, ephemeral=True)

@bot.tree.command(name='debug_collection', description='Debug user collection issues (Staff only)')
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user='User to debug collection for')
async def debug_collection_slash(interaction: discord.Interaction, user: discord.Member):
    """Debug user collection issues - Staff only"""
    try:
        # Get user's collection from database
        collection = card_manager.get_user_collection(user.id)
        
        # Get user's pack tokens
        tokens = pack_system.get_user_pack_tokens(user.id)
        
        # Get collection stats
        stats = card_manager.get_collection_stats(user.id)
        
        embed = discord.Embed(
            title=f"🔍 Collection Debug: {user.display_name}",
            description="Detailed collection diagnostics",
            color=0x3498db
        )
        
        embed.add_field(
            name="📊 Collection Stats",
            value=f"**Total Cards:** {stats['total_cards']}\n**Unique Cards:** {stats['unique_cards']}\n**Rare+ Cards:** {stats['rare_cards']}",
            inline=True
        )
        
        embed.add_field(
            name="🎫 Pack Tokens",
            value=f"**Standard Tokens:** {tokens.get('standard', 0)}",
            inline=True
        )
        
        # Show recent cards in collection
        if collection:
            recent_cards = collection[:10]  # First 10 cards
            card_list = []
            for card_data in recent_cards:
                card_id, name, element, rarity, attack, health, cost, ability, ascii_art, quantity = card_data
                card_list.append(f"• {name} x{quantity} ({rarity})")
            
            embed.add_field(
                name="🃏 Recent Cards (First 10)",
                value="\n".join(card_list) if card_list else "No cards found",
                inline=False
            )
        else:
            embed.add_field(
                name="🃏 Collection Status",
                value="❌ No cards found in collection",
                inline=False
            )
        
        # Check for database issues
        total_cards_in_db = db_manager.fetch_one('SELECT COUNT(*) FROM cards')[0]
        user_card_entries = db_manager.fetch_one('SELECT COUNT(*) FROM user_cards WHERE user_id = ?', (user.id,))[0]
        
        embed.add_field(
            name="🔧 Database Info",
            value=f"**Total Cards in DB:** {total_cards_in_db}\n**User Card Entries:** {user_card_entries}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Debug Collection Error",
            description=f"Error debugging collection: {str(e)}",
            color=0xff0000
        )
        await interaction.response.send_message(embed=error_embed, ephemeral=True)

@bot.tree.command(name='challenge', description='Challenge another player to a card battle')
@app_commands.describe(opponent='Player to challenge to a battle')
async def challenge_slash(interaction: discord.Interaction, opponent: discord.Member):
    """Challenge another player to a card battle"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    try:
        # Basic validation
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("❌ You cannot challenge yourself to a battle!", ephemeral=True)
            return
        
        if opponent.bot:
            await interaction.response.send_message("❌ You cannot challenge bots to battles!", ephemeral=True)
            return
        
        # Check if either player is already in a battle
        challenger_battle = battle_manager.get_player_active_battle(interaction.user.id)
        opponent_battle = battle_manager.get_player_active_battle(opponent.id)
        
        if challenger_battle:
            await interaction.response.send_message("❌ You are already in an active battle! Finish your current battle first.", ephemeral=True)
            return
        
        if opponent_battle:
            await interaction.response.send_message(f"❌ {opponent.display_name} is already in an active battle!", ephemeral=True)
            return
        
        # Check if both players have cards
        challenger_collection = card_manager.get_user_collection(interaction.user.id)
        opponent_collection = card_manager.get_user_collection(opponent.id)
        
        if not challenger_collection:
            await interaction.response.send_message("❌ You need cards to battle! Use `/pack` to get cards first.", ephemeral=True)
            return
        
        if not opponent_collection:
            await interaction.response.send_message(f"❌ {opponent.display_name} doesn't have any cards yet!", ephemeral=True)
            return
        
        # Create the battle
        battle = battle_manager.create_battle(interaction.user.id, opponent.id)
        
        if not battle:
            await interaction.response.send_message("❌ Failed to create battle. Please try again.", ephemeral=True)
            return
        
        # Create challenge embed with interactive buttons
        embed = discord.Embed(
            title="⚔️ Battle Challenge!",
            description=f"{interaction.user.mention} has challenged {opponent.mention} to a card battle!",
            color=0xff6b35
        )
        
        embed.add_field(
            name="🎮 Battle Info",
            value=f"**Battle ID:** {battle.battle_id}\n**Format:** 1v1 Single Card\n**Status:** Waiting for response",
            inline=True
        )
        
        embed.add_field(
            name="🃏 Your Collections",
            value=f"**{interaction.user.display_name}:** {len(challenger_collection)} cards\n**{opponent.display_name}:** {len(opponent_collection)} cards",
            inline=True
        )
        
        embed.add_field(
            name="📋 Challenge Options",
            value=f"**{opponent.display_name}:** Use the buttons below to respond!\n**{interaction.user.display_name}:** You can cancel if needed.",
            inline=False
        )
        
        embed.set_footer(text="Challenge expires in 5 minutes if no response")
        
        # Create interactive challenge view
        challenge_view = ChallengeView(interaction.user.id, opponent.id, battle.battle_id)
        
        await interaction.response.send_message(embed=embed, view=challenge_view)
        print(f"[CHALLENGE] Battle {battle.battle_id} created: {interaction.user.id} vs {opponent.id}")
        
    except Exception as e:
        print(f"Challenge error: {e}")
        await interaction.response.send_message("❌ Error creating battle challenge. Please try again.", ephemeral=True)

@bot.tree.command(name='battle_select', description='Select a card for your current battle using interactive UI')
async def battle_select_slash(interaction: discord.Interaction):
    """Select a card for your current battle using interactive UI"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    try:
        # Find the player's active battle
        battle = battle_manager.get_player_active_battle(interaction.user.id)
        
        if not battle:
            await interaction.response.send_message("❌ You are not in an active battle! Use `/challenge @user` to start a battle.", ephemeral=True)
            return
        
        # Check if player already selected a card
        player_card = battle.get_player_card(interaction.user.id)
        if player_card:
            await interaction.response.send_message(f"❌ You have already selected **{player_card.name}** for this battle!", ephemeral=True)
            return
        
        # Get user's collection
        user_collection = card_manager.get_user_collection(interaction.user.id)
        
        if not user_collection:
            await interaction.response.send_message("❌ You don't have any cards! Use `/pack` to get cards first.", ephemeral=True)
            return
        
        # Create interactive card selection view
        selection_view = CardSelectionView(interaction.user.id, battle.battle_id, user_collection)
        embed = selection_view.create_selection_embed()
        
        await interaction.response.send_message(embed=embed, view=selection_view, ephemeral=True)
        print(f"[BATTLE_SELECT] Interactive card selection shown for user {interaction.user.id} in battle {battle.battle_id}")
        
    except Exception as e:
        print(f"Battle select error: {e}")
        await interaction.response.send_message("❌ Error showing card selection. Please try again.", ephemeral=True)

@bot.tree.command(name='battle_attack', description='Attack your opponent in the current battle')
async def battle_attack_slash(interaction: discord.Interaction):
    """Attack your opponent in the current battle"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    try:
        # Find the player's active battle
        battle = battle_manager.get_player_active_battle(interaction.user.id)
        
        if not battle:
            await interaction.response.send_message("❌ You are not in an active battle! Use `/challenge @user` to start a battle.", ephemeral=True)
            return
        
        # Check if battle is in progress
        if battle.state.value != 'in_progress':
            await interaction.response.send_message("❌ Battle is not in progress! Both players need to select cards first.", ephemeral=True)
            return
        
        # Check if it's the player's turn
        if not battle.is_player_turn(interaction.user.id):
            current_turn_user = bot.get_user(battle.current_turn)
            turn_name = current_turn_user.display_name if current_turn_user else f"Player {battle.current_turn}"
            await interaction.response.send_message(f"❌ It's not your turn! Waiting for **{turn_name}** to attack.", ephemeral=True)
            return
        
        # Execute the attack
        attack_result = battle.attack(interaction.user.id)
        
        if not attack_result['success']:
            await interaction.response.send_message(f"❌ Attack failed: {attack_result['message']}", ephemeral=True)
            return
        
        # Save battle state
        battle_manager.save_battle(battle)
        
        # Create attack result embed
        embed = discord.Embed(
            title="⚔️ Battle Attack!",
            description=attack_result['message'],
            color=0xff6b35
        )
        
        # Get battle state for display
        battle_state = attack_result['battle_state']
        player1_card = battle_state['player1_card']
        player2_card = battle_state['player2_card']
        
        # Add card status
        if player1_card and player2_card:
            player1_user = bot.get_user(battle.player1_id)
            player2_user = bot.get_user(battle.player2_id)
            
            player1_name = player1_user.display_name if player1_user else f"Player {battle.player1_id}"
            player2_name = player2_user.display_name if player2_user else f"Player {battle.player2_id}"
            
            # Create health bars
            def create_health_bar(current_hp, max_hp, length=10):
                if max_hp <= 0:
                    return "💀 DEFEATED"
                
                percentage = current_hp / max_hp
                filled = int(percentage * length)
                empty = length - filled
                
                bar = "█" * filled + "░" * empty
                return f"{bar} {current_hp}/{max_hp} HP"
            
            embed.add_field(
                name=f"🃏 {player1_name}'s {player1_card['name']}",
                value=f"❤️ {create_health_bar(player1_card['current_health'], player1_card['max_health'])}\n⚔️ {player1_card['current_attack']} ATK",
                inline=True
            )
            
            embed.add_field(
                name=f"🃏 {player2_name}'s {player2_card['name']}",
                value=f"❤️ {create_health_bar(player2_card['current_health'], player2_card['max_health'])}\n⚔️ {player2_card['current_attack']} ATK",
                inline=True
            )
        
        # Check if battle ended
        if attack_result.get('target_defeated', False):
            winner_id = attack_result['winner']
            winner_user = bot.get_user(winner_id)
            winner_name = winner_user.display_name if winner_user else f"Player {winner_id}"
            
            embed.add_field(
                name="🏆 Battle Complete!",
                value=f"**{winner_name}** wins the battle!\n\n🎁 **Rewards:**\n• +50 XP\n• +1 Pack Token",
                inline=False
            )
            
            # Award rewards to winner
            try:
                # Award XP
                update_user_xp(winner_id, 50)
                
                # Award pack token
                pack_system.add_pack_tokens(winner_id, 'standard', 1)
                
                print(f"[BATTLE_ATTACK] Battle {battle.battle_id} completed. Winner: {winner_id}")
            except Exception as reward_error:
                print(f"[BATTLE_ATTACK] Error awarding rewards: {reward_error}")
            
            # Clean up battle
            battle_manager.finish_battle(battle.battle_id)
            
        else:
            # Battle continues
            next_turn_user = bot.get_user(battle.current_turn)
            next_turn_name = next_turn_user.display_name if next_turn_user else f"Player {battle.current_turn}"
            
            embed.add_field(
                name="🎮 Next Turn",
                value=f"**{next_turn_name}**'s turn to attack!\nUse `/battle_attack` when ready.",
                inline=False
            )
        
        embed.set_footer(text=f"Battle ID: {battle.battle_id} • Turn: {battle.turn_number}")
        
        await interaction.response.send_message(embed=embed)
        print(f"[BATTLE_ATTACK] Player {interaction.user.id} attacked in battle {battle.battle_id}")
        
    except Exception as e:
        print(f"Battle attack error: {e}")
        await interaction.response.send_message("❌ Error executing attack. Please try again.", ephemeral=True)

@bot.tree.command(name='battle_status', description='View the current status of your battle')
async def battle_status_slash(interaction: discord.Interaction):
    """View the current status of your battle"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    try:
        # Find the player's active battle
        battle = battle_manager.get_player_active_battle(interaction.user.id)
        
        if not battle:
            await interaction.response.send_message("❌ You are not in an active battle! Use `/challenge @user` to start a battle.", ephemeral=True)
            return
        
        # Get battle state
        battle_state = battle.get_battle_state()
        
        # Create status embed
        embed = discord.Embed(
            title="⚔️ Battle Status",
            description=f"**Battle ID:** {battle.battle_id}\n**Turn:** {battle.turn_number}\n**Phase:** {battle.phase.value.replace('_', ' ').title()}",
            color=0x3498db
        )
        
        # Get player information
        player1_user = bot.get_user(battle.player1_id)
        player2_user = bot.get_user(battle.player2_id)
        
        player1_name = player1_user.display_name if player1_user else f"Player {battle.player1_id}"
        player2_name = player2_user.display_name if player2_user else f"Player {battle.player2_id}"
        
        # Add battle participants
        embed.add_field(
            name="👥 Battle Participants",
            value=f"**Player 1:** {player1_name}\n**Player 2:** {player2_name}",
            inline=True
        )
        
        # Add current turn info
        current_turn_user = bot.get_user(battle.current_turn)
        current_turn_name = current_turn_user.display_name if current_turn_user else f"Player {battle.current_turn}"
        your_turn = "✅ Your Turn!" if battle.current_turn == interaction.user.id else "⏳ Opponent's Turn"
        
        embed.add_field(
            name="🎯 Current Turn",
            value=f"**{current_turn_name}**\n{your_turn}",
            inline=True
        )
        
        # Add battle state
        state_emoji = {
            'card_selection': '🃏',
            'in_progress': '⚔️',
            'finished': '🏆',
            'cancelled': '❌'
        }
        
        embed.add_field(
            name="📊 Battle State",
            value=f"{state_emoji.get(battle.state.value, '❓')} {battle.state.value.replace('_', ' ').title()}",
            inline=True
        )
        
        # Add card information if battle is in progress
        if battle.state.value == 'in_progress' and battle.player1_card and battle.player2_card:
            # Create health bars
            def create_health_bar(current_hp, max_hp, length=10):
                if max_hp <= 0:
                    return "💀 DEFEATED"
                
                percentage = current_hp / max_hp
                filled = int(percentage * length)
                empty = length - filled
                
                bar = "█" * filled + "░" * empty
                return f"{bar} {current_hp}/{max_hp} HP"
            
            # Player 1 card
            p1_card = battle.player1_card
            embed.add_field(
                name=f"🃏 {player1_name}'s {p1_card.name}",
                value=f"❤️ {create_health_bar(p1_card.current_health, p1_card.max_health)}\n⚔️ {p1_card.current_attack} ATK\n🛡️ {p1_card.damage_reduction} Armor\n🎯 {p1_card.ability}",
                inline=False
            )
            
            # Player 2 card
            p2_card = battle.player2_card
            embed.add_field(
                name=f"🃏 {player2_name}'s {p2_card.name}",
                value=f"❤️ {create_health_bar(p2_card.current_health, p2_card.max_health)}\n⚔️ {p2_card.current_attack} ATK\n🛡️ {p2_card.damage_reduction} Armor\n🎯 {p2_card.ability}",
                inline=False
            )
            
            # Add action buttons if it's the player's turn
            if battle.current_turn == interaction.user.id and battle.phase.value == 'attack':
                embed.add_field(
                    name="🎮 Available Actions",
                    value="• `/battle_attack` - Attack your opponent\n• `/battle_forfeit` - Surrender the battle",
                    inline=False
                )
        
        # Add recent battle log
        if battle.battle_log:
            recent_log = battle.battle_log[-3:]  # Last 3 events
            log_text = "\n".join([f"• {event['message']}" for event in recent_log])
            embed.add_field(
                name="📜 Recent Battle Log",
                value=log_text,
                inline=False
            )
        
        embed.set_footer(text=f"Use /battle_attack to attack • Use /battle_forfeit to surrender")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"Battle status error: {e}")
        await interaction.response.send_message("❌ Error getting battle status. Please try again.", ephemeral=True)

@bot.tree.command(name='battle_forfeit', description='Forfeit your current battle')
async def battle_forfeit_slash(interaction: discord.Interaction):
    """Forfeit your current battle"""
    if get_config('game_enabled') != 'True':
        await interaction.response.send_message("The card game is currently disabled.", ephemeral=True)
        return
    
    try:
        # Find the player's active battle
        battle = battle_manager.get_player_active_battle(interaction.user.id)
        
        if not battle:
            await interaction.response.send_message("❌ You are not in an active battle! Use `/challenge @user` to start a battle.", ephemeral=True)
            return
        
        # Get opponent information
        opponent_id = battle.get_opponent_id(interaction.user.id)
        opponent_user = bot.get_user(opponent_id)
        opponent_name = opponent_user.display_name if opponent_user else f"Player {opponent_id}"
        
        # End the battle with opponent as winner
        battle._end_battle(opponent_id)
        battle_manager.save_battle(battle)
        
        # Create forfeit embed
        embed = discord.Embed(
            title="🏳️ Battle Forfeited",
            description=f"You have forfeited the battle against **{opponent_name}**.",
            color=0xff9500
        )
        
        embed.add_field(
            name="🏆 Battle Result",
            value=f"**Winner:** {opponent_name}\n**Result:** Victory by forfeit",
            inline=True
        )
        
        embed.add_field(
            name="🎁 Opponent Rewards",
            value="• +25 XP (forfeit victory)\n• +1 Pack Token",
            inline=True
        )
        
        # Award rewards to opponent
        try:
            # Award XP (less for forfeit victory)
            update_user_xp(opponent_id, 25)
            
            # Award pack token
            pack_system.add_pack_tokens(opponent_id, 'standard', 1)
            
            print(f"[BATTLE_FORFEIT] Battle {battle.battle_id} forfeited by {interaction.user.id}. Winner: {opponent_id}")
        except Exception as reward_error:
            print(f"[BATTLE_FORFEIT] Error awarding rewards: {reward_error}")
        
        # Clean up battle
        battle_manager.finish_battle(battle.battle_id)
        
        embed.add_field(
            name="🎮 What's Next?",
            value="Use `/challenge @user` to start a new battle!\nUse `/cards` to view your collection.",
            inline=False
        )
        
        embed.set_footer(text=f"Battle ID: {battle.battle_id} • Better luck next time!")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        print(f"Battle forfeit error: {e}")
        await interaction.response.send_message("❌ Error forfeiting battle. Please try again.", ephemeral=True)

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
    print(f"[MAIN] Discord token present: {bool(token)}")
    
    if not token:
        print("[MAIN] ❌ Please set the DISCORD_TOKEN environment variable")
    else:
        # Start Flask server in a separate thread for cloud hosting
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        print("[MAIN] Flask server started")
        print("[MAIN] Starting VibeBot with modular architecture...")
        print(f"[MAIN] Bot intents: {bot.intents}")
        print(f"[MAIN] Bot command prefix: {bot.command_prefix}")
        
        try:
            print("[MAIN] Calling bot.run()...")
            bot.run(token)
        except Exception as e:
            print(f"[MAIN] ❌ Bot error: {e}")
            import traceback
            traceback.print_exc()
            flask_thread.join()
