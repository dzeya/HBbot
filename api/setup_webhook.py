import os
import sys
import requests
import json

def setup_webhook():
    """
    Set up the webhook for a Telegram bot
    """
    # Get environment variables
    token = os.getenv("TELEGRAM_TOKEN", "")
    webhook_url = os.getenv("WEBHOOK_URL", "")
    
    if not token:
        print("Error: TELEGRAM_TOKEN not set")
        sys.exit(1)
    
    if not webhook_url:
        print("Error: WEBHOOK_URL not set")
        sys.exit(1)
    
    # API endpoint for setting the webhook
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"
    
    # Parameters for the webhook
    params = {
        "url": webhook_url,
        "drop_pending_updates": True
    }
    
    # Make the request
    try:
        response = requests.post(api_url, json=params)
        result = response.json()
        
        if response.status_code == 200 and result.get("ok"):
            print(f"Webhook set successfully: {webhook_url}")
            
            # Get webhook info
            info_response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
            info = info_response.json()
            print("\nWebhook Info:")
            print(json.dumps(info, indent=2))
            
            return True
        else:
            print(f"Error setting webhook: {result}")
            return False
    
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    setup_webhook() 