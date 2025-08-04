"""
Pack System
Handles pack tokens, pack opening, and reward generation
"""
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..database.connection import db_manager
from .card_library import CardLibrary
from .card_manager import CardManager


class PackSystem:
    """Manages pack tokens and pack opening mechanics"""
    
    def __init__(self):
        self.db = db_manager
        self.card_library = CardLibrary()
        self.card_manager = CardManager()
    
    def add_pack_tokens(self, user_id: int, pack_type: str = 'standard', quantity: int = 1) -> bool:
        """Add pack tokens to user's inventory"""
        try:
            if self.db.db_type == 'postgresql':
                self.db.execute_query('''INSERT INTO user_packs (user_id, pack_type, quantity) 
                                         VALUES (%s, %s, %s) 
                                         ON CONFLICT (user_id, pack_type) 
                                         DO UPDATE SET quantity = user_packs.quantity + %s''',
                                      (user_id, pack_type, quantity, quantity))
            else:
                # SQLite approach
                existing = self.db.fetch_one('SELECT quantity FROM user_packs WHERE user_id = ? AND pack_type = ?', 
                                           (user_id, pack_type))
                
                if existing:
                    new_quantity = existing[0] + quantity
                    self.db.execute_query('UPDATE user_packs SET quantity = ? WHERE user_id = ? AND pack_type = ?',
                                         (new_quantity, user_id, pack_type))
                else:
                    self.db.execute_query('INSERT INTO user_packs (user_id, pack_type, quantity) VALUES (?, ?, ?)',
                                         (user_id, pack_type, quantity))
            
            return True
        except Exception as e:
            print(f"Error adding pack tokens: {e}")
            return False
    
    def get_user_pack_tokens(self, user_id: int) -> Dict[str, int]:
        """Get user's pack token inventory"""
        try:
            results = self.db.fetch_all('SELECT pack_type, quantity FROM user_packs WHERE user_id = ? AND quantity > 0', 
                                       (user_id,))
            return {pack_type: quantity for pack_type, quantity in results}
        except Exception as e:
            print(f"Error getting pack tokens: {e}")
            return {}
    
    def consume_pack_token(self, user_id: int, pack_type: str = 'standard') -> bool:
        """Consume one pack token and return success"""
        try:
            # Check if user has tokens
            result = self.db.fetch_one('SELECT quantity FROM user_packs WHERE user_id = ? AND pack_type = ?', 
                                      (user_id, pack_type))
            
            if not result or result[0] <= 0:
                return False
            
            # Consume one token
            new_quantity = result[0] - 1
            self.db.execute_query('UPDATE user_packs SET quantity = ? WHERE user_id = ? AND pack_type = ?',
                                 (new_quantity, user_id, pack_type))
            
            return True
        except Exception as e:
            print(f"Error consuming pack token: {e}")
            return False
    
    def open_pack(self, user_id: int, pack_type: str = 'standard', cards_per_pack: int = 3) -> Optional[List[Dict[str, Any]]]:
        """Open a pack and return the cards generated"""
        try:
            # Check and consume pack token
            if not self.consume_pack_token(user_id, pack_type):
                return None
            
            # Generate cards for the pack
            pack_cards = []
            
            for _ in range(cards_per_pack):
                # Determine rarity based on drop rates
                roll = random.randint(1, 100)
                cumulative = 0
                selected_rarity = 'common'
                
                for rarity, info in self.card_library.rarities.items():
                    cumulative += info['drop_rate']
                    if roll <= cumulative:
                        selected_rarity = rarity
                        break
                
                # Get random card of selected rarity
                rarity_cards = self.card_library.get_cards_by_rarity(selected_rarity)
                if rarity_cards:
                    selected_card = random.choice(rarity_cards)
                    pack_cards.append(selected_card)
                    
                    # Add card to user's collection in database
                    card_data = self.card_manager.get_card_by_name(selected_card['name'])
                    if card_data:
                        card_id = card_data[0]  # First column is card_id
                        self.card_manager.add_card_to_collection(user_id, card_id, 1)
            
            return pack_cards
            
        except Exception as e:
            print(f"Error opening pack: {e}")
            return None
    
    def get_pack_opening_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics about user's pack openings"""
        try:
            # Get total cards in collection
            collection_stats = self.card_manager.get_collection_stats(user_id)
            
            # Get remaining tokens
            tokens = self.get_user_pack_tokens(user_id)
            
            # Calculate estimated packs opened (rough estimate)
            total_cards = collection_stats.get('total_cards', 0)
            estimated_packs = total_cards // 3  # Assuming 3 cards per pack
            
            return {
                'estimated_packs_opened': estimated_packs,
                'total_cards_obtained': total_cards,
                'unique_cards_collected': collection_stats.get('unique_cards', 0),
                'rare_cards_obtained': collection_stats.get('rare_cards', 0),
                'remaining_tokens': tokens
            }
        except Exception as e:
            print(f"Error getting pack opening stats: {e}")
            return {}
    
    def simulate_pack_opening(self, pack_type: str = 'standard', cards_per_pack: int = 3) -> List[Dict[str, Any]]:
        """Simulate pack opening without consuming tokens or adding cards (for testing)"""
        try:
            pack_cards = []
            
            for _ in range(cards_per_pack):
                # Determine rarity based on drop rates
                roll = random.randint(1, 100)
                cumulative = 0
                selected_rarity = 'common'
                
                for rarity, info in self.card_library.rarities.items():
                    cumulative += info['drop_rate']
                    if roll <= cumulative:
                        selected_rarity = rarity
                        break
                
                # Get random card of selected rarity
                rarity_cards = self.card_library.get_cards_by_rarity(selected_rarity)
                if rarity_cards:
                    selected_card = random.choice(rarity_cards)
                    pack_cards.append(selected_card)
            
            return pack_cards
            
        except Exception as e:
            print(f"Error simulating pack opening: {e}")
            return []
    
    def get_pack_drop_rates(self) -> Dict[str, float]:
        """Get the current pack drop rates"""
        return {rarity: info['drop_rate'] for rarity, info in self.card_library.rarities.items()}
    
    def wipe_user_pack_tokens(self, user_id: int) -> bool:
        """Wipe all pack tokens for a specific user"""
        try:
            self.db.execute_query('DELETE FROM user_packs WHERE user_id = ?', (user_id,))
            return True
        except Exception as e:
            print(f"Error wiping user pack tokens: {e}")
            return False
    
    def wipe_all_pack_tokens(self) -> bool:
        """Wipe all pack tokens (admin function)"""
        try:
            self.db.execute_query('DELETE FROM user_packs')
            return True
        except Exception as e:
            print(f"Error wiping all pack tokens: {e}")
            return False
    
    def get_pack_system_stats(self) -> Dict[str, Any]:
        """Get overall pack system statistics"""
        try:
            # Total tokens in circulation
            total_tokens_result = self.db.fetch_one('SELECT SUM(quantity) FROM user_packs')
            total_tokens = total_tokens_result[0] if total_tokens_result and total_tokens_result[0] else 0
            
            # Users with tokens
            users_with_tokens_result = self.db.fetch_one('SELECT COUNT(DISTINCT user_id) FROM user_packs WHERE quantity > 0')
            users_with_tokens = users_with_tokens_result[0] if users_with_tokens_result else 0
            
            # Total cards in all collections
            total_cards_result = self.db.fetch_one('SELECT SUM(quantity) FROM user_cards')
            total_cards = total_cards_result[0] if total_cards_result and total_cards_result[0] else 0
            
            return {
                'total_tokens_in_circulation': total_tokens,
                'users_with_tokens': users_with_tokens,
                'total_cards_collected': total_cards,
                'estimated_packs_opened': total_cards // 3,
                'cards_in_library': len(self.card_library.get_all_cards())
            }
        except Exception as e:
            print(f"Error getting pack system stats: {e}")
            return {}


# Global pack system instance
pack_system = PackSystem()
