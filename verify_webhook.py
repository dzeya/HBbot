#!/usr/bin/env python
import os
import requests
import json
import sys

def verify_webhook(token=None):
    """Verify the current webhook configuration and status"""
    if token is None:
        token = os.getenv("TELEGRAM_TOKEN", "8150544076:AAF8GTQ-3CrkOdBvnOmJ85s0hKu0RE4swwE")
    
    print(f"Checking webhook for bot with token: {token[:5]}...{token[-5:]}")
    
    try:
        # Get webhook info
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
        
        if response.status_code != 200:
            print(f"❌ Error getting webhook info. Status code: {response.status_code}")
            print(response.text)
            return False
        
        webhook_info = response.json()
        
        if webhook_info.get("ok"):
            result = webhook_info.get("result", {})
            
            # Print webhook details
            print("\n📡 Webhook Info 📡")
            print(f"URL: {result.get('url', 'Not set')}")
            print(f"Has custom certificate: {result.get('has_custom_certificate', False)}")
            print(f"Pending update count: {result.get('pending_update_count', 0)}")
            
            # Check for errors
            if "last_error_date" in result and "last_error_message" in result:
                error_time = result.get("last_error_date")
                error_msg = result.get("last_error_message")
                print(f"\n⚠️ Last error at timestamp {error_time}:")
                print(f"  {error_msg}")
            
            # Check allowed updates
            allowed_updates = result.get("allowed_updates", [])
            print(f"\nAllowed updates: {', '.join(allowed_updates) if allowed_updates else 'All'}")
            
            # Test if the bot is responsive
            print("\n🔄 Testing bot response...")
            me_response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
            if me_response.status_code == 200 and me_response.json().get("ok"):
                bot_info = me_response.json().get("result", {})
                print(f"✅ Bot is active: @{bot_info.get('username')} ({bot_info.get('first_name')})")
            else:
                print("❌ Bot is not responding to getMe request")
            
            # Overall status
            if "last_error_date" in result:
                print("\n🟡 Webhook is set up but has errors")
                return False
            else:
                print("\n🟢 Webhook is correctly set up and working")
                return True
        else:
            print(f"❌ Error in API response: {webhook_info}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during verification: {e}")
        return False

if __name__ == "__main__":
    # Use token from command line if provided
    token = sys.argv[1] if len(sys.argv) > 1 else None
    verify_webhook(token) 