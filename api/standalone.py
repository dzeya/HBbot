from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from datetime import datetime

# Version marker to force new deployment - v1.0.4
# Basic configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8150544076:AAF8GTQ-3CrkOdBvnOmJ85s0hKu0RE4swwE")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Supabase connection details - Using environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "https://foliyzwhhkkfbemiptvp.supabase.co"))
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvbGl5endoaGtrZmJlbWlwdHZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIwNDg1MDksImV4cCI6MjA1NzYyNDUwOX0.SgTPp2Vwzl1wDixlItMt9v7YLwyH7AbZwH8mPB-BkQw"))
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if SUPABASE_SERVICE_KEY:
    print(f"Using service role key for Supabase API: {SUPABASE_SERVICE_KEY[:10]}...")
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
            return True, response.status_code
        else:
            print(f"Failed to connect to Supabase REST API: {response.status_code} - {response.text}")
            return False, response.status_code
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return False, str(e)

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

def get_diagnostic_report(user_id):
    """Generate a full diagnostic report"""
    print(f"Generating diagnostic report for user {user_id}...")
    # Start building the diagnostic report
    report = []
    
    # 1. Add header
    report.append("📊 Bot Diagnostic Results (standalone)")
    report.append("")
    
    # 2. Check environment variables
    report.append("🔑 Environment Variables:")
    
    # Check SUPABASE_URL
    supabase_url_value = SUPABASE_URL[:10] + "..." + SUPABASE_URL[-5:] if SUPABASE_URL else "Not set"
    report.append(f"{'✅' if SUPABASE_URL else '❌'} SUPABASE_URL is {'set' if SUPABASE_URL else 'not set'} (value: {supabase_url_value})")
    
    # Check SUPABASE_ANON_KEY
    anon_key_value = "eyJhb..." + SUPABASE_ANON_KEY[-5:] if SUPABASE_ANON_KEY else "Not set"
    report.append(f"{'✅' if SUPABASE_ANON_KEY else '❌'} SUPABASE_ANON_KEY is {'set' if SUPABASE_ANON_KEY else 'not set'} (value: {anon_key_value})")
    
    # Check TELEGRAM_TOKEN
    token_value = TELEGRAM_TOKEN[:6] + "..." + TELEGRAM_TOKEN[-6:] if TELEGRAM_TOKEN else "Not set"
    report.append(f"{'✅' if TELEGRAM_TOKEN else '❌'} TELEGRAM_TOKEN is {'set' if TELEGRAM_TOKEN else 'not set'} (value: {token_value})")
    
    # Check SUPABASE_SERVICE_KEY
    service_key_value = SUPABASE_SERVICE_KEY[:10] + "..." + SUPABASE_SERVICE_KEY[-5:] if SUPABASE_SERVICE_KEY else "Not set"
    report.append(f"{'✅' if SUPABASE_SERVICE_KEY else '❌'} SUPABASE_SERVICE_KEY is {'set' if SUPABASE_SERVICE_KEY else 'not set'} (value: {service_key_value if SUPABASE_SERVICE_KEY else 'Not set'})")
    
    # Which key is being used
    report.append(f"ℹ️ Currently using: {'Service Role Key' if SUPABASE_SERVICE_KEY else 'Anonymous Key'}")
    
    # 3. Check Supabase connection
    report.append("")
    report.append("💾 Supabase Connection:")
    
    connection_ok, status = test_supabase_connection()
    if connection_ok:
        report.append(f"✅ Connected to Supabase REST API successfully (status: {status})")
    else:
        report.append(f"❌ Failed to connect to Supabase REST API (status: {status})")
    
    # 4. Add webhook info
    report.append("")
    report.append("🔄 Webhook Info:")
    if TELEGRAM_TOKEN:
        try:
            response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo")
            webhook_info = response.json()
            if webhook_info.get("ok", False):
                webhook_data = webhook_info.get("result", {})
                report.append(f"URL: {webhook_data.get('url', 'Not set')}")
                report.append(f"Custom certificate: {'Yes' if webhook_data.get('has_custom_certificate') else 'No'}")
                report.append(f"Pending updates: {webhook_data.get('pending_update_count', 0)}")
            else:
                report.append(f"❌ Error getting webhook info: {webhook_info.get('description', 'Unknown error')}")
        except Exception as e:
            report.append(f"❌ Error checking webhook: {str(e)}")
    else:
        report.append("❌ Cannot check webhook without TELEGRAM_TOKEN")
    
    # 5. System info
    report.append("")
    report.append("💻 System Info:")
    report.append(f"Python version: 3.11.1")
    report.append(f"Current time: {datetime.now().isoformat()}")
    report.append(f"Standalone handler version: v1.0.4")
    
    print("Diagnostic report generated successfully")
    return "\n".join(report)

# Using the BaseHTTPRequestHandler approach for Vercel
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
            
            # Check Supabase connection
            supabase_connected, status = test_supabase_connection()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "message": "Bot webhook is running",
                "webhook_info": webhook_info,
                "webhook_url": WEBHOOK_URL,
                "supabase_connected": supabase_connected,
                "supabase_status": status,
                "using_service_key": bool(SUPABASE_SERVICE_KEY)
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
                user_id = update["message"]["from"].get("id", 0)
                print(f"Message from {chat_id} (User ID: {user_id}): {text}")
                
                # Handle diagnostic command
                if text and text.strip() == "/diagnostic":
                    print("Diagnostic command detected in standalone.py!")
                    response_text = get_diagnostic_report(user_id)
                # Add special handling for /start command
                elif text and text.strip() == "/start":
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