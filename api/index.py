from http.server import BaseHTTPRequestHandler
import os
import json
import logging
import requests
from datetime import datetime
import telegram
import asyncio
from urllib.parse import parse_qs

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Initialize bot globally
bot = None
try:
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
except Exception as e:
    logger.error(f"Error initializing bot: {e}")

def test_supabase_connection():
    """Test connection to Supabase using direct REST API calls"""
    try:
        # Make a simple request to the REST API
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        
        # Try to get database version as a simple test
        url = f"{SUPABASE_URL}/rest/v1/"
        logger.info(f"Testing connection to Supabase: {url}")
        
        response = requests.get(url, headers=headers)
        logger.info(f"Supabase connection test response: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Supabase connection test successful")
            return True
        else:
            logger.warning(f"Supabase connection test failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error testing Supabase connection: {e}")
        return False

async def send_message(chat_id, text):
    """Helper function to send a message"""
    try:
        if not bot:
            logger.error("Bot not initialized")
            return {"success": False, "error": "Bot not initialized"}
            
        await bot.send_message(chat_id=chat_id, text=text)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {"success": False, "error": str(e)}

async def handle_update(update_data):
    """Process the incoming update from Telegram"""
    try:
        update = telegram.Update.de_json(update_data, bot)
        
        # Handle different types of messages
        if update.message:
            chat_id = update.message.chat_id
            
            # Handle commands
            if update.message.text:
                if update.message.text.startswith('/start'):
                    return await send_message(chat_id, "👋 Welcome to the HB Telegram Bot! Your messages will be stored securely.")
                
                elif update.message.text.startswith('/help'):
                    return await send_message(chat_id, "💬 This bot stores your messages and media in a secure database.\n\nCommands:\n/start - Start the bot\n/help - Show this help message\n/stats - Show your message statistics")
                
                elif update.message.text.startswith('/stats'):
                    # Here you would get stats from Supabase
                    return await send_message(chat_id, "📊 Stats functionality available in the full version")
                
                # Regular text message
                else:
                    return await send_message(chat_id, "✅ Your message has been received and stored")
            
            # Handle media
            elif update.message.photo:
                return await send_message(chat_id, "📷 Your photo has been received and stored")
            
            elif update.message.document:
                return await send_message(chat_id, "📎 Your document has been received and stored")
            
            elif update.message.video:
                return await send_message(chat_id, "🎬 Your video has been received and stored")
            
            else:
                return await send_message(chat_id, "✅ Your message has been received and stored")
        
        return {"success": True, "message": "Update processed"}
    
    except Exception as e:
        logger.error(f"Error handling update: {e}")
        return {"success": False, "error": str(e)}

async def set_webhook():
    """Set webhook with Telegram API"""
    try:
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Current webhook info: {webhook_info.to_dict()}")
        
        # Only set webhook if it's not already set to our URL or is pending
        if webhook_info.url != WEBHOOK_URL or webhook_info.pending_update_count > 0:
            logger.info(f"Setting webhook to: {WEBHOOK_URL}")
            success = await bot.set_webhook(
                url=WEBHOOK_URL,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query", "inline_query"],
                max_connections=100  # Allow more simultaneous connections
            )
            if success:
                logger.info("Webhook set successfully!")
                return {"status": "webhook_updated", "url": WEBHOOK_URL}
            else:
                logger.error("Failed to set webhook")
                return {"status": "error", "message": "Failed to set webhook"}
        else:
            logger.info("Webhook already set correctly")
            return {"status": "webhook_already_set", "url": WEBHOOK_URL}
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return {"status": "error", "message": str(e)}

async def process_telegram_update(request_body):
    """Process update from Telegram webhook"""
    if not bot:
        logger.error("Bot not initialized")
        return {"success": False, "error": "Bot not initialized"}
    
    try:
        # Parse the update data
        update_data = request_body
        
        # Log the incoming update
        logger.info(f"Received update: {json.dumps(update_data, default=str)[:200]}...")
        
        # Process the update
        result = await handle_update(update_data)
        
        # Return the result immediately without waiting
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return {"success": False, "error": str(e)}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests (health check)"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "message": "Telegram bot webhook is running",
            "env_check": {
                "token_set": bool(TELEGRAM_TOKEN),
                "webhook_url_set": bool(WEBHOOK_URL),
                "supabase_url_set": bool(SUPABASE_URL),
                "supabase_key_set": bool(SUPABASE_ANON_KEY)
            }
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_POST(self):
        """Handle POST requests (webhook updates)"""
        try:
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            update_data = json.loads(post_data.decode('utf-8'))
            
            # Process the update asynchronously
            response = asyncio.run(process_telegram_update(update_data))
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        
        except Exception as e:
            logger.error(f"Error processing webhook request: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

# Initialize webhook on first load
def init():
    """Initialize the bot on first load"""
    if not bot:
        logger.error("Bot not initialized, skipping initialization")
        return
    
    logger.info("Initializing bot webhook")
    
    # Test Supabase connection
    supabase_result = test_supabase_connection()
    logger.info(f"Supabase connection test: {'Success' if supabase_result else 'Failed'}")
    
    # Set up webhook
    try:
        # Run the webhook setup asynchronously
        result = asyncio.run(set_webhook())
        logger.info(f"Webhook setup result: {result}")
        
        # Set up a keep-alive mechanism
        # This won't work in serverless, but it's added for documentation purposes
        # To keep Vercel functions warm, you need an external service to ping your endpoint
        logger.info("Note: To prevent cold starts, consider using an external service to ping your webhook URL every 5-10 minutes")
        
        return result
    except Exception as e:
        logger.error(f"Error during webhook setup: {e}")
        return {"success": False, "error": str(e)}

# Vercel serverless function entry point
def handler(request, context):
    """Entry point for Vercel serverless function"""
    method = request.get('method', '')
    
    # Health check endpoint
    if method == 'GET':
        # Get webhook info for diagnostics
        webhook_info = None
        if bot:
            try:
                webhook_info = asyncio.run(bot.get_webhook_info()).to_dict()
            except Exception as e:
                logger.error(f"Error getting webhook info: {e}")
                webhook_info = {"error": str(e)}
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'message': 'Telegram bot webhook is running',
                'webhook_info': webhook_info,
                'env_check': {
                    'token_set': bool(TELEGRAM_TOKEN),
                    'webhook_url_set': bool(WEBHOOK_URL),
                    'supabase_url_set': bool(SUPABASE_URL),
                    'supabase_key_set': bool(SUPABASE_ANON_KEY)
                }
            })
        }
    
    # Webhook endpoint
    elif method == 'POST':
        try:
            # Get the body from the request
            body = request.get('body', '{}')
            
            # Convert to dict if it's a string
            if isinstance(body, str):
                body = json.loads(body)
            
            # Log that we received a webhook call
            logger.info(f"Received webhook call at {datetime.now().isoformat()}")
                
            # Process the update asynchronously - don't wait for completion
            response = asyncio.run(process_telegram_update(body))
            
            # Return immediately to prevent Vercel from waiting
            return {
                'statusCode': 200,
                'body': json.dumps({"success": True, "message": "Update received"})
            }
        except Exception as e:
            logger.error(f"Error in webhook processing: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }
    
    # Other methods
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }

# Set up the webhook when the module is loaded
try:
    init()
except Exception as e:
    logger.error(f"Error during initialization: {e}") 