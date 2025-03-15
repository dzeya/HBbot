#!/usr/bin/env python
"""
A script to create the necessary tables and structure in Supabase PostgreSQL database.
This script reads the SQL schema from supabase_setup.sql and executes it.
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Direct PostgreSQL connection string
PG_CONNECTION_STRING = os.getenv("SUPABASE_POSTGRES_URL", 
    "postgresql://postgres:higmaK-8widka-buhqih@db.foliyzwhhkkfbemiptvp.supabase.co:5432/postgres")

def test_connection():
    """Test the connection to the Supabase PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            PG_CONNECTION_STRING,
            connect_timeout=10  # 10 seconds timeout
        )
        logger.info("Successfully connected to the database!")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

def read_sql_file(filename):
    """Read SQL commands from a file"""
    try:
        with open(filename, 'r') as file:
            sql_content = file.read()
            return sql_content
    except Exception as e:
        logger.error(f"Error reading SQL file {filename}: {str(e)}")
        return None

def execute_sql_commands(sql_content):
    """Execute SQL commands from a string"""
    if not sql_content:
        logger.error("No SQL commands to execute")
        return False
    
    # Split SQL commands by semicolon
    sql_commands = sql_content.split(';')
    
    try:
        conn = psycopg2.connect(PG_CONNECTION_STRING)
        with conn.cursor() as cur:
            for command in sql_commands:
                command = command.strip()
                if command:  # Skip empty commands
                    logger.info(f"Executing SQL: {command[:100]}...")  # Log first 100 chars for brevity
                    cur.execute(command)
            conn.commit()
        logger.info("Successfully executed SQL commands!")
        return True
    except Exception as e:
        logger.error(f"Error executing SQL commands: {str(e)}")
        if conn:
            conn.rollback()
        return False

def check_tables_exist():
    """Check if tables already exist in the database"""
    try:
        conn = psycopg2.connect(PG_CONNECTION_STRING)
        with conn.cursor() as cur:
            # Query to list all tables in the public schema
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cur.fetchall()
            
            # Check if our tables exist
            table_names = [t[0] for t in tables]
            expected_tables = ['users', 'message_history', 'user_data']
            
            # Print all tables
            logger.info("Existing tables:")
            for table in table_names:
                logger.info(f"  - {table}")
            
            # Check if all expected tables exist
            all_tables_exist = all(table in table_names for table in expected_tables)
            
            if all_tables_exist:
                logger.info("All required tables already exist!")
            else:
                missing_tables = [t for t in expected_tables if t not in table_names]
                logger.info(f"Missing tables: {missing_tables}")
            
            return all_tables_exist
    except Exception as e:
        logger.error(f"Error checking tables: {str(e)}")
        return False

def main():
    """Main function to set up the database"""
    logger.info("Testing Supabase PostgreSQL connection...")
    
    # Test connection
    if not test_connection():
        logger.error("Connection test failed! Exiting...")
        sys.exit(1)
    
    # Check if tables already exist
    logger.info("Checking if tables already exist...")
    tables_exist = check_tables_exist()
    
    if tables_exist:
        logger.info("Tables already exist. Do you want to recreate them? (y/n)")
        answer = input().strip().lower()
        if answer != 'y':
            logger.info("Exiting without recreating tables.")
            return
    
    # Read SQL file
    logger.info("Reading SQL schema from supabase_setup.sql...")
    sql_content = read_sql_file('supabase_setup.sql')
    
    if not sql_content:
        logger.error("Failed to read SQL schema. Exiting...")
        sys.exit(1)
    
    # Execute SQL commands
    logger.info("Executing SQL commands to create tables...")
    if execute_sql_commands(sql_content):
        logger.info("Successfully set up the database structure!")
    else:
        logger.error("Failed to set up the database structure.")
        sys.exit(1)

if __name__ == "__main__":
    main() 