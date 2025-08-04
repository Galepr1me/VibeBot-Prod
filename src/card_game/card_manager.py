"""
Card Manager
Handles card collection operations and database interactions
"""
from typing import List, Dict, Any, Optional
from ..database.connection import db_manager


class CardManager:
    """Manages user card collections and database operations"""
    
    def __init__(self):
        self.db = db_manager
    
    def add_card_to_collection(self, user_id: int, card_id: int, quantity: int = 1) -> bool:
        """Add a card to user's collection"""
        try:
            if self.db.db_type == 'postgresql':
                # Try to insert new card, or update quantity if it exists
                self.db.execute_query('''INSERT INTO user_cards (user_id, card_id, quantity) 
                                         VALUES (%s, %s, %s) 
                                         ON CONFLICT (user_id, card_id) 
                                         DO UPDATE SET quantity = user_cards.quantity + %s''',
                                      (user_id, card_id, quantity, quantity))
            else:
                # SQLite approach - check if exists first
                existing = self.db.fetch_one('SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = ?', 
                                           (user_id, card_id))
                
                if existing:
                    new_quantity = existing[0] + quantity
                    self.db.execute_query('UPDATE user_cards SET quantity = ? WHERE user_id = ? AND card_id = ?',
                                         (new_quantity, user_id, card_id))
                else:
                    self.db.execute_query('INSERT INTO user_cards (user_id, card_id, quantity) VALUES (?, ?, ?)',
                                         (user_id, card_id, quantity))
            
            return True
        except Exception as e:
            print(f"Error adding card to collection: {e}")
            return False
    
    def get_user_collection(self, user_id: int) -> List[tuple]:
        """Get user's card collection with card details"""
        try:
            return self.db.fetch_all('''SELECT c.card_id, c.name, c.element, c.rarity, c.attack, c.health, c.cost, c.ability, c.ascii_art, uc.quantity
                                       FROM cards c 
                                       JOIN user_cards uc ON c.card_id = uc.card_id 
                                       WHERE uc.user_id = ? 
                                       ORDER BY c.rarity DESC, c.name''', (user_id,))
        except Exception as e:
            print(f"Error getting user collection: {e}")
            return []
    
    def get_card_by_name(self, card_name: str) -> Optional[tuple]:
        """Get card details from database by name"""
        try:
            return self.db.fetch_one('SELECT * FROM cards WHERE name = ?', (card_name,))
        except Exception as e:
            print(f"Error getting card by name: {e}")
            return None
    
    def get_collection_stats(self, user_id: int) -> Dict[str, int]:
        """Get user's collection statistics"""
        try:
            collection = self.get_user_collection(user_id)
            
            if not collection:
                return {'total_cards': 0, 'unique_cards': 0, 'rare_cards': 0}
            
            total_cards = sum(card[9] for card in collection)  # quantity is index 9
            unique_cards = len(collection)
            rare_cards = sum(1 for card in collection if card[3] in ['rare', 'epic', 'legendary', 'mythic'])
            
            return {
                'total_cards': total_cards,
                'unique_cards': unique_cards,
                'rare_cards': rare_cards
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {'total_cards': 0, 'unique_cards': 0, 'rare_cards': 0}
    
    def get_rarity_breakdown(self, user_id: int) -> Dict[str, int]:
        """Get breakdown of cards by rarity"""
        try:
            collection = self.get_user_collection(user_id)
            
            rarity_counts = {}
            for card in collection:
                rarity = card[3]  # rarity is index 3
                quantity = card[9]  # quantity is index 9
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + quantity
            
            return rarity_counts
        except Exception as e:
            print(f"Error getting rarity breakdown: {e}")
            return {}
    
    def user_has_card(self, user_id: int, card_name: str) -> bool:
        """Check if user has a specific card"""
        try:
            result = self.db.fetch_one('''SELECT uc.quantity FROM user_cards uc
                                         JOIN cards c ON uc.card_id = c.card_id
                                         WHERE uc.user_id = ? AND c.name = ?''', 
                                      (user_id, card_name))
            return result is not None and result[0] > 0
        except Exception as e:
            print(f"Error checking if user has card: {e}")
            return False
    
    def get_card_quantity(self, user_id: int, card_name: str) -> int:
        """Get quantity of a specific card in user's collection"""
        try:
            result = self.db.fetch_one('''SELECT uc.quantity FROM user_cards uc
                                         JOIN cards c ON uc.card_id = c.card_id
                                         WHERE uc.user_id = ? AND c.name = ?''', 
                                      (user_id, card_name))
            return result[0] if result else 0
        except Exception as e:
            print(f"Error getting card quantity: {e}")
            return 0
    
    def remove_card_from_collection(self, user_id: int, card_id: int, quantity: int = 1) -> bool:
        """Remove cards from user's collection"""
        try:
            # Check current quantity
            current = self.db.fetch_one('SELECT quantity FROM user_cards WHERE user_id = ? AND card_id = ?',
                                       (user_id, card_id))
            
            if not current or current[0] < quantity:
                return False  # Not enough cards to remove
            
            new_quantity = current[0] - quantity
            
            if new_quantity <= 0:
                # Remove the entry entirely
                self.db.execute_query('DELETE FROM user_cards WHERE user_id = ? AND card_id = ?',
                                     (user_id, card_id))
            else:
                # Update quantity
                self.db.execute_query('UPDATE user_cards SET quantity = ? WHERE user_id = ? AND card_id = ?',
                                     (new_quantity, user_id, card_id))
            
            return True
        except Exception as e:
            print(f"Error removing card from collection: {e}")
            return False
    
    def wipe_user_collection(self, user_id: int) -> bool:
        """Wipe all cards from a user's collection"""
        try:
            self.db.execute_query('DELETE FROM user_cards WHERE user_id = ?', (user_id,))
            return True
        except Exception as e:
            print(f"Error wiping user collection: {e}")
            return False
    
    def wipe_all_collections(self) -> bool:
        """Wipe all user card collections (admin function)"""
        try:
            self.db.execute_query('DELETE FROM user_cards')
            return True
        except Exception as e:
            print(f"Error wiping all collections: {e}")
            return False


# Global card manager instance
card_manager = CardManager()
