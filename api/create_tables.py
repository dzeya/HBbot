#!/usr/bin/env python
"""
Script to create required Supabase tables for the Telegram bot.
This should be run once to set up the database structure.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase connection details
SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", "https://foliyzwhhkkfbemiptvp.supabase.co"))
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"))
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Service key is required for table creation
if not SUPABASE_SERVICE_KEY:
    print("❌ Error: Service key is required to create tables")
    print("Please set the SUPABASE_SERVICE_KEY environment variable")
    exit(1)

# REST API endpoint
REST_URL = f"{SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def execute_sql(sql_query):
    """Execute a raw SQL query via the Supabase API"""
    try:
        # Use the PostgreSQL RPC endpoint to execute SQL
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/execute_sql",
            headers=HEADERS,
            json={"query": sql_query}
        )
        
        if response.status_code in (200, 201, 204):
            print("✅ SQL executed successfully")
            return True
        else:
            print(f"❌ Error executing SQL: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error executing SQL: {str(e)}")
        return False

def check_table_exists(table_name):
    """Check if a table exists in Supabase"""
    try:
        response = requests.get(
            f"{REST_URL}/{table_name}",
            headers=HEADERS,
            params={"limit": 1}
        )
        
        if response.status_code in (200, 201, 204):
            print(f"✅ Table '{table_name}' already exists")
            return True
        else:
            print(f"Table '{table_name}' does not exist (will create)")
            return False
    except Exception as e:
        print(f"❌ Error checking table '{table_name}': {str(e)}")
        return False

def create_users_table():
    """Create the users table if it doesn't exist"""
    if check_table_exists("users"):
        return True
    
    print("\nCreating 'users' table...")
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        username TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    return execute_sql(sql)

def create_message_history_table():
    """Create the message_history table if it doesn't exist"""
    if check_table_exists("message_history"):
        return True
    
    print("\nCreating 'message_history' table...")
    sql = """
    CREATE TABLE IF NOT EXISTS message_history (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        message_id BIGINT,
        message_text TEXT,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        is_bot BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    CREATE INDEX IF NOT EXISTS idx_message_history_user_id ON message_history(user_id);
    """
    
    return execute_sql(sql)

def setup_rpc_functions():
    """Set up any required RPC functions"""
    print("\nSetting up RPC functions...")
    
    # Function to list tables
    list_tables_sql = """
    CREATE OR REPLACE FUNCTION list_tables()
    RETURNS SETOF text
    LANGUAGE sql
    SECURITY DEFINER
    AS $$
        SELECT tablename FROM pg_tables WHERE schemaname = 'public';
    $$;
    """
    
    # Function to execute SQL (for admin use)
    execute_sql_function = """
    CREATE OR REPLACE FUNCTION execute_sql(query text)
    RETURNS json
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    DECLARE
        result json;
    BEGIN
        EXECUTE query;
        result := json_build_object('success', true);
        RETURN result;
    EXCEPTION WHEN OTHERS THEN
        result := json_build_object('success', false, 'error', SQLERRM);
        RETURN result;
    END;
    $$;
    """
    
    # Execute the SQL
    print("Creating list_tables function...")
    list_tables_result = execute_sql(list_tables_sql)
    
    print("Creating execute_sql function...")
    execute_sql_result = execute_sql(execute_sql_function)
    
    return list_tables_result and execute_sql_result

def main():
    """Run the database initialization"""
    print("=" * 60)
    print("SUPABASE DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Check if we can connect to Supabase
    print(f"\nConnecting to Supabase at {SUPABASE_URL}")
    try:
        response = requests.get(
            f"{REST_URL}/users",
            headers=HEADERS,
            params={"limit": 1}
        )
        
        if response.status_code in (200, 201, 204, 404):
            print("✅ Successfully connected to Supabase REST API")
        else:
            print(f"❌ Failed to connect to Supabase REST API: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        return
    
    # Create tables and functions
    users_created = create_users_table()
    if not users_created:
        print("❌ Failed to create users table. Stopping.")
        return
    
    messages_created = create_message_history_table()
    if not messages_created:
        print("❌ Failed to create message_history table. Stopping.")
        return
    
    rpc_setup = setup_rpc_functions()
    
    # Final status
    if users_created and messages_created and rpc_setup:
        print("\n✅ All database tables and functions created successfully!")
        print("Your bot should now be able to store data in Supabase.")
    else:
        print("\n❌ There were some errors during setup.")
        print("Please check the logs above for details.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 