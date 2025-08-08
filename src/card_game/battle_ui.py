"""
Battle UI Components
Interactive Discord UI for card battles using buttons and views
"""
import discord
from typing import Dict, Any, Optional
from .battle_system import battle_manager
from .card_manager import card_manager
from .card_library import CardLibrary
from .pack_system import pack_system


class ChallengeView(discord.ui.View):
    """Interactive challenge accept/reject interface"""
    
    def __init__(self, challenger_id: int, opponent_id: int, battle_id: int):
        super().__init__(timeout=300)  # 5 minute timeout
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.battle_id = battle_id
        self.challenge_accepted = False
        self.challenge_cancelled = False
    
    @discord.ui.button(label='Accept Challenge', emoji='⚔️', style=discord.ButtonStyle.success)
    async def accept_challenge(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Accept the battle challenge"""
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message("❌ Only the challenged player can accept this challenge!", ephemeral=True)
            return
        
        if self.challenge_accepted or self.challenge_cancelled:
            await interaction.response.send_message("❌ This challenge has already been responded to!", ephemeral=True)
            return
        
        self.challenge_accepted = True
        
        # Get battle and update status
        battle = battle_manager.get_battle(self.battle_id)
        if not battle:
            await interaction.response.send_message("❌ Battle not found!", ephemeral=True)
            return
        
        # Create challenge accepted embed
        challenger_user = interaction.client.get_user(self.challenger_id)
        challenger_name = challenger_user.display_name if challenger_user else f"Player {self.challenger_id}"
        
        embed = discord.Embed(
            title="✅ Challenge Accepted!",
            description=f"{interaction.user.mention} has accepted the battle challenge from **{challenger_name}**!",
            color=0x00ff00
        )
        
        embed.add_field(
            name="🎮 Battle Info",
            value=f"**Battle ID:** {battle.battle_id}\n**Format:** 1v1 Single Card\n**Status:** Ready for card selection",
            inline=True
        )
        
        embed.add_field(
            name="📋 Next Step",
            value="Both players need to select their battle cards!\nUse the **Card Select** buttons below.",
            inline=False
        )
        
        # Create card selection view for both players
        card_select_view = CardSelectionPromptView(self.challenger_id, self.opponent_id, self.battle_id)
        
        # Disable all buttons in this view
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=card_select_view)
        
        print(f"[CHALLENGE] Challenge accepted: Battle {self.battle_id}")
    
    @discord.ui.button(label='Reject Challenge', emoji='❌', style=discord.ButtonStyle.danger)
    async def reject_challenge(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reject the battle challenge"""
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message("❌ Only the challenged player can reject this challenge!", ephemeral=True)
            return
        
        if self.challenge_accepted or self.challenge_cancelled:
            await interaction.response.send_message("❌ This challenge has already been responded to!", ephemeral=True)
            return
        
        self.challenge_cancelled = True
        
        # Get challenger info
        challenger_user = interaction.client.get_user(self.challenger_id)
        challenger_name = challenger_user.display_name if challenger_user else f"Player {self.challenger_id}"
        
        # Cancel the battle
        battle_manager.cancel_battle(self.battle_id)
        
        # Create rejection embed
        embed = discord.Embed(
            title="❌ Challenge Rejected",
            description=f"{interaction.user.mention} has rejected the battle challenge from **{challenger_name}**.",
            color=0xff0000
        )
        
        embed.add_field(
            name="🎮 What's Next?",
            value=f"**{challenger_name}** can challenge other players or try again later.\nUse `/challenge @user` to start a new battle!",
            inline=False
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
        
        print(f"[CHALLENGE] Challenge rejected: Battle {self.battle_id} cancelled")
    
    @discord.ui.button(label='Cancel Challenge', emoji='🚫', style=discord.ButtonStyle.secondary)
    async def cancel_challenge(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the battle challenge (challenger only)"""
        if interaction.user.id != self.challenger_id:
            await interaction.response.send_message("❌ Only the challenger can cancel this challenge!", ephemeral=True)
            return
        
        if self.challenge_accepted or self.challenge_cancelled:
            await interaction.response.send_message("❌ This challenge has already been responded to!", ephemeral=True)
            return
        
        self.challenge_cancelled = True
        
        # Get opponent info
        opponent_user = interaction.client.get_user(self.opponent_id)
        opponent_name = opponent_user.display_name if opponent_user else f"Player {self.opponent_id}"
        
        # Cancel the battle
        battle_manager.cancel_battle(self.battle_id)
        
        # Create cancellation embed
        embed = discord.Embed(
            title="🚫 Challenge Cancelled",
            description=f"{interaction.user.mention} has cancelled their battle challenge to **{opponent_name}**.",
            color=0x95a5a6
        )
        
        embed.add_field(
            name="🎮 What's Next?",
            value="Use `/challenge @user` to start a new battle challenge!",
            inline=False
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
        
        print(f"[CHALLENGE] Challenge cancelled by challenger: Battle {self.battle_id}")


class CardSelectionPromptView(discord.ui.View):
    """Card selection prompt with buttons for both players"""
    
    def __init__(self, player1_id: int, player2_id: int, battle_id: int):
        super().__init__(timeout=600)  # 10 minute timeout
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.battle_id = battle_id
        self.player1_selected = False
        self.player2_selected = False
    
    @discord.ui.button(label='Card Select', emoji='🃏', style=discord.ButtonStyle.primary, custom_id='card_select_p1')
    async def card_select_player1(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Card selection for player 1"""
        if interaction.user.id != self.player1_id:
            await interaction.response.send_message("❌ This card selection is not for you!", ephemeral=True)
            return
        
        await self._handle_card_selection(interaction, self.player1_id)
    
    @discord.ui.button(label='Card Select', emoji='🃏', style=discord.ButtonStyle.primary, custom_id='card_select_p2')
    async def card_select_player2(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Card selection for player 2"""
        if interaction.user.id != self.player2_id:
            await interaction.response.send_message("❌ This card selection is not for you!", ephemeral=True)
            return
        
        await self._handle_card_selection(interaction, self.player2_id)
    
    async def _handle_card_selection(self, interaction: discord.Interaction, user_id: int):
        """Handle card selection for a player"""
        try:
            # Get battle
            battle = battle_manager.get_battle(self.battle_id)
            if not battle:
                await interaction.response.send_message("❌ Battle not found!", ephemeral=True)
                return
            
            # Check if player already selected a card
            player_card = battle.get_player_card(user_id)
            if player_card:
                await interaction.response.send_message(f"❌ You have already selected **{player_card.name}** for this battle!", ephemeral=True)
                return
            
            # Get user's collection
            user_collection = card_manager.get_user_collection(user_id)
            if not user_collection:
                await interaction.response.send_message("❌ You don't have any cards! Use `/pack` to get cards first.", ephemeral=True)
                return
            
            # Create interactive card selection view
            selection_view = CardSelectionView(user_id, self.battle_id, user_collection)
            embed = selection_view.create_selection_embed()
            
            await interaction.response.send_message(embed=embed, view=selection_view, ephemeral=True)
            print(f"[CARD_SELECT] Interactive card selection shown for user {user_id} in battle {self.battle_id}")
            
        except Exception as e:
            print(f"Card selection error: {e}")
            await interaction.response.send_message("❌ Error showing card selection. Please try again.", ephemeral=True)
    
    async def update_selection_status(self, user_id: int):
        """Update the selection status when a player selects a card"""
        if user_id == self.player1_id:
            self.player1_selected = True
        elif user_id == self.player2_id:
            self.player2_selected = True
        
        # Check if both players have selected
        if self.player1_selected and self.player2_selected:
            # Both players selected - battle can begin
            battle = battle_manager.get_battle(self.battle_id)
            if battle and battle.state.value == 'in_progress':
                # Create battle ready message
                embed = discord.Embed(
                    title="⚔️ Battle Ready!",
                    description="Both players have selected their cards! The battle begins now!",
                    color=0xff6b35
                )
                
                # Create battle interface
                battle_view = BattleView(self.battle_id, self.player1_id)
                battle_embed = battle_view.create_battle_embed()
                
                # This would need to be called from the original message context
                # For now, we'll let the individual card selection handle this
                pass


class CardSelectionView(discord.ui.View):
    """Interactive card selection for battles"""
    
    def __init__(self, user_id: int, battle_id: int, collection: list):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
        self.battle_id = battle_id
        self.collection = collection
        self.current_page = 1
        self.cards_per_page = 5
        self.total_pages = (len(collection) + self.cards_per_page - 1) // self.cards_per_page
        
        # Add card selection buttons for current page
        self.update_card_buttons()
        
        # Add navigation buttons if needed
        if self.total_pages > 1:
            self.update_navigation_buttons()
    
    def update_card_buttons(self):
        """Update card selection buttons for current page"""
        # Clear existing card buttons
        for item in self.children[:]:
            if hasattr(item, 'card_data'):
                self.remove_item(item)
        
        # Add card buttons for current page
        start_idx = (self.current_page - 1) * self.cards_per_page
        end_idx = start_idx + self.cards_per_page
        page_cards = self.collection[start_idx:end_idx]
        
        card_library = CardLibrary()
        
        for i, card_data in enumerate(page_cards):
            card_id, name, element, rarity, attack, health, cost, ability, ascii_art, quantity = card_data
            
            # Get element emoji
            element_info = card_library.elements[element]
            
            # Create button
            button = discord.ui.Button(
                label=f"{name}",
                emoji=element_info['emoji'],
                style=discord.ButtonStyle.primary,
                custom_id=f"select_card_{card_id}",
                row=i // 5  # Max 5 buttons per row
            )
            
            # Store card data on button
            button.card_data = card_data
            button.callback = self.card_selected
            
            self.add_item(button)
    
    def update_navigation_buttons(self):
        """Add navigation buttons if multiple pages"""
        if self.total_pages <= 1:
            return
        
        # Previous page button
        prev_button = discord.ui.Button(
            label="◀️ Previous",
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page == 1),
            row=4
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # Next page button
        next_button = discord.ui.Button(
            label="Next ▶️",
            style=discord.ButtonStyle.secondary,
            disabled=(self.current_page == self.total_pages),
            row=4
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
    
    async def card_selected(self, interaction: discord.Interaction):
        """Handle card selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only select cards for your own battle!", ephemeral=True)
            return
        
        # Get the selected card data
        button = None
        for item in self.children:
            if hasattr(item, 'card_data'):
                button = item
                break
        
        if not button:
            await interaction.response.send_message("❌ Error selecting card. Please try again.", ephemeral=True)
            return
        
        card_data = button.card_data
        card_id, name, element, rarity, attack, health, cost, ability, ascii_art, quantity = card_data
        
        # Get battle and add card
        battle = battle_manager.get_battle(self.battle_id)
        if not battle:
            await interaction.response.send_message("❌ Battle not found!", ephemeral=True)
            return
        
        selected_card = {
            'card_id': card_id,
            'name': name,
            'element': element,
            'rarity': rarity,
            'attack': attack,
            'health': health,
            'cost': cost,
            'ability': ability,
            'ascii': ascii_art
        }
        
        success = battle.add_card(self.user_id, selected_card)
        if not success:
            await interaction.response.send_message("❌ Failed to select card for battle. Please try again.", ephemeral=True)
            return
        
        # Save battle state
        battle_manager.save_battle(battle)
        
        # Create response
        card_library = CardLibrary()
        element_info = card_library.elements[element]
        
        embed = discord.Embed(
            title="✅ Card Selected!",
            description=f"You have selected **{name}** for battle!",
            color=0x00ff00
        )
        
        embed.add_field(
            name="🃏 Your Battle Card",
            value=f"{element_info['emoji']} **{name}**\n⚔️ {attack} ATK • ❤️ {health} HP\n🎯 {ability}",
            inline=True
        )
        
        # Check if battle is ready to start
        if battle.state.value == 'in_progress':
            # Both players have selected - battle is ready!
            opponent_id = battle.get_opponent_id(self.user_id)
            opponent_card = battle.get_opponent_card(self.user_id)
            
            # Get player names
            user = interaction.client.get_user(self.user_id)
            opponent_user = interaction.client.get_user(opponent_id)
            user_name = user.display_name if user else f"Player {self.user_id}"
            opponent_name = opponent_user.display_name if opponent_user else f"Player {opponent_id}"
            
            # Create battle ready embed
            embed = discord.Embed(
                title="⚔️ Battle Ready!",
                description=f"Both players have selected their cards! The battle begins now!",
                color=0xff6b35
            )
            
            embed.add_field(
                name="🃏 Battle Matchup",
                value=f"**{user_name}:** {name}\n**{opponent_name}:** {opponent_card.name}",
                inline=True
            )
            
            # Show who goes first
            first_player_user = interaction.client.get_user(battle.current_turn)
            first_player_name = first_player_user.display_name if first_player_user else f"Player {battle.current_turn}"
            
            embed.add_field(
                name="🎯 Turn Order",
                value=f"**{first_player_name}** goes first!\n{'✅ Your turn!' if battle.current_turn == self.user_id else '⏳ Wait for opponent'}",
                inline=True
            )
            
            embed.add_field(
                name="🎮 Battle Instructions",
                value="Use the buttons below to take actions during your turn!\nThe battle interface will update after each action.",
                inline=False
            )
            
            # Create battle interface
            battle_view = BattleView(battle.battle_id, self.user_id)
            
            await interaction.response.edit_message(embed=embed, view=battle_view)
            
            # Also send a notification to the original challenge message
            # This would require storing the original message, for now we'll update this one
            
        else:
            # Only one player has selected - show waiting status
            opponent_id = battle.get_opponent_id(self.user_id)
            opponent_user = interaction.client.get_user(opponent_id)
            opponent_name = opponent_user.display_name if opponent_user else f"Player {opponent_id}"
            
            embed.add_field(
                name="✅ Card Selected!",
                value=f"You selected **{name}** for battle!",
                inline=False
            )
            
            embed.add_field(
                name="⏳ Waiting for Opponent",
                value=f"Waiting for **{opponent_name}** to select their card...\n\n🔔 **{opponent_name}** will be notified to select their card!",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
        
        self.stop()
    
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only navigate your own card selection!", ephemeral=True)
            return
        
        self.current_page = max(1, self.current_page - 1)
        self.clear_items()
        self.update_card_buttons()
        self.update_navigation_buttons()
        
        embed = self.create_selection_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only navigate your own card selection!", ephemeral=True)
            return
        
        self.current_page = min(self.total_pages, self.current_page + 1)
        self.clear_items()
        self.update_card_buttons()
        self.update_navigation_buttons()
        
        embed = self.create_selection_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    def create_selection_embed(self):
        """Create the card selection embed"""
        embed = discord.Embed(
            title="🃏 Select Your Battle Card",
            description=f"Choose a card from your collection for battle!\n**Page {self.current_page}/{self.total_pages}**",
            color=0x3498db
        )
        
        # Show cards on current page
        start_idx = (self.current_page - 1) * self.cards_per_page
        end_idx = start_idx + self.cards_per_page
        page_cards = self.collection[start_idx:end_idx]
        
        card_library = CardLibrary()
        
        for card_data in page_cards:
            card_id, name, element, rarity, attack, health, cost, ability, ascii_art, quantity = card_data
            element_info = card_library.elements[element]
            
            embed.add_field(
                name=f"{element_info['emoji']} {name}",
                value=f"⚔️ {attack} ATK • ❤️ {health} HP • 💎 {cost} Cost\n🎯 {ability}",
                inline=True
            )
        
        embed.set_footer(text="Click a card button below to select it for battle!")
        return embed


class BattleView(discord.ui.View):
    """Interactive battle interface with buttons"""
    
    def __init__(self, battle_id: int, user_id: int):
        super().__init__(timeout=600)  # 10 minute timeout
        self.battle_id = battle_id
        self.user_id = user_id
        
        # Add battle action buttons
        self.add_battle_buttons()
    
    def add_battle_buttons(self):
        """Add battle action buttons"""
        # Attack button
        attack_button = discord.ui.Button(
            label="Attack",
            emoji="⚔️",
            style=discord.ButtonStyle.danger,
            custom_id="battle_attack"
        )
        attack_button.callback = self.attack_button_callback
        self.add_item(attack_button)
        
        # Status button
        status_button = discord.ui.Button(
            label="Status",
            emoji="📊",
            style=discord.ButtonStyle.primary,
            custom_id="battle_status"
        )
        status_button.callback = self.status_button_callback
        self.add_item(status_button)
        
        # Forfeit button
        forfeit_button = discord.ui.Button(
            label="Forfeit",
            emoji="🏳️",
            style=discord.ButtonStyle.secondary,
            custom_id="battle_forfeit"
        )
        forfeit_button.callback = self.forfeit_button_callback
        self.add_item(forfeit_button)
        
        # Refresh button
        refresh_button = discord.ui.Button(
            label="Refresh",
            emoji="🔄",
            style=discord.ButtonStyle.secondary,
            custom_id="battle_refresh"
        )
        refresh_button.callback = self.refresh_button_callback
        self.add_item(refresh_button)
    
    async def attack_button_callback(self, interaction: discord.Interaction):
        """Handle attack button press"""
        battle = battle_manager.get_battle(self.battle_id)
        if not battle:
            await interaction.response.send_message("❌ Battle not found!", ephemeral=True)
            return
        
        # Check if it's the player's turn
        if not battle.is_player_turn(interaction.user.id):
            current_turn_user = interaction.client.get_user(battle.current_turn)
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
        
        # Update the battle interface
        if attack_result.get('target_defeated', False):
            # Battle ended
            winner_id = attack_result['winner']
            winner_user = interaction.client.get_user(winner_id)
            winner_name = winner_user.display_name if winner_user else f"Player {winner_id}"
            
            embed = discord.Embed(
                title="🏆 Battle Complete!",
                description=f"**{winner_name}** wins the battle!\n\n{attack_result['message']}",
                color=0xffd700
            )
            
            embed.add_field(
                name="🎁 Rewards",
                value="• +50 XP\n• +1 Pack Token",
                inline=True
            )
            
            # Award rewards
            try:
                from ..database.connection import db_manager
                from bot import update_user_xp
                update_user_xp(winner_id, 50)
                pack_system.add_pack_tokens(winner_id, 'standard', 1)
            except Exception as e:
                print(f"Error awarding battle rewards: {e}")
            
            # Clean up battle
            battle_manager.finish_battle(battle.battle_id)
            
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            # Battle continues - update interface
            embed = self.create_battle_embed()
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def status_button_callback(self, interaction: discord.Interaction):
        """Handle status button press"""
        embed = self.create_detailed_status_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def forfeit_button_callback(self, interaction: discord.Interaction):
        """Handle forfeit button press"""
        battle = battle_manager.get_battle(self.battle_id)
        if not battle:
            await interaction.response.send_message("❌ Battle not found!", ephemeral=True)
            return
        
        # Get opponent information
        opponent_id = battle.get_opponent_id(interaction.user.id)
        opponent_user = interaction.client.get_user(opponent_id)
        opponent_name = opponent_user.display_name if opponent_user else f"Player {opponent_id}"
        
        # End the battle
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
            from ..database.connection import db_manager
            from bot import update_user_xp
            update_user_xp(opponent_id, 25)
            pack_system.add_pack_tokens(opponent_id, 'standard', 1)
        except Exception as e:
            print(f"Error awarding forfeit rewards: {e}")
        
        # Clean up battle
        battle_manager.finish_battle(battle.battle_id)
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def refresh_button_callback(self, interaction: discord.Interaction):
        """Handle refresh button press"""
        embed = self.create_battle_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    def create_battle_embed(self):
        """Create the main battle embed with enhanced turn communication"""
        battle = battle_manager.get_battle(self.battle_id)
        if not battle:
            return discord.Embed(title="❌ Battle Not Found", color=0xff0000)
        
        # Get battle state
        battle_state = battle.get_battle_state()
        player1_card = battle_state['player1_card']
        player2_card = battle_state['player2_card']
        
        # Determine whose turn it is and create appropriate title
        is_your_turn = battle.current_turn == self.user_id
        current_turn_user = None
        try:
            # Try to get user from interaction client (this might not work in all contexts)
            current_turn_user = battle_manager.db.bot.get_user(battle.current_turn) if hasattr(battle_manager.db, 'bot') else None
        except:
            pass
        
        current_turn_name = current_turn_user.display_name if current_turn_user else f"Player {battle.current_turn}"
        
        if is_your_turn:
            title = f"⚔️ Your Turn to Attack! (Turn {battle.turn_number})"
            color = 0x00ff00  # Green for your turn
            description = f"🎯 **It's your turn!** Use the Attack button below to strike!\n**Battle ID:** {battle.battle_id}"
        else:
            title = f"⏳ Waiting for {current_turn_name} (Turn {battle.turn_number})"
            color = 0xffa500  # Orange for waiting
            description = f"🕐 **Waiting for opponent** to make their move...\n**Battle ID:** {battle.battle_id}"
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        if player1_card and player2_card:
            # Get player names (fallback method)
            player1_name = f"Player {battle.player1_id}"
            player2_name = f"Player {battle.player2_id}"
            
            # Try to get actual names
            try:
                if hasattr(battle_manager.db, 'bot'):
                    p1_user = battle_manager.db.bot.get_user(battle.player1_id)
                    p2_user = battle_manager.db.bot.get_user(battle.player2_id)
                    if p1_user:
                        player1_name = p1_user.display_name
                    if p2_user:
                        player2_name = p2_user.display_name
            except:
                pass
            
            # Create health bars
            def create_health_bar(current_hp, max_hp, length=10):
                if max_hp <= 0:
                    return "💀 DEFEATED"
                
                percentage = current_hp / max_hp
                filled = int(percentage * length)
                empty = length - filled
                
                bar = "█" * filled + "░" * empty
                return f"{bar} {current_hp}/{max_hp} HP"
            
            # Add turn indicator to player names
            p1_indicator = " 🎯" if battle.current_turn == battle.player1_id else ""
            p2_indicator = " 🎯" if battle.current_turn == battle.player2_id else ""
            
            # Add card status with turn indicators
            embed.add_field(
                name=f"🃏 {player1_name}'s {player1_card['name']}{p1_indicator}",
                value=f"❤️ {create_health_bar(player1_card['current_health'], player1_card['max_health'])}\n⚔️ {player1_card['current_attack']} ATK",
                inline=True
            )
            
            embed.add_field(
                name=f"🃏 {player2_name}'s {player2_card['name']}{p2_indicator}",
                value=f"❤️ {create_health_bar(player2_card['current_health'], player2_card['max_health'])}\n⚔️ {player2_card['current_attack']} ATK",
                inline=True
            )
            
            # Add clear action indicator
            if is_your_turn:
                embed.add_field(
                    name="🎮 Your Action",
                    value="✅ **Click [⚔️ Attack] to strike!**\n📊 Use [Status] for details\n🔄 Use [Refresh] to update",
                    inline=True
                )
            else:
                embed.add_field(
                    name="⏳ Waiting",
                    value=f"🕐 **{current_turn_name}** is choosing their action...\n📊 Use [Status] for details\n🔄 Use [Refresh] to update",
                    inline=True
                )
        
        # Add recent battle log with better formatting
        if battle.battle_log:
            recent_log = battle.battle_log[-2:]  # Last 2 events
            log_text = "\n".join([f"• {event['message']}" for event in recent_log])
            embed.add_field(
                name="📜 Recent Battle Events",
                value=log_text,
                inline=False
            )
        
        # Enhanced footer with turn information
        if is_your_turn:
            embed.set_footer(text="🎯 Your turn! Click Attack to strike your opponent!")
        else:
            embed.set_footer(text=f"⏳ Waiting for {current_turn_name} to attack...")
        
        return embed
    
    def create_detailed_status_embed(self):
        """Create detailed status embed for status button"""
        battle = battle_manager.get_battle(self.battle_id)
        if not battle:
            return discord.Embed(title="❌ Battle Not Found", color=0xff0000)
        
        embed = discord.Embed(
            title="📊 Detailed Battle Status",
            description=f"**Battle ID:** {battle.battle_id}\n**Turn:** {battle.turn_number}",
            color=0x3498db
        )
        
        # Add detailed card information
        if battle.player1_card and battle.player2_card:
            p1_card = battle.player1_card
            p2_card = battle.player2_card
            
            embed.add_field(
                name=f"🃏 Player 1: {p1_card.name}",
                value=f"❤️ {p1_card.current_health}/{p1_card.max_health} HP\n⚔️ {p1_card.current_attack} ATK\n🛡️ {p1_card.damage_reduction} Armor\n🎯 {p1_card.ability}",
                inline=True
            )
            
            embed.add_field(
                name=f"🃏 Player 2: {p2_card.name}",
                value=f"❤️ {p2_card.current_health}/{p2_card.max_health} HP\n⚔️ {p2_card.current_attack} ATK\n🛡️ {p2_card.damage_reduction} Armor\n🎯 {p2_card.ability}",
                inline=True
            )
        
        # Add full battle log
        if battle.battle_log:
            log_text = "\n".join([f"• {event['message']}" for event in battle.battle_log[-5:]])
            embed.add_field(
                name="📜 Battle Log (Last 5 Events)",
                value=log_text,
                inline=False
            )
        
        return embed
