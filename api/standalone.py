import json
import os
import requests

# Basic configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

def handler(request, context):
    """Ultra-minimal Vercel serverless function handler"""
    
    # Log request info
    print(f"Request received: method={request.get('method', 'UNKNOWN')}")
    
    try:
        # Handle GET requests (health checks)
        if request.get("method", "") == "GET":
            # Get webhook info for diagnostics
            webhook_info = None
            if TELEGRAM_TOKEN:
                try:
                    response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo")
                    webhook_info = response.json()
                except Exception as e:
                    webhook_info = {"error": str(e)}
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "ok",
                    "message": "Bot webhook is running",
                    "webhook_info": webhook_info
                })
            }
        
        # Handle POST requests (Telegram updates)
        elif request.get("method", "") == "POST":
            # Get body
            body = request.get("body", "{}")
            print(f"Body received: {body[:200]}...")
            
            # Parse JSON if needed
            update = body
            if isinstance(body, str):
                try:
                    update = json.loads(body)
                except:
                    print("Failed to parse body as JSON")
                    update = {}
            
            # Process message if present
            if isinstance(update, dict) and "message" in update and "chat" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")
                print(f"Message from {chat_id}: {text}")
                
                # Send a simple response
                if TELEGRAM_TOKEN:
                    try:
                        message_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                        message_data = {
                            "chat_id": chat_id,
                            "text": f"I received: {text}" if text else "I received your message!"
                        }
                        response = requests.post(message_url, json=message_data)
                        print(f"Response sent: {response.status_code}")
                    except Exception as e:
                        print(f"Error sending response: {e}")
            
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "ok"})
            }
        
        # Default response for other methods
        else:
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "ok", "message": "Method not supported"})
            }
            
    except Exception as e:
        print(f"Global error handler caught: {e}")
        return {
            "statusCode": 200,  # Always return 200 to Telegram
            "body": json.dumps({"status": "error", "message": str(e)})
        } 