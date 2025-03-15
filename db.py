"""
Database module for the Telegram bot using direct PostgreSQL connection to Supabase.
This module provides functions to interact with the Supabase database.
"""

import os
import logging
import psycopg2
import psycopg2.extras
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Supabase connection details
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

# Direct PostgreSQL connection string
# This can be set in the environment or hardcoded here
PG_CONNECTION_STRING = os.getenv("SUPABASE_POSTGRES_URL", 
    "postgresql://postgres:higmaK-8widka-buhqih@db.foliyzwhhkkfbemiptvp.supabase.co:5432/postgres")

class PostgresConnection:
    """Class to handle PostgreSQL connection to Supabase"""
    
    def __init__(self, connection_string=None):
        self.connection_string = connection_string or PG_CONNECTION_STRING
        self.conn = None
        
    def connect(self):
        """Connect to the PostgreSQL database"""
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(self.connection_string)
                logger.info("Connected to PostgreSQL database")
            return self.conn
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {str(e)}")
            raise
    
    def execute_query(self, query, params=None, fetch=True):
        """Execute a query and return results"""
        try:
            conn = self.connect()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params or {})
                
                if fetch:
                    results = cur.fetchall()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            if conn:
                conn.rollback()
            raise
    
    def insert(self, table, data, returning=True):
        """Insert data into a table"""
        columns = data.keys()
        values = [data[column] for column in columns]
        placeholders = [f"%({column})s" for column in columns]
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        if returning:
            query += " RETURNING *"
        
        try:
            conn = self.connect()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, data)
                
                if returning:
                    results = cur.fetchall()
                    conn.commit()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error inserting data: {str(e)}")
            if conn:
                conn.rollback()
            raise
    
    def update(self, table, data, condition, returning=True):
        """Update data in a table"""
        set_clause = ", ".join([f"{column} = %({column})s" for column in data.keys()])
        where_clause = " AND ".join([f"{key} = %({key})s" for key in condition.keys()])
        
        query = f"""
            UPDATE {table}
            SET {set_clause}
            WHERE {where_clause}
        """
        
        if returning:
            query += " RETURNING *"
        
        params = {**data, **condition}
        
        try:
            conn = self.connect()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                
                if returning:
                    results = cur.fetchall()
                    conn.commit()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error updating data: {str(e)}")
            if conn:
                conn.rollback()
            raise
    
    def upsert(self, table, data, conflict_columns, returning=True):
        """Insert or update data in a table"""
        columns = data.keys()
        values = [data[column] for column in columns]
        placeholders = [f"%({column})s" for column in columns]
        
        update_clause = ", ".join([f"{column} = EXCLUDED.{column}" for column in columns 
                                  if column not in conflict_columns])
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT ({', '.join(conflict_columns)})
            DO UPDATE SET {update_clause}
        """
        
        if returning:
            query += " RETURNING *"
        
        try:
            conn = self.connect()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, data)
                
                if returning:
                    results = cur.fetchall()
                    conn.commit()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error upserting data: {str(e)}")
            if conn:
                conn.rollback()
            raise
    
    def select(self, table, columns="*", condition=None, order_by=None, limit=None):
        """Select data from a table"""
        query = f"SELECT {columns} FROM {table}"
        
        params = {}
        if condition:
            where_clauses = []
            for i, (key, value) in enumerate(condition.items()):
                param_name = f"{key}_{i}"
                where_clauses.append(f"{key} = %({param_name})s")
                params[param_name] = value
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            return self.execute_query(query, params)
        except Exception as e:
            logger.error(f"Error selecting data: {str(e)}")
            raise

# Initialize PostgreSQL connection
db = PostgresConnection()

def test_connection() -> bool:
    """
    Test the database connection
    Returns True if connection is successful, False otherwise
    """
    try:
        # Try to make a simple query
        db.execute_query("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return False

def create_tables() -> bool:
    """
    Create the necessary tables if they don't exist
    Returns True if successful, False otherwise
    """
    try:
        # Check if tables exist by trying to access the users table
        try:
            db.execute_query("SELECT 1 FROM users LIMIT 1")
            logger.info("Tables already exist")
            return True
        except Exception:
            logger.info("Tables don't exist, need to create them")
        
        # Tables need to be created manually via SQL editor
        logger.warning("Tables need to be created manually in Supabase dashboard")
        return False
    except Exception as e:
        logger.error(f"Error checking/creating tables: {str(e)}")
        return False

# User-related operations
def save_user(user_id: int, username: str, first_name: str, last_name: str = None) -> Dict:
    """
    Save or update a user in the database
    """
    try:
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name
        }
        
        # Use upsert to insert if not exists or update if exists
        result = db.upsert("users", user_data, ["user_id"])
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error saving user {user_id}: {str(e)}")
        raise

def get_user(user_id: int) -> Dict:
    """
    Get user information from the database
    """
    try:
        condition = {"user_id": user_id}
        result = db.select("users", condition=condition)
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise

def get_all_users() -> List[Dict]:
    """
    Get all users from the database
    """
    try:
        return db.select("users")
    except Exception as e:
        logger.error(f"Error getting all users: {str(e)}")
        raise

# Message history operations
def save_message(user_id: int, message_text: str, message_id: int, timestamp: str) -> Dict:
    """
    Save a message to the message history
    """
    try:
        message_data = {
            "user_id": user_id,
            "message_text": message_text,
            "message_id": message_id,
            "timestamp": timestamp
        }
        
        result = db.insert("message_history", message_data)
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error saving message for user {user_id}: {str(e)}")
        raise

def get_user_messages(user_id: int, limit: int = 10) -> List[Dict]:
    """
    Get the most recent messages for a specific user
    """
    try:
        condition = {"user_id": user_id}
        result = db.select("message_history", condition=condition, 
                         order_by="timestamp DESC", limit=limit)
        return result
    except Exception as e:
        logger.error(f"Error getting messages for user {user_id}: {str(e)}")
        raise

# Custom user data operations
def save_user_data(user_id: int, data_key: str, data_value: Any) -> Dict:
    """
    Save custom user data (preferences, settings, etc.)
    """
    try:
        # Convert complex objects to JSON
        if isinstance(data_value, (dict, list)):
            data_value = json.dumps(data_value)
            
        user_data = {
            "user_id": user_id,
            "data_key": data_key,
            "data_value": data_value
        }
        
        # Use upsert to insert if not exists or update if exists
        result = db.upsert("user_data", user_data, ["user_id", "data_key"])
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error saving user data for user {user_id}, key {data_key}: {str(e)}")
        raise

def get_user_data(user_id: int, data_key: str) -> Any:
    """
    Get custom user data by key
    """
    try:
        condition = {"user_id": user_id, "data_key": data_key}
        result = db.select("user_data", condition=condition)
        
        if not result:
            return None
            
        data_value = result[0]["data_value"]
        
        # Try to parse JSON if it looks like JSON
        if isinstance(data_value, str) and (data_value.startswith('{') or data_value.startswith('[')):
            try:
                return json.loads(data_value)
            except:
                pass
                
        return data_value
    except Exception as e:
        logger.error(f"Error getting user data for user {user_id}, key {data_key}: {str(e)}")
        raise 