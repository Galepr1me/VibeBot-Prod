"""
Database Models
Data classes representing database entities
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Dict, Any


@dataclass
class User:
    """User model for XP and level tracking"""
    user_id: int
    xp: int = 0
    level: int = 1
    last_message: Optional[datetime] = None
    total_messages: int = 0
    username: Optional[str] = None
    display_name: Optional[str] = None


@dataclass
class Card:
    """Card model for the trading card game"""
    card_id: int
    name: str
    element: str
    rarity: str
    attack: int
    health: int
    cost: int
    ability: Optional[str] = None
    ascii_art: str = ""


@dataclass
class UserCard:
    """User's card collection entry"""
    user_id: int
    card_id: int
    quantity: int = 1
    obtained_date: Optional[datetime] = None


@dataclass
class DailyReward:
    """Daily reward tracking"""
    user_id: int
    last_claim_date: Optional[date] = None
    current_streak: int = 0
    total_claims: int = 0
    best_streak: int = 0


@dataclass
class UserPack:
    """User's pack token inventory"""
    user_id: int
    pack_type: str = 'standard'
    quantity: int = 0
    obtained_date: Optional[datetime] = None


@dataclass
class Config:
    """Bot configuration entry"""
    key: str
    value: str


@dataclass
class GameData:
    """Legacy game data (for compatibility)"""
    user_id: int
    health: int = 100
    gold: int = 0
    inventory: str = '{}'
    location: str = 'town'
    level: int = 1
    adventure_xp: int = 0
    monsters_defeated: int = 0
    last_daily_quest: Optional[date] = None
    daily_quest_progress: str = '{}'
