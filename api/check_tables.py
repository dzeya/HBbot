#!/usr/bin/env python
"""
Script to check if required Supabase tables exist and create them if they don't.
This helps ensure the bot has the necessary database structure.
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

# Try to use service key if available, otherwise fall back to anon key
if SUPABASE_SERVICE_KEY:
    print("Using service role key for Supabase API")
    API_KEY = SUPABASE_SERVICE_KEY
else:
    print("Using anonymous key for Supabase API")
    API_KEY = SUPABASE_ANON_KEY

# REST API endpoint
REST_URL = f"{SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def check_table_exists(table_name):
    """Check if a table exists in Supabase"""
    try:
        response = requests.get(
            f"{REST_URL}/{table_name}",
            headers=HEADERS,
            params={"limit": 1}
        )
        
        if response.status_code in (200, 201, 204):
            print(f"✅ Table '{table_name}' exists and is accessible")
            return True
        else:
            print(f"❌ Table '{table_name}' might not exist or is not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking table '{table_name}': {str(e)}")
        return False

def list_tables():
    """List all tables in the database using Supabase API"""
    try:
        print("\nAttempting to list all tables in the database...")
        
        # This is a PostgreSQL query to list tables
        # We need to use the PostgreSQL RPC endpoint
        rpc_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/list_tables",
            headers=HEADERS,
            json={}
        )
        
        if rpc_response.status_code in (200, 201, 204):
            try:
                tables = rpc_response.json()
                print(f"Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table}")
                return tables
            except json.JSONDecodeError:
                print("❌ Failed to parse table list response")
                return []
        else:
            print(f"❌ Failed to list tables: {rpc_response.status_code} - {rpc_response.text}")
            return []
    except Exception as e:
        print(f"❌ Error listing tables: {str(e)}")
        return []

def main():
    """Run the table checks"""
    print("=" * 60)
    print("SUPABASE TABLE CHECK")
    print("=" * 60)
    
    # Check if we can connect to Supabase
    print(f"\nConnecting to Supabase at {SUPABASE_URL}")
    try:
        response = requests.get(
            f"{REST_URL}/users",
            headers=HEADERS,
            params={"limit": 1}
        )
        
        if response.status_code in (200, 201, 204):
            print("✅ Successfully connected to Supabase REST API")
        else:
            print(f"❌ Failed to connect to Supabase REST API: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        return
    
    # Check required tables
    required_tables = ["users", "message_history"]
    
    print("\nChecking required tables:")
    all_tables_exist = True
    for table in required_tables:
        if not check_table_exists(table):
            all_tables_exist = False
    
    if all_tables_exist:
        print("\n✅ All required tables exist!")
    else:
        print("\n❌ Some required tables are missing.")
        print("Please run the initialization script to create the tables.")
    
    # Try to list all tables
    list_tables()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 