"""
Card Abilities System
Handles execution of card abilities and effects
"""
from typing import Dict, Any, List, Optional
from ..database.connection import db_manager


class AbilityEffect:
    """Represents a single ability effect"""
    
    def __init__(self, effect_type: str, value: int = 0, target: str = 'self', condition: str = None):
        self.effect_type = effect_type  # 'damage', 'heal', 'buff', 'debuff', etc.
        self.value = value  # Amount of effect
        self.target = target  # 'self', 'enemy', 'all_enemies', 'all_allies', 'any'
        self.condition = condition  # When to trigger: 'on_play', 'on_attack', 'on_damage', etc.


class AbilitySystem:
    """Manages card abilities and their execution"""
    
    def __init__(self):
        self.db = db_manager
        self._ability_registry = self._initialize_abilities()
    
    def _initialize_abilities(self) -> Dict[str, AbilityEffect]:
        """Initialize all card abilities from the card library"""
        abilities = {}
        
        # Basic damage abilities
        abilities['Burn: Deal 1 damage when played'] = AbilityEffect('damage', 1, 'enemy', 'on_play')
        abilities['Burn: Deal 1 extra damage'] = AbilityEffect('damage_boost', 1, 'self', 'on_attack')
        abilities['Burn: Deal 1 damage to enemy'] = AbilityEffect('damage', 1, 'enemy', 'on_play')
        abilities['Shock: Stun target'] = AbilityEffect('stun', 1, 'enemy', 'on_attack')
        abilities['Lightning: Deal 3 damage to any target'] = AbilityEffect('damage', 3, 'any', 'on_play')
        abilities['Backstab: Deal double damage to damaged enemies'] = AbilityEffect('damage_double', 0, 'enemy', 'on_attack')
        abilities['Immolate: Destroy to deal 5 damage'] = AbilityEffect('sacrifice_damage', 5, 'enemy', 'on_sacrifice')
        
        # Healing abilities
        abilities['Heal: Restore 1 health when played'] = AbilityEffect('heal', 1, 'self', 'on_play')
        abilities['Heal: Restore 2 health'] = AbilityEffect('heal', 2, 'self', 'on_play')
        abilities['Heal: Restore 1 health to ally'] = AbilityEffect('heal', 1, 'ally', 'on_play')
        abilities['Radiance: Heal all allies to full'] = AbilityEffect('heal_full', 0, 'all_allies', 'on_play')
        abilities['Tsunami: Heal all allies'] = AbilityEffect('heal', 3, 'all_allies', 'on_play')
        
        # Defensive abilities
        abilities['Armor: Reduce damage by 1'] = AbilityEffect('damage_reduction', 1, 'self', 'passive')
        abilities['Shield: Absorb next attack'] = AbilityEffect('shield', 1, 'self', 'on_play')
        abilities['Ice Shield: Reflect damage'] = AbilityEffect('reflect', 1, 'self', 'passive')
        abilities['Divine Shield: Immune to damage for 1 turn'] = AbilityEffect('immunity', 1, 'self', 'on_play')
        abilities['Protection: Shield allies'] = AbilityEffect('shield', 1, 'all_allies', 'on_play')
        
        # Utility abilities
        abilities['Rush: Can attack immediately'] = AbilityEffect('rush', 1, 'self', 'passive')
        abilities['Flying: Cannot be blocked'] = AbilityEffect('flying', 1, 'self', 'passive')
        abilities['Stealth: Cannot be targeted'] = AbilityEffect('stealth', 1, 'self', 'passive')
        abilities['Taunt: Enemies must attack this first'] = AbilityEffect('taunt', 1, 'self', 'passive')
        abilities['Swift: Attack first'] = AbilityEffect('first_strike', 1, 'self', 'passive')
        
        # Evasion abilities
        abilities['Evasion: 50% chance to dodge attacks'] = AbilityEffect('dodge', 50, 'self', 'passive')
        abilities['Dodge: 75% evasion chance'] = AbilityEffect('dodge', 75, 'self', 'passive')
        abilities['Phase: 25% dodge chance'] = AbilityEffect('dodge', 25, 'self', 'passive')
        abilities['Stealth: 50% dodge chance'] = AbilityEffect('dodge', 50, 'self', 'passive')
        
        # Stat modification abilities
        abilities['Rage: +1 attack when damaged'] = AbilityEffect('attack_boost', 1, 'self', 'on_damage')
        abilities['Blessing: Boost ally stats'] = AbilityEffect('stat_boost', 1, 'ally', 'on_play')
        abilities['Fear: Reduce enemy attack'] = AbilityEffect('attack_debuff', 1, 'enemy', 'on_play')
        abilities['Curse: Reduce enemy attack by 1'] = AbilityEffect('attack_debuff', 1, 'enemy', 'on_play')
        abilities['Growth: Gain +1/+1 each turn'] = AbilityEffect('stat_boost', 1, 'self', 'each_turn')
        
        # Special abilities
        abilities['Rebirth: Return when destroyed'] = AbilityEffect('resurrect', 1, 'self', 'on_death')
        abilities['Rebirth: Return to hand when destroyed'] = AbilityEffect('return_hand', 1, 'self', 'on_death')
        abilities['Draw: Draw a card when played'] = AbilityEffect('draw', 1, 'player', 'on_play')
        abilities['Sacrifice: Destroy to draw card'] = AbilityEffect('sacrifice_draw', 1, 'player', 'on_sacrifice')
        abilities['Freeze: Skip enemy turn'] = AbilityEffect('freeze', 1, 'enemy', 'on_attack')
        
        # Area effect abilities
        abilities['Inferno: Deal damage to all enemies'] = AbilityEffect('damage', 2, 'all_enemies', 'on_play')
        abilities['Tentacles: Attack all enemies'] = AbilityEffect('damage', 1, 'all_enemies', 'on_attack')
        abilities['Earthquake: Stun all enemies'] = AbilityEffect('stun', 1, 'all_enemies', 'on_play')
        abilities['Tempest: All creatures gain flying'] = AbilityEffect('flying', 1, 'all_creatures', 'on_play')
        
        # Complex abilities
        abilities['Molten: Damage attackers'] = AbilityEffect('counter_damage', 1, 'attacker', 'on_attacked')
        abilities['Drain: Heal when dealing damage'] = AbilityEffect('lifesteal', 1, 'self', 'on_damage_dealt')
        abilities['Ambush: +2 attack if enemy damaged'] = AbilityEffect('conditional_attack', 2, 'self', 'on_attack')
        abilities['Reflect: Return spell damage'] = AbilityEffect('spell_reflect', 1, 'self', 'passive')
        abilities['Devour: Destroy any card and gain its stats'] = AbilityEffect('devour', 1, 'any', 'on_play')
        abilities['Consume: Destroy ally to gain +3/+3'] = AbilityEffect('sacrifice_boost', 3, 'self', 'on_play')
        
        return abilities
    
    def get_ability_effect(self, ability_text: str) -> Optional[AbilityEffect]:
        """Get the effect for a given ability text"""
        if ability_text == 'None' or not ability_text:
            return None
        return self._ability_registry.get(ability_text)
    
    def can_trigger_ability(self, ability_text: str, trigger_condition: str) -> bool:
        """Check if an ability can trigger under the given condition"""
        effect = self.get_ability_effect(ability_text)
        if not effect:
            return False
        return effect.condition == trigger_condition or effect.condition == 'passive'
    
    def execute_ability(self, ability_text: str, caster_data: Dict[str, Any], 
                       target_data: Dict[str, Any] = None, battle_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an ability and return the results"""
        effect = self.get_ability_effect(ability_text)
        if not effect:
            return {'success': False, 'message': 'Unknown ability'}
        
        try:
            result = self._execute_effect(effect, caster_data, target_data, battle_context)
            return {
                'success': True,
                'effect_type': effect.effect_type,
                'value': effect.value,
                'target': effect.target,
                'result': result,
                'message': self._format_ability_message(ability_text, result)
            }
        except Exception as e:
            print(f"Error executing ability '{ability_text}': {e}")
            return {'success': False, 'message': f'Ability execution failed: {str(e)}'}
    
    def _execute_effect(self, effect: AbilityEffect, caster_data: Dict[str, Any], 
                       target_data: Dict[str, Any] = None, battle_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the actual effect logic"""
        result = {}
        
        if effect.effect_type == 'damage':
            result = self._apply_damage(effect.value, caster_data, target_data)
        elif effect.effect_type == 'heal':
            result = self._apply_heal(effect.value, caster_data, target_data)
        elif effect.effect_type == 'damage_boost':
            result = self._apply_damage_boost(effect.value, caster_data)
        elif effect.effect_type == 'shield':
            result = self._apply_shield(effect.value, caster_data, target_data)
        elif effect.effect_type == 'stun':
            result = self._apply_stun(effect.value, target_data)
        elif effect.effect_type == 'dodge':
            result = self._apply_dodge_chance(effect.value, caster_data)
        elif effect.effect_type == 'attack_boost':
            result = self._apply_attack_boost(effect.value, caster_data)
        elif effect.effect_type == 'attack_debuff':
            result = self._apply_attack_debuff(effect.value, target_data)
        elif effect.effect_type == 'damage_reduction':
            result = self._apply_damage_reduction(effect.value, caster_data)
        else:
            result = {'applied': False, 'message': f'Effect type {effect.effect_type} not implemented yet'}
        
        return result
    
    def _apply_damage(self, damage: int, caster_data: Dict[str, Any], target_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply damage to target"""
        if not target_data:
            return {'applied': False, 'message': 'No target specified'}
        
        # Apply damage (would be used in battle system)
        return {
            'applied': True,
            'damage_dealt': damage,
            'target_id': target_data.get('card_id'),
            'message': f'Dealt {damage} damage'
        }
    
    def _apply_heal(self, heal_amount: int, caster_data: Dict[str, Any], target_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply healing to target (or self if no target)"""
        target = target_data or caster_data
        
        return {
            'applied': True,
            'heal_amount': heal_amount,
            'target_id': target.get('card_id'),
            'message': f'Healed for {heal_amount}'
        }
    
    def _apply_damage_boost(self, boost: int, caster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply temporary damage boost"""
        return {
            'applied': True,
            'attack_boost': boost,
            'target_id': caster_data.get('card_id'),
            'message': f'Attack increased by {boost}'
        }
    
    def _apply_shield(self, shield_amount: int, caster_data: Dict[str, Any], target_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply shield effect"""
        target = target_data or caster_data
        
        return {
            'applied': True,
            'shield_amount': shield_amount,
            'target_id': target.get('card_id'),
            'message': f'Shield applied ({shield_amount} absorption)'
        }
    
    def _apply_stun(self, duration: int, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply stun effect"""
        if not target_data:
            return {'applied': False, 'message': 'No target specified'}
        
        return {
            'applied': True,
            'stun_duration': duration,
            'target_id': target_data.get('card_id'),
            'message': f'Target stunned for {duration} turn(s)'
        }
    
    def _apply_dodge_chance(self, dodge_percent: int, caster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply dodge chance modifier"""
        return {
            'applied': True,
            'dodge_chance': dodge_percent,
            'target_id': caster_data.get('card_id'),
            'message': f'Dodge chance set to {dodge_percent}%'
        }
    
    def _apply_attack_boost(self, boost: int, caster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply permanent attack boost"""
        return {
            'applied': True,
            'attack_boost': boost,
            'target_id': caster_data.get('card_id'),
            'message': f'Attack permanently increased by {boost}'
        }
    
    def _apply_attack_debuff(self, debuff: int, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply attack debuff to target"""
        if not target_data:
            return {'applied': False, 'message': 'No target specified'}
        
        return {
            'applied': True,
            'attack_debuff': debuff,
            'target_id': target_data.get('card_id'),
            'message': f'Target attack reduced by {debuff}'
        }
    
    def _apply_damage_reduction(self, reduction: int, caster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply damage reduction (armor)"""
        return {
            'applied': True,
            'damage_reduction': reduction,
            'target_id': caster_data.get('card_id'),
            'message': f'Damage reduction increased by {reduction}'
        }
    
    def _format_ability_message(self, ability_text: str, result: Dict[str, Any]) -> str:
        """Format a user-friendly message for ability execution"""
        if not result.get('applied', False):
            return f"❌ {ability_text} failed to activate"
        
        base_message = result.get('message', 'Ability activated')
        return f"✨ **{ability_text}** - {base_message}"
    
    def get_all_abilities(self) -> List[str]:
        """Get list of all available abilities"""
        return list(self._ability_registry.keys())
    
    def get_abilities_by_trigger(self, trigger: str) -> List[str]:
        """Get all abilities that trigger on a specific condition"""
        return [ability for ability, effect in self._ability_registry.items() 
                if effect.condition == trigger]


# Global ability system instance
ability_system = AbilitySystem()
