"""
Daily Rewards System
Handles daily pack token rewards with streak bonuses
"""
from datetime import datetime, timedelta
from src.database.connection import db_manager
from src.card_game.pack_system import pack_system


class DailyRewards:
    """Manages daily reward system for pack tokens"""
    
    def __init__(self):
        pass
    
    def get_daily_reward_data(self, user_id):
        """Get user's daily reward data"""
        try:
            result = db_manager.fetch_one('SELECT * FROM daily_rewards WHERE user_id = ?', (user_id,))
            if not result:
                # Create new daily reward record
                db_manager.execute_query('INSERT INTO daily_rewards (user_id) VALUES (?)', (user_id,))
                result = (user_id, None, 0, 0, 0)
            return result
        except Exception as e:
            print(f"Error getting daily reward data: {e}")
            return None
    
    def claim_daily_reward(self, user_id):
        """Claim daily reward and return reward info"""
        try:
            # Get current reward data
            reward_data = self.get_daily_reward_data(user_id)
            if not reward_data:
                return None
            
            user_id, last_claim_date, current_streak, total_claims, best_streak = reward_data
            today = datetime.now().date()
            
            # Check if already claimed today
            if last_claim_date and str(last_claim_date) == str(today):
                return {'already_claimed': True, 'streak': current_streak}
            
            # Calculate new streak
            yesterday = today - timedelta(days=1)
            if last_claim_date and str(last_claim_date) == str(yesterday):
                # Continuing streak
                new_streak = current_streak + 1
            elif last_claim_date and str(last_claim_date) < str(yesterday):
                # Streak broken, reset to 1
                new_streak = 1
            else:
                # First claim or continuing from today
                new_streak = current_streak + 1 if current_streak > 0 else 1
            
            # Update best streak
            new_best_streak = max(best_streak, new_streak)
            
            # Generate rewards based on streak
            rewards = self._generate_daily_rewards(new_streak)
            
            # Update database
            db_manager.execute_query('''UPDATE daily_rewards 
                                       SET last_claim_date = ?, current_streak = ?, total_claims = ?, best_streak = ? 
                                       WHERE user_id = ?''',
                                   (today, new_streak, total_claims + 1, new_best_streak, user_id))
            
            # Add pack tokens to user's inventory
            if rewards['pack_tokens'] > 0:
                pack_system.add_pack_tokens(user_id, 'standard', rewards['pack_tokens'])
            
            return {
                'already_claimed': False,
                'streak': new_streak,
                'best_streak': new_best_streak,
                'total_claims': total_claims + 1,
                'rewards': rewards
            }
            
        except Exception as e:
            print(f"Error claiming daily reward: {e}")
            return None
    
    def _generate_daily_rewards(self, streak):
        """Generate daily rewards based on streak - gives pack tokens"""
        rewards = {'pack_tokens': 0, 'bonus': None}
        
        # Base reward: pack tokens
        if streak < 7:
            # Days 1-6: 1 pack token
            rewards['pack_tokens'] = 1
        elif streak == 7:
            # Day 7: 2 pack tokens
            rewards['pack_tokens'] = 2
            rewards['bonus'] = '🎉 Weekly Bonus!'
        elif streak == 30:
            # Day 30: 3 pack tokens
            rewards['pack_tokens'] = 3
            rewards['bonus'] = '🏆 Monthly Legendary!'
        elif streak % 7 == 0:
            # Every 7 days after first week: 2 pack tokens
            rewards['pack_tokens'] = 2
            rewards['bonus'] = f'🔥 {streak} Day Streak!'
        else:
            # Regular days: 1 pack token with streak bonus
            base_tokens = 1
            if streak >= 14:
                # After 2 weeks, small chance for bonus token
                import random
                bonus_chance = min(streak, 30)  # Up to 30% chance
                if random.randint(1, 100) <= bonus_chance:
                    base_tokens += 1
                    rewards['bonus'] = '🎁 Bonus Token!'
            
            rewards['pack_tokens'] = base_tokens
        
        return rewards
