from http.server import BaseHTTPRequestHandler
import json
import os
import requests

# Basic configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8150544076:AAF8GTQ-3CrkOdBvnOmJ85s0hKu0RE4swwE")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

def send_telegram_message(chat_id, text):
    """Send a message to a Telegram chat"""
    if not TELEGRAM_TOKEN:
        print("Telegram token not set")
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(url, json=payload)
        print(f"Message sent to {chat_id}, status: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

class handler(BaseHTTPRequestHandler):
    def handle_error(self, error_message):
        self.send_response(200)  # Still return 200 to Telegram
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "error",
            "message": str(error_message)
        }).encode('utf-8'))
        
    def do_GET(self):
        try:
            # Get webhook info for diagnostics
            webhook_info = None
            if TELEGRAM_TOKEN:
                try:
                    response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo")
                    webhook_info = response.json()
                except Exception as e:
                    webhook_info = {"error": str(e)}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "message": "Bot webhook is running",
                "webhook_info": webhook_info,
                "webhook_url": WEBHOOK_URL
            }).encode('utf-8'))
        except Exception as e:
            print(f"Error in GET handler: {e}")
            self.handle_error(e)
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')
            print(f"Body received: {body[:200]}...")
            
            # Parse JSON if needed
            try:
                update = json.loads(body)
            except json.JSONDecodeError:
                print("Failed to parse body as JSON")
                update = {}
            
            # Process message if present
            if isinstance(update, dict) and "message" in update and "chat" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")
                print(f"Message from {chat_id}: {text}")
                
                # Add special handling for /start command
                if text and text.strip() == "/start":
                    response_text = "👋 Welcome to the HB Telegram Bot! I'm now active and ready to help you."
                else:
                    response_text = f"I received: {text}" if text else "I received your message!"
                
                # Send the response
                if TELEGRAM_TOKEN:
                    send_telegram_message(chat_id, response_text)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok"
            }).encode('utf-8'))
        except Exception as e:
            print(f"Error in POST handler: {e}")
            self.handle_error(e) 