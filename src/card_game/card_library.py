"""
Card Library
Contains all card definitions and game mechanics
"""
from typing import List, Dict, Any


class CardLibrary:
    """Manages the complete card library and game mechanics"""
    
    def __init__(self):
        # Card elements and their advantages
        self.elements = {
            'fire': {'beats': 'earth', 'color': 0xff4500, 'emoji': '🔥'},
            'water': {'beats': 'fire', 'color': 0x1e90ff, 'emoji': '💧'},
            'earth': {'beats': 'air', 'color': 0x8b4513, 'emoji': '🌍'},
            'air': {'beats': 'water', 'color': 0x87ceeb, 'emoji': '💨'},
            'light': {'beats': 'dark', 'color': 0xffd700, 'emoji': '✨'},
            'dark': {'beats': 'light', 'color': 0x4b0082, 'emoji': '🌑'}
        }
        
        # Rarity system
        self.rarities = {
            'common': {'color': 0x808080, 'drop_rate': 60, 'border': '─'},
            'rare': {'color': 0x0080ff, 'drop_rate': 25, 'border': '═'},
            'epic': {'color': 0x8000ff, 'drop_rate': 10, 'border': '━'},
            'legendary': {'color': 0xff8000, 'drop_rate': 4, 'border': '█'},
            'mythic': {'color': 0xff0080, 'drop_rate': 1, 'border': '▓'}
        }
        
        # Initialize card library
        self._card_library = self._create_card_library()
    
    def get_all_cards(self) -> List[Dict[str, Any]]:
        """Get all cards in the library"""
        return self._card_library
    
    def get_cards_by_rarity(self, rarity: str) -> List[Dict[str, Any]]:
        """Get all cards of a specific rarity"""
        return [card for card in self._card_library if card['rarity'] == rarity]
    
    def get_card_by_name(self, name: str) -> Dict[str, Any] | None:
        """Get a specific card by name"""
        for card in self._card_library:
            if card['name'].lower() == name.lower():
                return card
        return None
    
    def _create_card_library(self) -> List[Dict[str, Any]]:
        """Create the complete card library"""
        cards = []
        
        # Common Cards (28 total)
        common_cards = [
            # Fire Commons (4 total)
            {'name': 'Fire Sprite', 'element': 'fire', 'rarity': 'common', 'attack': 2, 'health': 1, 'cost': 1,
             'ascii': ' /^\\\n( o )\n \\v/', 'ability': 'None'},
            {'name': 'Flame Imp', 'element': 'fire', 'rarity': 'common', 'attack': 3, 'health': 2, 'cost': 2,
             'ascii': ' /^^^\\\n( >o< )\n  \\_/', 'ability': 'None'},
            {'name': 'Ember Scout', 'element': 'fire', 'rarity': 'common', 'attack': 1, 'health': 2, 'cost': 1,
             'ascii': '  /\\\n ( * )\n  \\_/', 'ability': 'Rush: Can attack immediately'},
            {'name': 'Cinder Beast', 'element': 'fire', 'rarity': 'common', 'attack': 2, 'health': 3, 'cost': 3,
             'ascii': ' /^^^\\\n( >=< )\n  \\_/', 'ability': 'Burn: Deal 1 damage when played'},
            
            # Water Commons (4 total)
            {'name': 'Water Drop', 'element': 'water', 'rarity': 'common', 'attack': 1, 'health': 3, 'cost': 1,
             'ascii': '  ~\n (~)\n  ~', 'ability': 'None'},
            {'name': 'Stream Fish', 'element': 'water', 'rarity': 'common', 'attack': 2, 'health': 2, 'cost': 2,
             'ascii': ' ><>\n~~~~\n ><>', 'ability': 'None'},
            {'name': 'Tide Caller', 'element': 'water', 'rarity': 'common', 'attack': 1, 'health': 4, 'cost': 2,
             'ascii': '  ~~~\n ( o )\n  ~~~', 'ability': 'Heal: Restore 1 health when played'},
            {'name': 'Coral Guard', 'element': 'water', 'rarity': 'common', 'attack': 0, 'health': 5, 'cost': 2,
             'ascii': ' ^^^^^\n^  o  ^\n ^^^^^', 'ability': 'Taunt: Enemies must attack this first'},
            
            # Earth Commons (4 total)
            {'name': 'Rock Pebble', 'element': 'earth', 'rarity': 'common', 'attack': 1, 'health': 4, 'cost': 2,
             'ascii': ' ###\n#####\n ###', 'ability': 'None'},
            {'name': 'Mud Golem', 'element': 'earth', 'rarity': 'common', 'attack': 3, 'health': 3, 'cost': 3,
             'ascii': ' ###\n# O #\n ###', 'ability': 'None'},
            {'name': 'Stone Beetle', 'element': 'earth', 'rarity': 'common', 'attack': 2, 'health': 1, 'cost': 1,
             'ascii': ' /###\\\n( o o )\n \\___/', 'ability': 'Armor: Reduce damage by 1'},
            {'name': 'Crystal Miner', 'element': 'earth', 'rarity': 'common', 'attack': 1, 'health': 3, 'cost': 2,
             'ascii': '  ###\n # o #\n  ###', 'ability': 'Draw: Draw a card when played'},
            
            # Air Commons (4 total)
            {'name': 'Wind Wisp', 'element': 'air', 'rarity': 'common', 'attack': 3, 'health': 1, 'cost': 1,
             'ascii': ' ~~~\n~ o ~\n ~~~', 'ability': 'None'},
            {'name': 'Cloud Sprite', 'element': 'air', 'rarity': 'common', 'attack': 2, 'health': 3, 'cost': 2,
             'ascii': ' ~~~~\n(  o )\n ~~~~', 'ability': 'None'},
            {'name': 'Gust Rider', 'element': 'air', 'rarity': 'common', 'attack': 2, 'health': 2, 'cost': 2,
             'ascii': '  /\\\n ( o )\n  \\_/', 'ability': 'Flying: Cannot be blocked'},
            {'name': 'Zephyr Dancer', 'element': 'air', 'rarity': 'common', 'attack': 1, 'health': 1, 'cost': 1,
             'ascii': '   ^\n  /|\\\n ( o )', 'ability': 'Evasion: 50% chance to dodge attacks'},
            
            # Light Commons (6 total)
            {'name': 'Light Spark', 'element': 'light', 'rarity': 'common', 'attack': 1, 'health': 1, 'cost': 1,
             'ascii': '   *\n  /|\\\n   o', 'ability': 'Illuminate: Reveal enemy hand'},
            {'name': 'Dawn Wisp', 'element': 'light', 'rarity': 'common', 'attack': 2, 'health': 2, 'cost': 2,
             'ascii': '  ***\n ( o )\n  ***', 'ability': 'Purify: Remove negative effects'},
            {'name': 'Radiant Orb', 'element': 'light', 'rarity': 'common', 'attack': 0, 'health': 3, 'cost': 1,
             'ascii': '  ***\n * O *\n  ***', 'ability': 'Shield: Absorb next attack'},
            {'name': 'Holy Priest', 'element': 'light', 'rarity': 'common', 'attack': 1, 'health': 3, 'cost': 2,
             'ascii': '   *\n  /|\\\n ( o )\n  /|\\', 'ability': 'Heal: Restore 1 health to ally'},
            {'name': 'Divine Messenger', 'element': 'light', 'rarity': 'common', 'attack': 2, 'health': 1, 'cost': 1,
             'ascii': '  ***\n * /|\\ *\n ( o )', 'ability': 'Flying: Cannot be blocked'},
            {'name': 'Sacred Flame', 'element': 'light', 'rarity': 'common', 'attack': 3, 'health': 1, 'cost': 2,
             'ascii': '   *\n  ***\n   *', 'ability': 'Burn: Deal 1 damage to enemy'},
            
            # Dark Commons (6 total)
            {'name': 'Shadow Wisp', 'element': 'dark', 'rarity': 'common', 'attack': 2, 'health': 1, 'cost': 1,
             'ascii': '  ...\n ( x )\n  ...', 'ability': 'Stealth: Cannot be targeted'},
            {'name': 'Void Spawn', 'element': 'dark', 'rarity': 'common', 'attack': 1, 'health': 2, 'cost': 1,
             'ascii': '  ###\n # x #\n  ###', 'ability': 'Drain: Heal when dealing damage'},
            {'name': 'Night Crawler', 'element': 'dark', 'rarity': 'common', 'attack': 3, 'health': 1, 'cost': 2,
             'ascii': ' /xxx\\\n( x x )\n \\___/', 'ability': 'Ambush: +2 attack if enemy damaged'},
            {'name': 'Dark Cultist', 'element': 'dark', 'rarity': 'common', 'attack': 2, 'health': 2, 'cost': 2,
             'ascii': '  xxx\n ( x )\n  /|\\', 'ability': 'Sacrifice: Destroy to draw card'},
            {'name': 'Shade Walker', 'element': 'dark', 'rarity': 'common', 'attack': 1, 'health': 3, 'cost': 2,
             'ascii': '  ...\n . x .\n  /|\\', 'ability': 'Phase: 25% dodge chance'},
            {'name': 'Cursed Spirit', 'element': 'dark', 'rarity': 'common', 'attack': 2, 'health': 1, 'cost': 1,
             'ascii': '  xxx\n ( x )\n  xxx', 'ability': 'Curse: Reduce enemy attack by 1'},
        ]
        
        # Rare Cards (18 total - 3 per element)
        rare_cards = [
            # Fire Rares (3 total)
            {'name': 'Fire Wolf', 'element': 'fire', 'rarity': 'rare', 'attack': 4, 'health': 3, 'cost': 3,
             'ascii': '  /\\_/\\\n ( o.o )\n  > ^ <', 'ability': 'Burn: Deal 1 extra damage'},
            {'name': 'Lava Elemental', 'element': 'fire', 'rarity': 'rare', 'attack': 3, 'health': 4, 'cost': 4,
             'ascii': '  /^^^\\\n ( >=< )\n  \\___/', 'ability': 'Molten: Damage attackers'},
            {'name': 'Flame Phoenix', 'element': 'fire', 'rarity': 'rare', 'attack': 2, 'health': 2, 'cost': 3,
             'ascii': '   /\\\n  /  \\\n ( ** )\n  \\__/', 'ability': 'Rebirth: Return when destroyed'},
            
            # Water Rares (3 total)
            {'name': 'Ice Mage', 'element': 'water', 'rarity': 'rare', 'attack': 3, 'health': 4, 'cost': 4,
             'ascii': '   /|\\\n  /*|*\\\n ( o o )', 'ability': 'Freeze: Skip enemy turn'},
            {'name': 'Tidal Kraken', 'element': 'water', 'rarity': 'rare', 'attack': 5, 'health': 3, 'cost': 4,
             'ascii': '  ~~~~~\n ~(o o)~\n~  \\_/  ~\n ~~~~~', 'ability': 'Tentacles: Attack all enemies'},
            {'name': 'Frost Guardian', 'element': 'water', 'rarity': 'rare', 'attack': 1, 'health': 6, 'cost': 4,
             'ascii': '  ^^^^^\n ^ o o ^\n^  _  ^\n ^^^^^', 'ability': 'Ice Shield: Reflect damage'},
            
            # Earth Rares (3 total)
            {'name': 'Stone Giant', 'element': 'earth', 'rarity': 'rare', 'attack': 5, 'health': 5, 'cost': 5,
             'ascii': '  #####\n #  O  #\n #  _  #\n  #####', 'ability': 'Armor: Reduce damage by 1'},
            {'name': 'Crystal Golem', 'element': 'earth', 'rarity': 'rare', 'attack': 4, 'health': 4, 'cost': 4,
             'ascii': '  #***#\n # * * #\n #  _  #\n  #####', 'ability': 'Reflect: Return spell damage'},
            {'name': 'Mountain Troll', 'element': 'earth', 'rarity': 'rare', 'attack': 6, 'health': 2, 'cost': 4,
             'ascii': '  #####\n # >O< #\n #  ^  #\n  #####', 'ability': 'Rage: +1 attack when damaged'},
            
            # Air Rares (3 total)
            {'name': 'Storm Eagle', 'element': 'air', 'rarity': 'rare', 'attack': 4, 'health': 2, 'cost': 3,
             'ascii': '  \\   /\n   \\_/\n  (o o)\n   ^^^', 'ability': 'Swift: Attack first'},
            {'name': 'Lightning Bird', 'element': 'air', 'rarity': 'rare', 'attack': 3, 'health': 3, 'cost': 3,
             'ascii': '   /\\\n  /  \\\n ( ^^ )\n  \\__/', 'ability': 'Shock: Stun target'},
            {'name': 'Wind Dancer', 'element': 'air', 'rarity': 'rare', 'attack': 2, 'health': 4, 'cost': 3,
             'ascii': '   ^\n  /|\\\n ( o )\n  /|\\', 'ability': 'Dodge: 75% evasion chance'},
            
            # Light Rares (3 total)
            {'name': 'Light Fairy', 'element': 'light', 'rarity': 'rare', 'attack': 2, 'health': 3, 'cost': 3,
             'ascii': '   *\n  /|\\\n ( o )\n  /|\\', 'ability': 'Heal: Restore 2 health'},
            {'name': 'Solar Angel', 'element': 'light', 'rarity': 'rare', 'attack': 4, 'health': 4, 'cost': 5,
             'ascii': '   ***\n  /|\\\n ( o )\n  /|\\', 'ability': 'Blessing: Boost ally stats'},
            {'name': 'Radiant Knight', 'element': 'light', 'rarity': 'rare', 'attack': 3, 'health': 5, 'cost': 4,
             'ascii': '   /|\\\n  [***]\n ( o )\n  /|\\', 'ability': 'Protection: Shield allies'},
            
            # Dark Rares (3 total)
            {'name': 'Shadow Cat', 'element': 'dark', 'rarity': 'rare', 'attack': 3, 'health': 2, 'cost': 2,
             'ascii': '  /\\_/\\\n ( -.o )\n  > ^ <', 'ability': 'Stealth: 50% dodge chance'},
            {'name': 'Void Walker', 'element': 'dark', 'rarity': 'rare', 'attack': 4, 'health': 3, 'cost': 4,
             'ascii': '  .....\n . x x .\n .  _  .\n  .....', 'ability': 'Phase: Cannot be blocked'},
            {'name': 'Night Terror', 'element': 'dark', 'rarity': 'rare', 'attack': 5, 'health': 1, 'cost': 3,
             'ascii': '  xxxxx\n x >o< x\n x  ^  x\n  xxxxx', 'ability': 'Fear: Reduce enemy attack'},
        ]
        
        # Epic Cards (12 total - 2 per element)
        epic_cards = [
            # Fire Epics (2 total)
            {'name': 'Fire Dragon', 'element': 'fire', 'rarity': 'epic', 'attack': 6, 'health': 5, 'cost': 6,
             'ascii': '   /\\_/\\\n  /  o  \\\n |  ___  |\n  \\  ^  /\n   \\___/', 'ability': 'Inferno: Deal damage to all enemies'},
            {'name': 'Inferno Beast', 'element': 'fire', 'rarity': 'epic', 'attack': 7, 'health': 4, 'cost': 6,
             'ascii': '  /^^^^^\\\n ( >===< )\n  \\  ^  /\n   \\___/', 'ability': 'Immolate: Destroy to deal 5 damage'},
            
            # Water Epics (2 total)
            {'name': 'Water Leviathan', 'element': 'water', 'rarity': 'epic', 'attack': 5, 'health': 7, 'cost': 7,
             'ascii': '  ~~~~~~~\n ~  o o  ~\n~   ___   ~\n ~  \\_/  ~\n  ~~~~~~~', 'ability': 'Tsunami: Heal all allies'},
            {'name': 'Ocean Master', 'element': 'water', 'rarity': 'epic', 'attack': 4, 'health': 8, 'cost': 7,
             'ascii': '  ~~~~~~~\n ~ /|\\ ~\n~  o o  ~\n ~  _  ~\n  ~~~~~~~', 'ability': 'Tidal Wave: Return all cards to hand'},
            
            # Earth Epics (2 total)
            {'name': 'Earth Titan', 'element': 'earth', 'rarity': 'epic', 'attack': 7, 'health': 6, 'cost': 7,
             'ascii': '  #######\n # O   O #\n #   _   #\n #  \\_/  #\n  #######', 'ability': 'Earthquake: Stun all enemies'},
            {'name': 'Stone Warden', 'element': 'earth', 'rarity': 'epic', 'attack': 5, 'health': 9, 'cost': 8,
             'ascii': '  #######\n # [***] #\n #  O O  #\n #   _   #\n  #######', 'ability': 'Fortress: Cannot be targeted by spells'},
            
            # Air Epics (2 total)
            {'name': 'Sky Lord', 'element': 'air', 'rarity': 'epic', 'attack': 6, 'health': 4, 'cost': 5,
             'ascii': '    /|\\\n   / | \\\n  |  *  |\n   \\ | /\n    \\|/', 'ability': 'Lightning: Deal 3 damage to any target'},
            {'name': 'Storm Caller', 'element': 'air', 'rarity': 'epic', 'attack': 5, 'health': 5, 'cost': 6,
             'ascii': '   ^^^^^\n  ^ /|\\ ^\n ^  o o  ^\n  ^  _  ^\n   ^^^^^', 'ability': 'Tempest: All creatures gain flying'},
            
            # Light Epics (2 total)
            {'name': 'Dawn Bringer', 'element': 'light', 'rarity': 'epic', 'attack': 6, 'health': 6, 'cost': 7,
             'ascii': '   *****\n  * /|\\ *\n * ( o ) *\n  * /|\\ *\n   *****', 'ability': 'Radiance: Heal all allies to full'},
            {'name': 'Light Avatar', 'element': 'light', 'rarity': 'epic', 'attack': 5, 'health': 7, 'cost': 6,
             'ascii': '   *****\n  *  |  *\n * (***) *\n  * /|\\ *\n   *****', 'ability': 'Divine Shield: Immune to damage for 1 turn'},
            
            # Dark Epics (2 total)
            {'name': 'Shadow Assassin', 'element': 'dark', 'rarity': 'epic', 'attack': 8, 'health': 3, 'cost': 6,
             'ascii': '  .......\n . /xxx\\ .\n. ( x x ) .\n . \\___/ .\n  .......', 'ability': 'Backstab: Deal double damage to damaged enemies'},
            {'name': 'Void Lord', 'element': 'dark', 'rarity': 'epic', 'attack': 6, 'health': 5, 'cost': 7,
             'ascii': '  xxxxxxx\n x  ___  x\n x (o o) x\n x  \\_/  x\n  xxxxxxx', 'ability': 'Consume: Destroy ally to gain +3/+3'},
        ]
        
        # Legendary Cards (6 total - 1 per element)
        legendary_cards = [
            {'name': 'Phoenix God', 'element': 'light', 'rarity': 'legendary', 'attack': 8, 'health': 8, 'cost': 9,
             'ascii': '     /|\\\n    / | \\\n   |  *  |\n  /|\\ | /|\\\n / | \\|/ | \\\n|  |  *  |  |\n \\ |     | /\n  \\|_____|/', 'ability': 'Rebirth: Return to hand when destroyed'},
            {'name': 'Void Demon', 'element': 'dark', 'rarity': 'legendary', 'attack': 9, 'health': 6, 'cost': 8,
             'ascii': '   #######\n  # \\   / #\n #   \\_/   #\n#  (o) (o)  #\n #    ^    #\n  # \\_-_/ #\n   #######', 'ability': 'Devour: Destroy any card and gain its stats'},
            {'name': 'Eternal Flame', 'element': 'fire', 'rarity': 'legendary', 'attack': 10, 'health': 5, 'cost': 9,
             'ascii': '   /^^^^^\\\n  / ===== \\\n | (  *  ) |\n  \\ ===== /\n   \\^^^^^/', 'ability': 'Immortal: Cannot be destroyed by spells'},
            {'name': 'Primordial Sea', 'element': 'water', 'rarity': 'legendary', 'attack': 6, 'health': 10, 'cost': 10,
             'ascii': '  ~~~~~~~~~\n ~ ~~~~~~~ ~\n~  ( *** )  ~\n ~ ~~~~~~~ ~\n  ~~~~~~~~~', 'ability': 'Flood: Reset all cards to base stats'},
            {'name': 'World Tree', 'element': 'earth', 'rarity': 'legendary', 'attack': 5, 'health': 12, 'cost': 10,
             'ascii': '    #####\n   # *** #\n  #  ***  #\n #   ***   #\n#    ***    #\n     ###', 'ability': 'Growth: Gain +1/+1 each turn'},
            {'name': 'Sky Sovereign', 'element': 'air', 'rarity': 'legendary', 'attack': 8, 'health': 7, 'cost': 9,
             'ascii': '   ^^^^^^^\n  ^ ***** ^\n ^ ( *** ) ^\n  ^ ***** ^\n   ^^^^^^^', 'ability': 'Dominion: Control all flying creatures'},
        ]
        
        # Combine all cards
        cards.extend(common_cards)
        cards.extend(rare_cards) 
        cards.extend(epic_cards)
        cards.extend(legendary_cards)
        
        return cards
