import json
import os
import requests

# Get Telegram token from environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8150544076:AAF8GTQ-3CrkOdBvnOmJ85s0hKu0RE4swwE")

def handler(request, context):
    """Ultra-minimal Vercel serverless function handler"""
    
    # Log request info
    print(f"Request received: method={request.get('method', 'UNKNOWN')}")
    
    try:
        # Handle GET requests (health checks)
        if request.get("method", "") == "GET":
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "ok",
                    "message": "Bot webhook is running"
                })
            }
        
        # Handle POST requests (Telegram updates)
        elif request.get("method", "") == "POST":
            body = request.get("body", "{}")
            
            try:
                if isinstance(body, str):
                    update = json.loads(body)
                else:
                    update = body
                
                # Process the Telegram update and send a response
                if "message" in update and "chat" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"].get("text", "")
                    print(f"Message from {chat_id}: {text}")
                    
                    # Special handling for /start command
                    if text and text.strip() == "/start":
                        response_text = "👋 Welcome to the HB Telegram Bot! I'm now active and ready to help you."
                    else:
                        response_text = f"I received your message: {text}" if text else "I received your message!"
                    
                    # Send response using Telegram API
                    if TELEGRAM_TOKEN:
                        try:
                            send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                            payload = {
                                "chat_id": chat_id,
                                "text": response_text
                            }
                            resp = requests.post(send_url, json=payload)
                            print(f"Response sent to user, status: {resp.status_code}")
                        except Exception as e:
                            print(f"Error sending message to user: {e}")
                
                # Return a success response to Telegram servers
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "ok",
                        "message": "Update processed successfully"
                    })
                }
            except Exception as e:
                print(f"Error processing request: {e}")
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "error",
                        "message": str(e)
                    })
                }
        
        # Default response for other methods
        else:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "ok",
                    "message": "Method not supported"
                })
            }
            
    except Exception as e:
        print(f"Global error handler caught: {e}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        } 