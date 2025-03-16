#!/usr/bin/env python
import os
import sys
import requests
import json

def setup_webhook():
    """
    Set up the webhook for a Telegram bot to point to the fixed API endpoint
    """
    # Get environment variables
    token = os.getenv("TELEGRAM_TOKEN", "8150544076:AAF8GTQ-3CrkOdBvnOmJ85s0hKu0RE4swwE")
    webhook_url = os.getenv("WEBHOOK_URL", "https://h-bbot.vercel.app/api/simple_fixed")
    
    if not token:
        print("Error: TELEGRAM_TOKEN not set, using default")
    
    if not webhook_url:
        print("Error: WEBHOOK_URL not set, using default")
    
    # API endpoint for setting the webhook
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    # Parameters for the webhook
    params = {
        "url": webhook_url,
        "drop_pending_updates": True,
        "allowed_updates": ["message", "callback_query", "inline_query"]
    }
    
    print(f"Setting webhook for bot {token} to URL: {webhook_url}")
    
    # Make the request
    try:
        response = requests.post(api_url, json=params)
        result = response.json()
        
        if response.status_code == 200 and result.get("ok"):
            print(f"✅ Webhook set successfully: {webhook_url}")
            
            # Get webhook info
            info_response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
            info = info_response.json()
            print("\nWebhook Info:")
            print(json.dumps(info, indent=2))
            
            return True
        else:
            print(f"❌ Error setting webhook: {result}")
            return False
    
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    setup_webhook() 