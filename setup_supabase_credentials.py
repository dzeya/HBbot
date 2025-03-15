#!/usr/bin/env python
"""
Setup script to guide users through configuring Supabase credentials
for the Telegram bot.
"""

import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load any existing environment variables
load_dotenv()

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def print_instruction(msg):
    """Print formatted instruction text"""
    print(f"\n➡️  {msg}")

def get_input(prompt, default=""):
    """Get input with optional default value"""
    if default:
        result = input(f"{prompt} [{default}]: ")
        return result if result else default
    return input(f"{prompt}: ")

def test_credentials(supabase_url, api_key):
    """Test if credentials work correctly"""
    if not supabase_url or not api_key:
        return False, "URL or API key is missing"
    
    try:
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}"
        }
        
        # Test basic connection
        response = requests.get(
            f"{supabase_url}/rest/v1/users?limit=1", 
            headers=headers
        )
        
        if response.status_code == 200:
            return True, "Connection successful"
        elif response.status_code == 401:
            return False, f"Authentication failed: {response.text}"
        elif response.status_code == 404:
            return False, f"Endpoint not found. Check URL: {response.text}"
        else:
            return False, f"Unexpected error (status {response.status_code}): {response.text}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def print_guide_to_find_credentials():
    """Print instructions on where to find credentials"""
    print_header("WHERE TO FIND SUPABASE CREDENTIALS")
    print("""
To find your Supabase credentials:

1. Log in to your Supabase account at https://app.supabase.io
2. Select your project
3. Go to Project Settings (gear icon in the sidebar)
4. Select "API" from the settings menu
5. You'll find:
   - Project URL: Your Supabase URL 
   - Project API keys: 
     - anon public: For client-side code (less permissions)
     - service_role: For server-side code (more permissions, use this one)

Copy these values and enter them below.
""")

def save_to_env_file(env_vars):
    """Save environment variables to .env file"""
    env_path = Path('.env')
    
    # Load existing .env file or create a new one
    if env_path.exists():
        print(f"Updating existing .env file")
        load_dotenv(env_path)
    else:
        print(f"Creating new .env file")
        env_path.touch()
    
    # Write each variable
    for key, value in env_vars.items():
        if value:  # Only write non-empty values
            set_key(str(env_path), key, value)
    
    print(f"✅ Environment variables saved to {env_path.absolute()}")

def main():
    """Main function for setup process"""
    print_header("SUPABASE CREDENTIALS SETUP")
    print("\nThis script will help you set up credentials for connecting to Supabase.")
    
    # Check for existing credentials
    existing_url = os.getenv("SUPABASE_URL")
    existing_anon = os.getenv("SUPABASE_ANON_KEY")
    existing_service = os.getenv("SUPABASE_SERVICE_KEY")
    
    if existing_url or existing_anon or existing_service:
        print("\nExisting Supabase credentials found:")
        if existing_url:
            masked_url = existing_url[:15] + "..." if len(existing_url) > 18 else existing_url
            print(f"- SUPABASE_URL: {masked_url}")
        if existing_anon:
            masked_anon = existing_anon[:10] + "..." + existing_anon[-5:] if len(existing_anon) > 20 else "****"
            print(f"- SUPABASE_ANON_KEY: {masked_anon}")
        if existing_service:
            masked_service = existing_service[:10] + "..." + existing_service[-5:] if len(existing_service) > 20 else "****"
            print(f"- SUPABASE_SERVICE_KEY: {masked_service}")
            
        update = input("\nDo you want to update these credentials? (y/n): ").lower() == 'y'
        if not update:
            print("Keeping existing credentials.")
            
            # Test the existing credentials
            print("\nTesting existing credentials...")
            success, message = test_credentials(existing_url, existing_service or existing_anon)
            
            if success:
                print(f"✅ {message}")
                print("\nYour existing credentials are working correctly.")
                return 0
            else:
                print(f"❌ {message}")
                print("\nYour existing credentials are not working. Please update them.")
    
    # Display guide to find credentials if needed
    if input("\nDo you need instructions on where to find your Supabase credentials? (y/n): ").lower() == 'y':
        print_guide_to_find_credentials()
    
    # Get new credentials
    print_instruction("Enter your Supabase project credentials")
    
    supabase_url = get_input("Supabase URL (e.g., https://yourproject.supabase.co)", existing_url or "")
    supabase_service_key = get_input("Supabase Service Role Key (recommended for bot)", existing_service or "")
    supabase_anon_key = get_input("Supabase Anon Key (optional)", existing_anon or "")
    
    # Make sure at least one key is provided
    if not supabase_service_key and not supabase_anon_key:
        print("\n❌ Error: You must provide at least one API key.")
        return 1
    
    # Test connection with provided credentials
    print("\nTesting connection to Supabase...")
    
    # Prefer service key for testing
    test_key = supabase_service_key or supabase_anon_key
    success, message = test_credentials(supabase_url, test_key)
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        retry = input("\nCredentials test failed. Do you want to save them anyway? (y/n): ").lower() == 'y'
        if not retry:
            print("Setup canceled. Please try again with correct credentials.")
            return 1
    
    # Save credentials to .env file
    env_vars = {
        "SUPABASE_URL": supabase_url,
        "SUPABASE_ANON_KEY": supabase_anon_key,
        "SUPABASE_SERVICE_KEY": supabase_service_key
    }
    
    save_to_env_file(env_vars)
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print("\nYou can now run your bot with the new credentials.")
    print("To use these credentials, make sure to:")
    print("1. Restart your bot: python fixed_bot_rest.py")
    print("2. Test connectivity: python test_supabase_connection.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 