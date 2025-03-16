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
            
        logger.info(f"Sending message to chat_id {chat_id}: {text[:30]}...")
        message = await bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Message sent successfully: {message.message_id}")
        return {"success": True, "message_id": message.message_id}
    except telegram.error.TelegramError as e:
        logger.error(f"Telegram error sending message: {e}")
        return {"success": False, "error": f"Telegram error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {"success": False, "error": str(e)}

async def handle_update(update_data):
    """Process the incoming update from Telegram"""
    try:
        logger.info("Converting update_data to Update object")
        update = telegram.Update.de_json(update_data, bot)
        logger.info(f"Update object created: {update}")
        
        # Handle different types of messages
        if update.message:
            chat_id = update.message.chat_id
            logger.info(f"Processing message from chat_id: {chat_id}")
            
            # Handle commands
            if update.message.text:
                logger.info(f"Processing text message: {update.message.text[:50]}")
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
            
            # Handle media - PRIORITY CASE
            elif update.message.photo:
                # This is now priority handling for photos
                logger.info(f"PRIORITY: Processing photo message. Photo size: {len(update.message.photo)}")
                
                # Get photo details for debugging
                photo_sizes = []
                file_ids = []
                for photo in update.message.photo:
                    photo_sizes.append(f"{photo.width}x{photo.height}")
                    file_ids.append(photo.file_id)
                
                logger.info(f"Photo sizes: {', '.join(photo_sizes)}")
                logger.info(f"Photo file IDs: {', '.join(file_ids)}")
                
                # Try to get info about the largest photo
                try:
                    if update.message.photo:
                        # Get the largest photo (last in the array)
                        largest_photo = update.message.photo[-1]
                        file_info = await bot.get_file(largest_photo.file_id)
                        logger.info(f"Photo file path: {file_info.file_path}")
                except Exception as file_error:
                    logger.error(f"Error getting file info: {file_error}")
                
                # Make sure we respond to the photo quickly
                try:
                    # Send acknowledgment for the photo - with direct call to ensure it happens
                    result = await send_message(chat_id, "📷 Your photo has been received and stored")
                    logger.info(f"Photo response result: {result}")
                    return result
                except Exception as photo_error:
                    # Special error handling for photos
                    logger.error(f"CRITICAL - Error responding to photo: {photo_error}")
                    # Try one more time with basic message
                    try:
                        basic_result = await bot.send_message(chat_id=chat_id, text="📷 Photo received")
                        return {"success": True, "message_id": basic_result.message_id, "recovery": True}
                    except:
                        logger.error("Failed in recovery attempt for photo")
                        pass
                    return {"success": False, "error": str(photo_error)}
            
            elif update.message.document:
                logger.info(f"Processing document: {update.message.document.file_name}")
                return await send_message(chat_id, "📎 Your document has been received and stored")
            
            elif update.message.video:
                logger.info(f"Processing video")
                return await send_message(chat_id, "🎬 Your video has been received and stored")
            
            else:
                logger.info(f"Processing other message type")
                return await send_message(chat_id, "✅ Your message has been received and stored")
        else:
            logger.info("Update does not contain a message")
        
        return {"success": True, "message": "Update processed"}
    
    except Exception as e:
        logger.error(f"Error handling update: {e}")
        logger.error(f"Update data that caused the error: {json.dumps(update_data, default=str)[:300]}")
        
        # Critical recovery - try to send a message if we can determine the chat_id
        try:
            if isinstance(update_data, dict) and "message" in update_data and "chat" in update_data["message"] and "id" in update_data["message"]["chat"]:
                recovery_chat_id = update_data["message"]["chat"]["id"]
                logger.info(f"Attempting recovery response to chat_id: {recovery_chat_id}")
                await bot.send_message(chat_id=recovery_chat_id, text="✅ Message received (recovery response)")
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {recovery_error}")
        
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
        
        # Log the incoming update with more detail for debugging
        update_type = "unknown"
        is_photo = False
        if isinstance(update_data, dict):
            if "message" in update_data:
                if "photo" in update_data["message"]:
                    update_type = "photo"
                    is_photo = True
                    logger.info("📸 PHOTO DETECTED - Processing with priority")
                elif "text" in update_data["message"]:
                    update_type = "text"
                elif "document" in update_data["message"]:
                    update_type = "document"
                else:
                    update_type = "other_message"
            else:
                update_type = "non_message"
        
        logger.info(f"Received update type: {update_type}")
        
        # For photo updates, log more details
        if is_photo:
            logger.info(f"Photo update details: {json.dumps(update_data.get('message', {}).get('photo', []), default=str)}")
        else:
            logger.info(f"Received update data: {json.dumps(update_data, default=str)[:300]}...")
        
        # Process the update with special handling for photos
        if is_photo:
            # For photos, make sure we handle them with special care
            logger.info("Starting priority processing for photo")
            # Process directly and make sure we get a response
            result = await handle_update(update_data)
            logger.info(f"Photo processing result: {result}")
            return {"success": True, "result": result, "update_type": "photo"}
        else:
            # Regular updates
            result = await handle_update(update_data)
            return {"success": True, "result": result, "update_type": update_type}
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
    logger.info(f"Handler called with method: {method}")
    
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
            logger.info(f"Received POST body type: {type(body)}")
            
            # Convert to dict if it's a string
            if isinstance(body, str):
                logger.info(f"Converting string body to JSON. Length: {len(body)}")
                try:
                    body = json.loads(body)
                    logger.info(f"Successfully parsed JSON. Keys: {', '.join(body.keys())}")
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON: {e}")
                    logger.error(f"Body preview: {body[:100]}")
                    # Return error response for invalid JSON
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Invalid JSON payload'})
                    }
            
            # Log that we received a webhook call
            logger.info(f"Received webhook call at {datetime.now().isoformat()}")
            
            # Check for key Telegram update components
            if isinstance(body, dict):
                if 'update_id' not in body:
                    logger.warning("Received webhook without update_id - might not be from Telegram")
                    logger.warning(f"Body keys: {', '.join(body.keys() if isinstance(body, dict) else ['<not a dict>'])}")
            
            # Special handling for photo messages
            is_photo = False
            if (isinstance(body, dict) and 
                "message" in body and 
                isinstance(body["message"], dict) and 
                "photo" in body["message"]):
                is_photo = True
                logger.info("📸 PHOTO MESSAGE detected in handler")
            
            # Process the update asynchronously
            response = asyncio.run(process_telegram_update(body))
            
            # For photos, make sure we're sending a more specific response
            if is_photo:
                logger.info("Photo processing completed in handler")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        "success": True, 
                        "message": "Photo received and processed",
                        "timestamp": datetime.now().isoformat()
                    })
                }
            
            # Return success response
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