"""
Database Connection Manager
Handles PostgreSQL and SQLite connections with automatic fallback
"""
import os
import sqlite3
from typing import Optional, Union


class DatabaseManager:
    """Manages database connections with automatic PostgreSQL/SQLite fallback"""
    
    def __init__(self):
        self.db_type = 'sqlite'
        self._test_connection()
    
    def _test_connection(self):
        """Test and determine the best database connection"""
        database_url = os.getenv('DATABASE_URL')
        
        if database_url and database_url.startswith('postgresql://'):
            try:
                import psycopg2
                print("🗄️ Attempting to connect to PostgreSQL database...")
                
                # Test connection
                conn = psycopg2.connect(
                    database_url,
                    connect_timeout=10,
                    sslmode='require'
                )
                conn.close()
                
                print("✅ Successfully connected to PostgreSQL database")
                self.db_type = 'postgresql'
                return
                
            except ImportError:
                print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
                print("🔄 Falling back to SQLite...")
                
            except Exception as e:
                print(f"❌ PostgreSQL connection failed: {e}")
                print("🔄 Falling back to SQLite...")
        
        # Use SQLite as fallback
        db_path = self._get_sqlite_path()
        print(f"🗄️ Using SQLite database at: {db_path}")
        self.db_type = 'sqlite'
    
    def _get_sqlite_path(self) -> str:
        """Get the appropriate SQLite database path for the environment"""
        # Check if we're in a cloud environment
        if os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT'):
            # Use /tmp for cloud hosting (ephemeral but works)
            return '/tmp/bot_data.db'
        else:
            # Use local file for development
            return 'bot_data.db'
    
    def get_connection(self):
        """Get a database connection"""
        if self.db_type == 'postgresql':
            import psycopg2
            database_url = os.getenv('DATABASE_URL')
            return psycopg2.connect(
                database_url,
                connect_timeout=10,
                sslmode='require'
            )
        else:
            return sqlite3.connect(self._get_sqlite_path())
    
    def execute_query(self, query: str, params: Optional[tuple] = None):
        """Execute a database query with automatic parameter conversion"""
        conn = self.get_connection()
        
        try:
            # Convert SQLite placeholders (?) to PostgreSQL placeholders (%s) if needed
            if self.db_type == 'postgresql':
                converted_query = query.replace('?', '%s')
            else:
                converted_query = query
            
            cursor = conn.cursor()
            
            if params:
                cursor.execute(converted_query, params)
            else:
                cursor.execute(converted_query)
            
            # Only try to fetch results for SELECT queries
            query_type = query.strip().upper().split()[0]
            if query_type == 'SELECT':
                result = cursor.fetchone()
                conn.commit()
                return result
            else:
                # For INSERT, UPDATE, DELETE - just commit and return success
                conn.commit()
                return True
            
        except Exception as e:
            print(f"Database error in execute_query: {e}")
            print(f"Query: {converted_query}")
            print(f"Params: {params}")
            raise
        finally:
            conn.close()
    
    def execute_many(self, query: str, params_list: list):
        """Execute a query with multiple parameter sets"""
        conn = self.get_connection()
        
        try:
            # Convert SQLite placeholders (?) to PostgreSQL placeholders (%s) if needed
            if self.db_type == 'postgresql':
                converted_query = query.replace('?', '%s')
            else:
                converted_query = query
            
            cursor = conn.cursor()
            cursor.executemany(converted_query, params_list)
            conn.commit()
            
        except Exception as e:
            print(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> list:
        """Fetch all results from a query"""
        conn = self.get_connection()
        
        try:
            # Convert SQLite placeholders (?) to PostgreSQL placeholders (%s) if needed
            if self.db_type == 'postgresql':
                converted_query = query.replace('?', '%s')
            else:
                converted_query = query
            
            cursor = conn.cursor()
            
            if params:
                cursor.execute(converted_query, params)
            else:
                cursor.execute(converted_query)
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def fetch_one(self, query: str, params: Optional[tuple] = None):
        """Fetch one result from a query"""
        conn = self.get_connection()
        
        try:
            # Convert SQLite placeholders (?) to PostgreSQL placeholders (%s) if needed
            if self.db_type == 'postgresql':
                converted_query = query.replace('?', '%s')
            else:
                converted_query = query
            
            cursor = conn.cursor()
            
            if params:
                cursor.execute(converted_query, params)
            else:
                cursor.execute(converted_query)
            
            result = cursor.fetchone()
            return result  # This will be None if no results, which is expected
            
        except Exception as e:
            print(f"Database error in fetch_one: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            # Don't raise the exception, return None instead for empty results
            return None
        finally:
            conn.close()


# Global database manager instance
db_manager = DatabaseManager()
