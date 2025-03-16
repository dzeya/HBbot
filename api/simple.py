import json
import os
import requests
from datetime import datetime

# Get Telegram token from environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8150544076:AAF8GTQ-3CrkOdBvnOmJ85s0hKu0RE4swwE")

# Supabase connection details - Using environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "https://foliyzwhhkkfbemiptvp.supabase.co"))
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvbGl5endoaGtrZmJlbWlwdHZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIwNDg1MDksImV4cCI6MjA1NzYyNDUwOX0.SgTPp2Vwzl1wDixlItMt9v7YLwyH7AbZwH8mPB-BkQw"))
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# Try to use service key if available, otherwise fall back to anon key
if SUPABASE_SERVICE_KEY:
    print("Using service role key for Supabase API")
    API_KEY = SUPABASE_SERVICE_KEY
else:
    print("Using anonymous key for Supabase API")
    API_KEY = SUPABASE_ANON_KEY

# REST API endpoints
REST_URL = f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else ""
HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
    "X-Client-Info": "python-telegram-bot-supabase-rest"
}

def test_supabase_connection():
    """Test connection to Supabase and database tables"""
    try:
        # Test basic connection
        response = requests.get(
            f"{REST_URL}/users",
            headers=HEADERS,
            params={"limit": 1}
        )
        
        if response.status_code in (200, 201, 204):
            print(f"Successfully connected to Supabase REST API (status: {response.status_code})")
            return True
        else:
            print(f"Failed to connect to Supabase REST API: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return False

def save_user_to_supabase(user_data):
    """Save user data to Supabase"""
    try:
        # Check if user already exists
        check_response = requests.get(
            f"{REST_URL}/users",
            headers=HEADERS,
            params={"user_id": f"eq.{user_data['user_id']}"}
        )
        
        if check_response.status_code == 200 and check_response.json():
            # User exists, update
            print(f"Updating existing user {user_data['user_id']}")
            response = requests.patch(
                f"{REST_URL}/users",
                headers=HEADERS,
                params={"user_id": f"eq.{user_data['user_id']}"},
                json=user_data
            )
        else:
            # User doesn't exist, create
            print(f"Creating new user {user_data['user_id']}")
            response = requests.post(
                f"{REST_URL}/users",
                headers=HEADERS,
                json=user_data
            )
        
        if response.status_code in (200, 201, 204):
            print(f"Successfully saved user data for {user_data['user_id']}")
            return True
        else:
            print(f"Failed to save user data: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error saving user data: {str(e)}")
        return False

def save_message_to_supabase(message_data):
    """Save message to Supabase"""
    try:
        response = requests.post(
            f"{REST_URL}/message_history",
            headers=HEADERS,
            json=message_data
        )
        
        if response.status_code in (200, 201, 204):
            print(f"Successfully saved message for user {message_data['user_id']}")
            return True
        else:
            print(f"Failed to save message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error saving message: {str(e)}")
        return False

def handler(request, context):
    """Ultra-minimal Vercel serverless function handler"""
    
    # Log request info
    print(f"Request received: method={request.get('method', 'UNKNOWN')}")
    
    try:
        # Handle GET requests (health checks)
        if request.get("method", "") == "GET":
            # Test Supabase connection
            supabase_status = test_supabase_connection()
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "ok",
                    "message": "Bot webhook is running",
                    "supabase_connected": supabase_status,
                    "supabase_url": SUPABASE_URL
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
                    
                    # Extract user information
                    user = update["message"]["from"]
                    user_id = user.get("id")
                    first_name = user.get("first_name", "")
                    last_name = user.get("last_name", "")
                    username = user.get("username", "")
                    
                    print(f"Message from {chat_id} (User: {username or first_name}): {text}")
                    
                    # Save user data to Supabase
                    user_data = {
                        "user_id": user_id,
                        "first_name": first_name,
                        "last_name": last_name,
                        "username": username,
                        "last_active": datetime.now().isoformat()
                    }
                    
                    save_user_to_supabase(user_data)
                    
                    # Save message to Supabase
                    message_data = {
                        "user_id": user_id,
                        "message_id": update["message"].get("message_id"),
                        "message_text": text,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    save_message_to_supabase(message_data)
                    
                    # Special handling for /start command
                    if text.strip() == "/start":
                        response_text = "👋 Welcome to the HB Telegram Bot! I'm now active and ready to help you."
                    else:
                        response_text = f"I received your message: {text}"
                    
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
                            
                            # Save bot response to Supabase
                            response_data = {
                                "user_id": user_id,
                                "message_id": -1,  # Placeholder for bot message
                                "message_text": response_text,
                                "timestamp": datetime.now().isoformat(),
                                "is_bot": True
                            }
                            
                            save_message_to_supabase(response_data)
                            
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