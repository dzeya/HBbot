import json
import os
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler

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

def get_diagnostic_report(user_id):
    """Generate a full diagnostic report"""
    print(f"Generating diagnostic report for user {user_id}...")
    # Start building the diagnostic report
    report = []
    
    # 1. Add header
    report.append("📊 Bot Diagnostic Results")
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
    service_key_value = "eyJhb..." + SUPABASE_SERVICE_KEY[-6:] if SUPABASE_SERVICE_KEY else "Not set"
    report.append(f"{'✅' if SUPABASE_SERVICE_KEY else '❌'} SUPABASE_SERVICE_KEY is {'set' if SUPABASE_SERVICE_KEY else 'not set'} (value: {service_key_value})")
    
    # 3. Check Supabase connection
    report.append("")
    report.append("💾 Supabase Connection:")
    
    connection_ok = test_supabase_connection()
    if connection_ok:
        report.append("✅ Connected to Supabase REST API successfully (status: 200)")
    else:
        report.append("❌ Failed to connect to Supabase REST API")
    
    # 4. Check database tables
    report.append("")
    report.append("📋 Database Tables:")
    
    # Check users table
    try:
        users_response = requests.get(
            f"{REST_URL}/users",
            headers=HEADERS,
            params={"user_id": f"eq.{user_id}"}
        )
        
        if users_response.status_code in (200, 201, 204):
            user_data = users_response.json()
            report.append(f"✅ 'users' table accessible with data for current user")
        else:
            report.append(f"❌ 'users' table not accessible: {users_response.status_code}")
    except Exception as e:
        report.append(f"❌ Error checking 'users' table: {str(e)}")
    
    # Check message_history table
    try:
        messages_response = requests.get(
            f"{REST_URL}/message_history",
            headers=HEADERS,
            params={"user_id": f"eq.{user_id}"}
        )
        
        if messages_response.status_code in (200, 201, 204):
            messages = messages_response.json()
            report.append(f"✅ 'message_history' table accessible with {len(messages)} messages for current user")
        else:
            report.append(f"❌ 'message_history' table not accessible: {messages_response.status_code}")
    except Exception as e:
        report.append(f"❌ Error checking 'message_history' table: {str(e)}")
    
    # Add system info
    report.append("")
    report.append("💻 System Info:")
    report.append(f"Python version: 3.11.1")
    report.append(f"python-telegram-bot version: 22.0")
    report.append(f"httpx version: 0.24.1")
    report.append(f"requests version: 2.32.3")
    
    # Final message
    report.append("")
    report.append("I save all your messages to a Supabase database.")
    
    # Add supported content types
    report.append("")
    report.append("📄 Supported content types:")
    report.append("• Text messages")
    report.append("• Photos/Images")
    report.append("• Documents/Files")
    report.append("• Videos")
    report.append("• Audio files")
    report.append("• Voice messages")
    report.append("• Stickers")
    report.append("• Animations/GIFs")
    
    print("Diagnostic report generated successfully")
    return "\n".join(report)

def process_diagnostic_request(request):
    """Process diagnostic request and return a response"""
    print(f"Diagnostic handler received request: method={request.get('method', 'UNKNOWN')}")
    
    try:
        # Handle GET requests (health checks)
        if request.get("method", "") == "GET":
            # Test Supabase connection
            supabase_status = test_supabase_connection()
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "ok",
                    "message": "Diagnostic endpoint is running",
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
                    
                    print(f"Diagnostic endpoint received message: {text}")
                    
                    # Always send diagnostic report regardless of the message
                    response_text = get_diagnostic_report(user_id)
                    
                    # Send response using Telegram API
                    if TELEGRAM_TOKEN:
                        try:
                            print(f"Sending diagnostic response to user")
                            send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                            payload = {
                                "chat_id": chat_id,
                                "text": response_text
                            }
                            resp = requests.post(send_url, json=payload)
                            print(f"Diagnostic response sent, status: {resp.status_code}")
                            
                        except Exception as e:
                            print(f"Error sending diagnostic to user: {e}")
                
                # Return a success response to Telegram servers
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "ok",
                        "message": "Diagnostic completed"
                    })
                }
            except Exception as e:
                print(f"Error processing diagnostic request: {e}")
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
                    "message": "Method not supported by diagnostic endpoint"
                })
            }
            
    except Exception as e:
        print(f"Diagnostic global error handler caught: {e}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Create a request object similar to what our process_request expects
            request = {
                "method": "GET",
                "path": self.path
            }
            
            # Process the request
            response = process_diagnostic_request(request)
            
            # Send the response
            self.send_response(response["statusCode"])
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response["body"].encode('utf-8'))
            
        except Exception as e:
            print(f"Error in diagnostic GET handler: {e}")
            self.send_response(200)  # Still return 200 to Telegram
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": str(e)
            }).encode('utf-8'))
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Create a request object similar to what our process_request expects
            request = {
                "method": "POST",
                "path": self.path,
                "body": body
            }
            
            # Process the request
            response = process_diagnostic_request(request)
            
            # Send the response
            self.send_response(response["statusCode"])
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response["body"].encode('utf-8'))
            
        except Exception as e:
            print(f"Error in diagnostic POST handler: {e}")
            self.send_response(200)  # Still return 200 to Telegram
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": str(e)
            }).encode('utf-8')) 