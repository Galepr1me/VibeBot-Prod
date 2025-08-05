"""
Battle System
Handles turn-based card battles between players
"""
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import random
import json
from datetime import datetime
from ..database.connection import db_manager
from .abilities import ability_system
from .card_library import CardLibrary


class BattleState(Enum):
    """Battle state enumeration"""
    WAITING_FOR_OPPONENT = "waiting_for_opponent"
    CARD_SELECTION = "card_selection"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class TurnPhase(Enum):
    """Turn phase enumeration"""
    CARD_PLAY = "card_play"
    ATTACK = "attack"
    END_TURN = "end_turn"


class BattleCard:
    """Represents a card in battle with current stats"""
    
    def __init__(self, card_data: Dict[str, Any], owner_id: int):
        self.card_id = card_data.get('card_id', 0)
        self.name = card_data['name']
        self.element = card_data['element']
        self.rarity = card_data['rarity']
        self.base_attack = card_data['attack']
        self.base_health = card_data['health']
        self.cost = card_data['cost']
        self.ability = card_data['ability']
        self.ascii_art = card_data.get('ascii', '')
        self.owner_id = owner_id
        
        # Current battle stats (can be modified by abilities)
        self.current_attack = self.base_attack
        self.current_health = self.base_health
        self.max_health = self.base_health
        
        # Battle effects
        self.effects = {}  # Dictionary of active effects
        self.has_attacked = False
        self.can_attack = True
        self.is_stunned = False
        self.dodge_chance = 0
        self.damage_reduction = 0
        self.shield_amount = 0
        
        # Special flags
        self.has_rush = 'Rush:' in self.ability
        self.has_flying = 'Flying:' in self.ability
        self.has_stealth = 'Stealth:' in self.ability or 'stealth' in self.ability.lower()
        self.has_taunt = 'Taunt:' in self.ability
    
    def is_alive(self) -> bool:
        """Check if card is still alive"""
        return self.current_health > 0
    
    def take_damage(self, damage: int) -> int:
        """Apply damage to the card, returns actual damage taken"""
        if damage <= 0:
            return 0
        
        # Apply damage reduction (armor)
        reduced_damage = max(1, damage - self.damage_reduction)
        
        # Apply shield
        if self.shield_amount > 0:
            shield_absorbed = min(self.shield_amount, reduced_damage)
            self.shield_amount -= shield_absorbed
            reduced_damage -= shield_absorbed
        
        # Apply remaining damage to health
        actual_damage = min(reduced_damage, self.current_health)
        self.current_health -= actual_damage
        
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal the card, returns actual healing done"""
        if amount <= 0:
            return 0
        
        actual_healing = min(amount, self.max_health - self.current_health)
        self.current_health += actual_healing
        return actual_healing
    
    def can_dodge_attack(self) -> bool:
        """Check if card dodges an attack"""
        if self.dodge_chance <= 0:
            return False
        return random.randint(1, 100) <= self.dodge_chance
    
    def reset_turn_flags(self):
        """Reset turn-specific flags"""
        self.has_attacked = False
        if not self.has_rush:
            self.can_attack = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert card to dictionary for storage"""
        return {
            'card_id': self.card_id,
            'name': self.name,
            'element': self.element,
            'rarity': self.rarity,
            'base_attack': self.base_attack,
            'base_health': self.base_health,
            'current_attack': self.current_attack,
            'current_health': self.current_health,
            'max_health': self.max_health,
            'cost': self.cost,
            'ability': self.ability,
            'owner_id': self.owner_id,
            'effects': self.effects,
            'has_attacked': self.has_attacked,
            'can_attack': self.can_attack,
            'is_stunned': self.is_stunned,
            'dodge_chance': self.dodge_chance,
            'damage_reduction': self.damage_reduction,
            'shield_amount': self.shield_amount
        }


class Battle:
    """Represents a battle between two players"""
    
    def __init__(self, battle_id: int, player1_id: int, player2_id: int):
        self.battle_id = battle_id
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.state = BattleState.CARD_SELECTION
        self.current_turn = player1_id  # Player 1 goes first
        self.turn_number = 1
        self.phase = TurnPhase.CARD_PLAY
        
        # Battle cards (one card per player for now)
        self.player1_card: Optional[BattleCard] = None
        self.player2_card: Optional[BattleCard] = None
        
        # Battle log
        self.battle_log = []
        self.created_at = datetime.now()
        self.finished_at = None
        self.winner_id = None
        
        # Card library reference
        self.card_library = CardLibrary()
    
    def add_card(self, player_id: int, card_data: Dict[str, Any]) -> bool:
        """Add a card for a player"""
        try:
            battle_card = BattleCard(card_data, player_id)
            
            if player_id == self.player1_id:
                self.player1_card = battle_card
            elif player_id == self.player2_id:
                self.player2_card = battle_card
            else:
                return False
            
            # Check if both players have selected cards
            if self.player1_card and self.player2_card:
                self.state = BattleState.IN_PROGRESS
                self.log_event(f"Battle begins! {self.player1_card.name} vs {self.player2_card.name}")
                
                # Trigger on_play abilities
                self._trigger_on_play_abilities()
            
            return True
        except Exception as e:
            print(f"Error adding card to battle: {e}")
            return False
    
    def get_player_card(self, player_id: int) -> Optional[BattleCard]:
        """Get the card for a specific player"""
        if player_id == self.player1_id:
            return self.player1_card
        elif player_id == self.player2_id:
            return self.player2_card
        return None
    
    def get_opponent_card(self, player_id: int) -> Optional[BattleCard]:
        """Get the opponent's card"""
        if player_id == self.player1_id:
            return self.player2_card
        elif player_id == self.player2_id:
            return self.player1_card
        return None
    
    def get_opponent_id(self, player_id: int) -> Optional[int]:
        """Get the opponent's ID"""
        if player_id == self.player1_id:
            return self.player2_id
        elif player_id == self.player2_id:
            return self.player1_id
        return None
    
    def is_player_turn(self, player_id: int) -> bool:
        """Check if it's the player's turn"""
        return self.current_turn == player_id and self.state == BattleState.IN_PROGRESS
    
    def attack(self, attacker_id: int) -> Dict[str, Any]:
        """Execute an attack"""
        if not self.is_player_turn(attacker_id):
            return {'success': False, 'message': 'Not your turn!'}
        
        if self.phase != TurnPhase.ATTACK:
            return {'success': False, 'message': 'Not the attack phase!'}
        
        attacker_card = self.get_player_card(attacker_id)
        defender_card = self.get_opponent_card(attacker_id)
        
        if not attacker_card or not defender_card:
            return {'success': False, 'message': 'Missing battle cards!'}
        
        if not attacker_card.can_attack or attacker_card.has_attacked:
            return {'success': False, 'message': 'Card cannot attack!'}
        
        if not attacker_card.is_alive():
            return {'success': False, 'message': 'Dead cards cannot attack!'}
        
        # Execute the attack
        return self._execute_attack(attacker_card, defender_card)
    
    def _execute_attack(self, attacker: BattleCard, defender: BattleCard) -> Dict[str, Any]:
        """Execute the actual attack logic"""
        attack_damage = attacker.current_attack
        
        # Check for dodge
        if defender.can_dodge_attack():
            self.log_event(f"{defender.name} dodged {attacker.name}'s attack!")
            attacker.has_attacked = True
            self._end_turn()
            return {
                'success': True,
                'dodged': True,
                'message': f"{defender.name} dodged the attack!",
                'battle_state': self.get_battle_state()
            }
        
        # Apply damage
        damage_dealt = defender.take_damage(attack_damage)
        attacker.has_attacked = True
        
        self.log_event(f"{attacker.name} attacks {defender.name} for {damage_dealt} damage!")
        
        # Check for death
        if not defender.is_alive():
            self.log_event(f"{defender.name} has been defeated!")
            self._end_battle(attacker.owner_id)
            return {
                'success': True,
                'damage_dealt': damage_dealt,
                'target_defeated': True,
                'winner': attacker.owner_id,
                'message': f"{attacker.name} defeats {defender.name}!",
                'battle_state': self.get_battle_state()
            }
        
        # End turn
        self._end_turn()
        
        return {
            'success': True,
            'damage_dealt': damage_dealt,
            'target_defeated': False,
            'message': f"{attacker.name} deals {damage_dealt} damage to {defender.name}!",
            'battle_state': self.get_battle_state()
        }
    
    def _trigger_on_play_abilities(self):
        """Trigger on_play abilities for both cards"""
        if self.player1_card:
            self._trigger_ability(self.player1_card, 'on_play')
        if self.player2_card:
            self._trigger_ability(self.player2_card, 'on_play')
    
    def _trigger_ability(self, card: BattleCard, trigger: str):
        """Trigger a card's ability if it matches the trigger"""
        if not ability_system.can_trigger_ability(card.ability, trigger):
            return
        
        # Get target card (for now, abilities target the opponent)
        target_card = self.get_opponent_card(card.owner_id)
        
        # Create ability context
        caster_data = card.to_dict()
        target_data = target_card.to_dict() if target_card else None
        battle_context = {'battle_id': self.battle_id, 'turn': self.turn_number}
        
        # Execute ability
        result = ability_system.execute_ability(card.ability, caster_data, target_data, battle_context)
        
        if result['success']:
            self.log_event(f"{card.name} uses {card.ability}!")
            self._apply_ability_result(card, target_card, result)
        else:
            self.log_event(f"{card.name}'s ability failed: {result['message']}")
    
    def _apply_ability_result(self, caster: BattleCard, target: Optional[BattleCard], result: Dict[str, Any]):
        """Apply the results of an ability to the battle"""
        effect_result = result.get('result', {})
        effect_type = result.get('effect_type', '')
        
        if not effect_result.get('applied', False):
            return
        
        # Apply different effect types
        if effect_type == 'damage' and target:
            damage = effect_result.get('damage_dealt', 0)
            actual_damage = target.take_damage(damage)
            self.log_event(f"{target.name} takes {actual_damage} damage from {caster.name}'s ability!")
            
            if not target.is_alive():
                self.log_event(f"{target.name} is defeated by {caster.name}'s ability!")
                self._end_battle(caster.owner_id)
        
        elif effect_type == 'heal':
            heal_amount = effect_result.get('heal_amount', 0)
            actual_healing = caster.heal(heal_amount)
            self.log_event(f"{caster.name} heals for {actual_healing} health!")
        
        elif effect_type == 'damage_boost':
            boost = effect_result.get('attack_boost', 0)
            caster.current_attack += boost
            self.log_event(f"{caster.name}'s attack increases by {boost}!")
        
        elif effect_type == 'shield':
            shield = effect_result.get('shield_amount', 0)
            caster.shield_amount += shield
            self.log_event(f"{caster.name} gains {shield} shield!")
        
        elif effect_type == 'dodge':
            dodge_chance = effect_result.get('dodge_chance', 0)
            caster.dodge_chance = dodge_chance
            self.log_event(f"{caster.name} gains {dodge_chance}% dodge chance!")
        
        elif effect_type == 'damage_reduction':
            reduction = effect_result.get('damage_reduction', 0)
            caster.damage_reduction += reduction
            self.log_event(f"{caster.name} gains {reduction} armor!")
    
    def _end_turn(self):
        """End the current turn and switch to the next player"""
        # Switch turns
        if self.current_turn == self.player1_id:
            self.current_turn = self.player2_id
        else:
            self.current_turn = self.player1_id
            self.turn_number += 1
        
        # Reset turn flags
        if self.player1_card:
            self.player1_card.reset_turn_flags()
        if self.player2_card:
            self.player2_card.reset_turn_flags()
        
        # Reset phase
        self.phase = TurnPhase.ATTACK
        
        self.log_event(f"Turn {self.turn_number} begins!")
    
    def _end_battle(self, winner_id: int):
        """End the battle with a winner"""
        self.state = BattleState.FINISHED
        self.winner_id = winner_id
        self.finished_at = datetime.now()
        self.log_event(f"Battle ends! Player {winner_id} wins!")
    
    def log_event(self, message: str):
        """Add an event to the battle log"""
        timestamp = datetime.now().isoformat()
        self.battle_log.append({
            'timestamp': timestamp,
            'turn': self.turn_number,
            'message': message
        })
    
    def get_battle_state(self) -> Dict[str, Any]:
        """Get the current battle state"""
        return {
            'battle_id': self.battle_id,
            'state': self.state.value,
            'current_turn': self.current_turn,
            'turn_number': self.turn_number,
            'phase': self.phase.value,
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'player1_card': self.player1_card.to_dict() if self.player1_card else None,
            'player2_card': self.player2_card.to_dict() if self.player2_card else None,
            'winner_id': self.winner_id,
            'battle_log': self.battle_log[-5:],  # Last 5 events
            'created_at': self.created_at.isoformat(),
            'finished_at': self.finished_at.isoformat() if self.finished_at else None
        }


class BattleManager:
    """Manages all battles and battle operations"""
    
    def __init__(self):
        self.db = db_manager
        self.active_battles: Dict[int, Battle] = {}
        self.card_library = CardLibrary()
        self._ensure_battle_tables()
    
    def _ensure_battle_tables(self):
        """Ensure battle tables exist"""
        try:
            # Battles table
            if self.db.db_type == 'postgresql':
                self.db.execute_query('''
                    CREATE TABLE IF NOT EXISTS battles (
                        battle_id SERIAL PRIMARY KEY,
                        player1_id BIGINT NOT NULL,
                        player2_id BIGINT NOT NULL,
                        state VARCHAR(50) NOT NULL DEFAULT 'waiting_for_opponent',
                        current_turn BIGINT,
                        battle_data JSONB,
                        winner_id BIGINT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        finished_at TIMESTAMP
                    )
                ''')
            else:
                self.db.execute_query('''
                    CREATE TABLE IF NOT EXISTS battles (
                        battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player1_id INTEGER NOT NULL,
                        player2_id INTEGER NOT NULL,
                        state TEXT NOT NULL DEFAULT 'waiting_for_opponent',
                        current_turn INTEGER,
                        battle_data TEXT,
                        winner_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        finished_at TIMESTAMP
                    )
                ''')
            
            print("[BATTLE_MANAGER] Battle tables ensured")
        except Exception as e:
            print(f"[BATTLE_MANAGER] Error creating battle tables: {e}")
    
    def create_battle(self, player1_id: int, player2_id: int) -> Optional[Battle]:
        """Create a new battle between two players"""
        try:
            # Insert battle into database
            if self.db.db_type == 'postgresql':
                result = self.db.fetch_one('''
                    INSERT INTO battles (player1_id, player2_id, state) 
                    VALUES (%s, %s, %s) RETURNING battle_id
                ''', (player1_id, player2_id, BattleState.CARD_SELECTION.value))
            else:
                self.db.execute_query('''
                    INSERT INTO battles (player1_id, player2_id, state) 
                    VALUES (?, ?, ?)
                ''', (player1_id, player2_id, BattleState.CARD_SELECTION.value))
                result = self.db.fetch_one('SELECT last_insert_rowid()')
            
            if not result:
                return None
            
            battle_id = result[0]
            
            # Create battle object
            battle = Battle(battle_id, player1_id, player2_id)
            self.active_battles[battle_id] = battle
            
            print(f"[BATTLE_MANAGER] Created battle {battle_id}: {player1_id} vs {player2_id}")
            return battle
            
        except Exception as e:
            print(f"[BATTLE_MANAGER] Error creating battle: {e}")
            return None
    
    def get_battle(self, battle_id: int) -> Optional[Battle]:
        """Get a battle by ID"""
        return self.active_battles.get(battle_id)
    
    def get_player_active_battle(self, player_id: int) -> Optional[Battle]:
        """Get a player's active battle"""
        for battle in self.active_battles.values():
            if (battle.player1_id == player_id or battle.player2_id == player_id) and \
               battle.state in [BattleState.CARD_SELECTION, BattleState.IN_PROGRESS]:
                return battle
        return None
    
    def save_battle(self, battle: Battle):
        """Save battle state to database"""
        try:
            battle_data = json.dumps(battle.get_battle_state())
            
            if self.db.db_type == 'postgresql':
                self.db.execute_query('''
                    UPDATE battles SET 
                    state = %s, current_turn = %s, battle_data = %s, 
                    winner_id = %s, finished_at = %s
                    WHERE battle_id = %s
                ''', (
                    battle.state.value, battle.current_turn, battle_data,
                    battle.winner_id, battle.finished_at, battle.battle_id
                ))
            else:
                self.db.execute_query('''
                    UPDATE battles SET 
                    state = ?, current_turn = ?, battle_data = ?, 
                    winner_id = ?, finished_at = ?
                    WHERE battle_id = ?
                ''', (
                    battle.state.value, battle.current_turn, battle_data,
                    battle.winner_id, battle.finished_at, battle.battle_id
                ))
            
        except Exception as e:
            print(f"[BATTLE_MANAGER] Error saving battle {battle.battle_id}: {e}")
    
    def finish_battle(self, battle_id: int):
        """Finish and clean up a battle"""
        battle = self.active_battles.get(battle_id)
        if battle:
            self.save_battle(battle)
            del self.active_battles[battle_id]
            print(f"[BATTLE_MANAGER] Finished battle {battle_id}")


# Global battle manager instance
battle_manager = BattleManager()
