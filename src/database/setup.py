"""
Database Setup and Initialization
Handles table creation, migrations, and initial data population
"""
from .connection import db_manager
from ..card_game.card_library import CardLibrary


class DatabaseSetup:
    """Handles database initialization and migrations"""
    
    def __init__(self):
        self.db = db_manager
        self.card_library = CardLibrary()
    
    def initialize_database(self):
        """Initialize all database tables and populate initial data"""
        print("🔧 Initializing database...")
        
        self._create_tables()
        self._run_migrations()
        self._populate_initial_data()
        
        print("✅ Database initialization complete")
    
    def _create_tables(self):
        """Create all necessary database tables"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.db.db_type == 'postgresql':
                self._create_postgresql_tables(cursor)
            else:
                self._create_sqlite_tables(cursor)
            
            conn.commit()
            print("✅ Database tables created")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise
        finally:
            conn.close()
    
    def _create_postgresql_tables(self, cursor):
        """Create PostgreSQL tables"""
        # Users table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                         (user_id BIGINT PRIMARY KEY, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, 
                          last_message TIMESTAMP, total_messages INTEGER DEFAULT 0, 
                          username TEXT, display_name TEXT)''')
        
        # Config table
        cursor.execute('''CREATE TABLE IF NOT EXISTS config
                         (key TEXT PRIMARY KEY, value TEXT)''')
        
        # Game data table (legacy compatibility)
        cursor.execute('''CREATE TABLE IF NOT EXISTS game_data
                         (user_id BIGINT PRIMARY KEY, health INTEGER DEFAULT 100, 
                          gold INTEGER DEFAULT 0, inventory TEXT DEFAULT '{}', 
                          location TEXT DEFAULT 'town', level INTEGER DEFAULT 1,
                          adventure_xp INTEGER DEFAULT 0, monsters_defeated INTEGER DEFAULT 0,
                          last_daily_quest DATE, daily_quest_progress TEXT DEFAULT '{}')''')
        
        # Database version tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS db_version
                         (version INTEGER PRIMARY KEY)''')
        
        # Card Game Tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS cards
                         (card_id SERIAL PRIMARY KEY, name TEXT NOT NULL, element TEXT NOT NULL,
                          rarity TEXT NOT NULL, attack INTEGER NOT NULL, health INTEGER NOT NULL,
                          cost INTEGER NOT NULL, ability TEXT, ascii_art TEXT NOT NULL)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_cards
                         (user_id BIGINT NOT NULL, card_id INTEGER NOT NULL, quantity INTEGER DEFAULT 1,
                          obtained_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          PRIMARY KEY (user_id, card_id),
                          FOREIGN KEY (card_id) REFERENCES cards(card_id))''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_decks
                         (deck_id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, deck_name TEXT DEFAULT 'Main Deck',
                          card_ids JSON NOT NULL, is_active BOOLEAN DEFAULT FALSE,
                          created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_rewards
                         (user_id BIGINT PRIMARY KEY, last_claim_date DATE, 
                          current_streak INTEGER DEFAULT 0, total_claims INTEGER DEFAULT 0,
                          best_streak INTEGER DEFAULT 0)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_packs
                         (user_id BIGINT NOT NULL, pack_type TEXT DEFAULT 'standard', 
                          quantity INTEGER DEFAULT 0, obtained_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          PRIMARY KEY (user_id, pack_type))''')
    
    def _create_sqlite_tables(self, cursor):
        """Create SQLite tables"""
        # Users table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                         (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, 
                          last_message TIMESTAMP, total_messages INTEGER DEFAULT 0, 
                          username TEXT, display_name TEXT)''')
        
        # Config table
        cursor.execute('''CREATE TABLE IF NOT EXISTS config
                         (key TEXT PRIMARY KEY, value TEXT)''')
        
        # Game data table (legacy compatibility)
        cursor.execute('''CREATE TABLE IF NOT EXISTS game_data
                         (user_id INTEGER PRIMARY KEY, health INTEGER DEFAULT 100, 
                          gold INTEGER DEFAULT 0, inventory TEXT DEFAULT '{}', 
                          location TEXT DEFAULT 'town', level INTEGER DEFAULT 1,
                          adventure_xp INTEGER DEFAULT 0, monsters_defeated INTEGER DEFAULT 0,
                          last_daily_quest DATE, daily_quest_progress TEXT DEFAULT '{}')''')
        
        # Database version tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS db_version
                         (version INTEGER PRIMARY KEY)''')
        
        # Card Game Tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS cards
                         (card_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, element TEXT NOT NULL,
                          rarity TEXT NOT NULL, attack INTEGER NOT NULL, health INTEGER NOT NULL,
                          cost INTEGER NOT NULL, ability TEXT, ascii_art TEXT NOT NULL)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_cards
                         (user_id INTEGER NOT NULL, card_id INTEGER NOT NULL, quantity INTEGER DEFAULT 1,
                          obtained_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          PRIMARY KEY (user_id, card_id),
                          FOREIGN KEY (card_id) REFERENCES cards(card_id))''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_decks
                         (deck_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, deck_name TEXT DEFAULT 'Main Deck',
                          card_ids TEXT NOT NULL, is_active INTEGER DEFAULT 0,
                          created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_rewards
                         (user_id INTEGER PRIMARY KEY, last_claim_date DATE, 
                          current_streak INTEGER DEFAULT 0, total_claims INTEGER DEFAULT 0,
                          best_streak INTEGER DEFAULT 0)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_packs
                         (user_id INTEGER NOT NULL, pack_type TEXT DEFAULT 'standard', 
                          quantity INTEGER DEFAULT 0, obtained_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          PRIMARY KEY (user_id, pack_type))''')
    
    def _run_migrations(self):
        """Run database migrations"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current version
            try:
                cursor.execute('SELECT version FROM db_version ORDER BY version DESC LIMIT 1')
                current_version = cursor.fetchone()
                current_version = current_version[0] if current_version else 0
            except:
                current_version = 0
            
            # Run migrations based on database type
            if self.db.db_type == 'postgresql':
                self._run_postgresql_migrations(cursor, current_version)
            else:
                self._run_sqlite_migrations(cursor, current_version)
            
            conn.commit()
            print(f"✅ Database migrations complete (version {current_version})")
            
        except Exception as e:
            print(f"❌ Error running migrations: {e}")
            raise
        finally:
            conn.close()
    
    def _run_postgresql_migrations(self, cursor, current_version):
        """Run PostgreSQL-specific migrations"""
        if current_version < 2:
            # Migration 1: Add adventure columns
            try:
                cursor.execute('ALTER TABLE game_data ADD COLUMN IF NOT EXISTS adventure_xp INTEGER DEFAULT 0')
                cursor.execute('ALTER TABLE game_data ADD COLUMN IF NOT EXISTS monsters_defeated INTEGER DEFAULT 0')
                cursor.execute('ALTER TABLE game_data ADD COLUMN IF NOT EXISTS last_daily_quest DATE')
                cursor.execute('ALTER TABLE game_data ADD COLUMN IF NOT EXISTS daily_quest_progress TEXT DEFAULT \'{}\'')
                cursor.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT')
                cursor.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT')
            except Exception as e:
                print(f"Migration note: {e}")
            
            cursor.execute('INSERT INTO db_version (version) VALUES (%s) ON CONFLICT (version) DO NOTHING', (2,))
        
        if current_version < 3:
            # Migration 2: Populate card library
            try:
                cursor.execute('SELECT COUNT(*) FROM cards')
                card_count = cursor.fetchone()[0]
                if card_count == 0:
                    print("🃏 Populating card library...")
                    self._populate_card_library_postgresql(cursor)
            except Exception as e:
                print(f"Card migration note: {e}")
            
            cursor.execute('INSERT INTO db_version (version) VALUES (%s) ON CONFLICT (version) DO NOTHING', (3,))
    
    def _run_sqlite_migrations(self, cursor, current_version):
        """Run SQLite-specific migrations"""
        if current_version < 1:
            # Migration 1: Add adventure columns
            try:
                cursor.execute('ALTER TABLE game_data ADD COLUMN adventure_xp INTEGER DEFAULT 0')
            except:
                pass
            try:
                cursor.execute('ALTER TABLE game_data ADD COLUMN monsters_defeated INTEGER DEFAULT 0')
            except:
                pass
            try:
                cursor.execute('ALTER TABLE game_data ADD COLUMN last_daily_quest DATE')
            except:
                pass
            try:
                cursor.execute('ALTER TABLE game_data ADD COLUMN daily_quest_progress TEXT DEFAULT "{}"')
            except:
                pass
            
            cursor.execute('INSERT OR REPLACE INTO db_version (version) VALUES (1)')
        
        if current_version < 2:
            # Migration 2: Add user columns
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN username TEXT')
            except:
                pass
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN display_name TEXT')
            except:
                pass
            
            cursor.execute('INSERT OR REPLACE INTO db_version (version) VALUES (2)')
        
        if current_version < 3:
            # Migration 3: Populate card library
            try:
                cursor.execute('SELECT COUNT(*) FROM cards')
                card_count = cursor.fetchone()[0]
                if card_count == 0:
                    print("🃏 Populating card library...")
                    self._populate_card_library_sqlite(cursor)
            except Exception as e:
                print(f"Card migration note: {e}")
            
            cursor.execute('INSERT OR REPLACE INTO db_version (version) VALUES (3)')
    
    def _populate_initial_data(self):
        """Populate initial configuration data"""
        default_config = {
            'xp_per_message': '15',
            'xp_cooldown': '60',
            'level_multiplier': '100',
            'level_scaling_factor': '1.2',
            'xp_channel': 'None',
            'game_enabled': 'True',
            'welcome_message': 'Welcome to the server, {user}!',
            'level_up_message': 'Congratulations {user}! You reached level {level}!',
            'rare_event_chance': '5',
            'legendary_event_chance': '1',
            'daily_quests_enabled': 'True',
            'adventure_leaderboard_enabled': 'True',
            'boss_encounter_chance': '3'
        }
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            for key, value in default_config.items():
                if self.db.db_type == 'postgresql':
                    cursor.execute('INSERT INTO config (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING', (key, value))
                else:
                    cursor.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)', (key, value))
            
            conn.commit()
            print("✅ Default configuration populated")
            
        except Exception as e:
            print(f"❌ Error populating config: {e}")
            raise
        finally:
            conn.close()
    
    def _populate_card_library_postgresql(self, cursor):
        """Populate the cards table with the initial card library for PostgreSQL"""
        for card in self.card_library.get_all_cards():
            cursor.execute('''INSERT INTO cards (name, element, rarity, attack, health, cost, ability, ascii_art) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                          (card['name'], card['element'], card['rarity'], card['attack'], 
                           card['health'], card['cost'], card['ability'], card['ascii']))
    
    def _populate_card_library_sqlite(self, cursor):
        """Populate the cards table with the initial card library for SQLite"""
        for card in self.card_library.get_all_cards():
            cursor.execute('''INSERT INTO cards (name, element, rarity, attack, health, cost, ability, ascii_art) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (card['name'], card['element'], card['rarity'], card['attack'], 
                           card['health'], card['cost'], card['ability'], card['ascii']))


# Global database setup instance
db_setup = DatabaseSetup()
