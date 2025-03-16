import json
import os
import requests
from datetime import datetime

# Version marker to force new deployment - v1.0.0
# Basic configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8150544076:AAF8GTQ-3CrkOdBvnOmJ85s0hKu0RE4swwE")

# Simple function to send a message
def send_message(chat_id, text):
    if not TELEGRAM_TOKEN:
        print("No token available for sending message")
        return False
    
    params = {
        'chat_id': chat_id,
        'text': text
    }
    
    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(send_url, json=params)
    
    if response.status_code == 200:
        print(f"Message sent to {chat_id}")
        return True
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")
        return False

# Vercel serverless function handler 
def handler(request):
    """Process a request from Vercel"""
    try:
        # Handle GET requests (health checks)
        if request.get("method", "") == "GET":
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "ok",
                    "message": "Minimal bot handler is running",
                    "timestamp": datetime.now().isoformat()
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
                
                # Check if we have a message
                if "message" not in update or "chat" not in update["message"]:
                    print("Update doesn't contain a message or chat")
                    return {
                        "statusCode": 200,
                        "body": json.dumps({
                            "status": "ok",
                            "message": "Update processed (no message/chat)"
                        })
                    }
                
                chat_id = update["message"]["chat"]["id"]
                
                # If there's a text message, respond to it
                if "text" in update["message"]:
                    text = update["message"]["text"]
                    print(f"Message received: {text}")
                    
                    # Send a simple response
                    response_text = f"I received: {text}"
                    send_message(chat_id, response_text)
                else:
                    send_message(chat_id, "I received your message but it's not text.")
                
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