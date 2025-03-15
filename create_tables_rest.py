#!/usr/bin/env python
"""
A script to create tables in Supabase using direct REST API calls.
This avoids using the Supabase client library which might have compatibility issues.
"""

import os
import json
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Supabase connection details
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://foliyzwhhkkfbemiptvp.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvbGl5endoaGtrZmJlbWlwdHZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIwNDg1MDksImV4cCI6MjA1NzYyNDUwOX0.SgTPp2Vwzl1wDixlItMt9v7YLwyH7AbZwH8mPB-BkQw")
# Try to get service role key if available (has more permissions)
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", SUPABASE_ANON_KEY)

# Choose the key with highest privileges available
API_KEY = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY != SUPABASE_ANON_KEY else SUPABASE_ANON_KEY

# Log key information (safely)
key_type = "Service Role Key" if SUPABASE_SERVICE_KEY != SUPABASE_ANON_KEY else "Anon Key"
logger.info(f"Using key type: {key_type}")
logger.info(f"SUPABASE_SERVICE_KEY is {'set' if SUPABASE_SERVICE_KEY != SUPABASE_ANON_KEY else 'NOT set'}")
logger.info(f"API Key prefix: {API_KEY[:10]}...")

# REST API endpoints
REST_URL = f"{SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def check_connection():
    """Check if we can connect to Supabase REST API"""
    try:
        # Try to access the health endpoint
        response = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=HEADERS)
        if response.status_code == 200:
            logger.info("Successfully connected to Supabase REST API!")
            return True
        else:
            logger.error(f"Failed to connect to Supabase REST API. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to Supabase REST API: {str(e)}")
        return False

def check_table_exists(table_name):
    """Check if a specific table exists by trying to query it"""
    try:
        # Try to fetch a single row from the table with limit=1
        response = requests.get(
            f"{REST_URL}/{table_name}",
            headers=HEADERS,
            params={"limit": 1}
        )
        
        # If we get a 200 OK, the table exists
        # If we get a 404 Not Found, the table doesn't exist
        # Any other response indicates some other error
        if response.status_code == 200:
            logger.info(f"Table '{table_name}' exists")
            return True
        elif response.status_code == 404:
            logger.info(f"Table '{table_name}' does not exist")
            return False
        else:
            logger.error(f"Error checking table '{table_name}'. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error checking table '{table_name}': {str(e)}")
        return False

def list_tables():
    """Check for the existence of the required tables"""
    tables_to_check = ["users", "message_history", "user_data"]
    existing_tables = []
    
    for table in tables_to_check:
        if check_table_exists(table):
            existing_tables.append(table)
    
    if existing_tables:
        logger.info("Existing tables:")
        for table in existing_tables:
            logger.info(f"  - {table}")
    else:
        logger.info("No required tables found in public schema")
    
    return existing_tables

def create_user(user_id, first_name, username=None, last_name=None):
    """Create a sample user in the users table"""
    try:
        user_data = {
            "user_id": user_id,
            "first_name": first_name,
            "username": username,
            "last_name": last_name
        }
        
        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        response = requests.post(
            f"{REST_URL}/users",
            headers=HEADERS,
            json=user_data
        )
        
        if response.status_code in (201, 200):
            logger.info(f"Successfully created user with ID: {user_id}")
            return True
        else:
            logger.error(f"Failed to create user. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            # If we have RLS policy errors
            if "row-level security policy" in response.text:
                logger.error("You need to use a service role key or update RLS policies")
                logger.error("Add SUPABASE_SERVICE_KEY to your .env file from Supabase Dashboard > Settings > API")
            return False
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return False

def main():
    """Main function to check connection and list tables"""
    logger.info("=== Checking Supabase REST API connection ===")
    
    if not check_connection():
        logger.error("Failed to connect to Supabase REST API. Exiting.")
        return
    
    # List existing tables
    tables = list_tables()
    
    # If users table exists, try to create a sample user
    if "users" in tables:
        logger.info("Attempting to create a sample user...")
        logger.info("Using key type: " + ("Service Role Key" if API_KEY == SUPABASE_SERVICE_KEY else "Anonymous Key"))
        create_user(123456789, "Test", "testuser", "User")
    else:
        logger.info("Users table not found. Please create tables first using the SQL script.")
        logger.info("You can run the SQL script in the Supabase SQL Editor.")

if __name__ == "__main__":
    main() 