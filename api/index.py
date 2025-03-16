import os
import json
import logging
import requests
from datetime import datetime
import telegram
from telegram.ext import Application
import asyncio
import time

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

# Create HTTP-specific application parameters - explicitly disable SOCKS
app_params = {
    "connection_pool_size": 10,
    "connect_timeout": 10.0,
    "read_timeout": 10.0,
    "write_timeout": 10.0,
    "pool_timeout": 1.0,
    "base_url": "https://api.telegram.org/bot",
    "base_file_url": "https://api.telegram.org/file/bot",
    "proxy_url": None,  # Explicitly set to None to avoid any SOCKS issues
    "bot_token": TELEGRAM_TOKEN,
}

# Initialize bot with explicit HTTP configuration
try:
    bot = telegram.Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None
    logger.info("Bot initialized with basic configuration")
except Exception as e:
    logger.error(f"Error initializing basic bot: {e}")
    bot = None

def test_supabase_connection():
    """Test connection to Supabase using direct REST API calls"""
    try:
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        
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

async def set_webhook():
    """Set webhook with Telegram API"""
    if not bot:
        return {"status": "error", "message": "Bot not initialized"}
    
    try:
        # First, delete any existing webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info(f"Deleted existing webhook")
        
        # Wait a moment to ensure deletion is processed
        await asyncio.sleep(1)
        
        # Set the new webhook
        success = await bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "inline_query"]
        )
        
        if success:
            logger.info(f"Webhook set successfully to {WEBHOOK_URL}")
            
            # Get information about the new webhook
            webhook_info = await bot.get_webhook_info()
            logger.info(f"Webhook info: {webhook_info.to_dict()}")
            
            return {"status": "success", "webhook_info": webhook_info.to_dict()}
        else:
            logger.error("Failed to set webhook")
            return {"status": "error", "message": "Failed to set webhook"}
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return {"status": "error", "message": str(e)}

def dump_object(obj, name="object", max_depth=3, current_depth=0):
    """Recursively dump object structure for debugging"""
    if current_depth > max_depth:
        return "..."
    
    if isinstance(obj, dict):
        result = "{\n"
        for k, v in obj.items():
            if current_depth < max_depth:
                result += "  " * (current_depth + 1) + f'"{k}": {dump_object(v, k, max_depth, current_depth + 1)},\n'
            else:
                result += "  " * (current_depth + 1) + f'"{k}": ...,\n'
        result += "  " * current_depth + "}"
        return result
    elif isinstance(obj, list):
        if not obj:
            return "[]"
        result = "[\n"
        for i, item in enumerate(obj[:3]):  # Only show first 3 items
            result += "  " * (current_depth + 1) + f"{dump_object(item, f'{name}[{i}]', max_depth, current_depth + 1)},\n"
        if len(obj) > 3:
            result += "  " * (current_depth + 1) + f"... ({len(obj) - 3} more items)\n"
        result += "  " * current_depth + "]"
        return result
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return json.dumps(obj)
    else:
        # For non-serializable objects, show type and dir if available
        try:
            # For telegram.Update objects or similar
            if hasattr(obj, 'to_dict'):
                return dump_object(obj.to_dict(), name, max_depth, current_depth)
            else:
                return f"<{type(obj).__name__}: {str(obj)[:50]}>"
        except:
            return f"<{type(obj).__name__}>"

# Alternative direct message sending function to avoid HTTP issues
async def send_message_direct(chat_id, text):
    """Send message using requests directly to avoid HTTP/SOCKS issues"""
    if not TELEGRAM_TOKEN:
        logger.error("No token available for direct API call")
        return False
        
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        # Make synchronous request since we're in an async function
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            logger.info(f"Direct API message sent successfully to {chat_id}")
            return True
        else:
            logger.error(f"Direct API message failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error in direct message sending: {e}")
        return False

async def handle_telegram_update(update_data):
    """Process an update from Telegram"""
    if not bot:
        return {"success": False, "error": "Bot not initialized"}
    
    try:
        # First, log the raw update data as is
        logger.info("🔍 RAW UPDATE STRUCTURE: 🔍")
        logger.info(dump_object(update_data, "update_data"))
        
        # Direct access to message for simplicity
        chat_id = None
        message_type = "unknown"
        response_sent = False
        
        # Extract chat_id and key message data directly from dict
        if isinstance(update_data, dict) and "message" in update_data:
            message = update_data["message"]
            
            if "chat" in message and "id" in message["chat"]:
                chat_id = message["chat"]["id"]
                logger.info(f"Extracted chat_id directly: {chat_id}")
            
            # Check for message type by keys present
            if "text" in message:
                message_type = "text"
                text_content = message["text"]
                logger.info(f"Text message detected: {text_content[:100]}")
                
                # Handle commands directly
                if text_content.startswith('/'):
                    response_message = "Command received!"
                    if text_content.startswith('/start'):
                        response_message = "👋 Welcome to the HB Telegram Bot! [FIXED MODE]"
                    elif text_content.startswith('/help'):
                        response_message = "💬 This bot stores your messages and media. [FIXED MODE]"
                
                # Regular message response
                else:
                    response_message = "✅ Your text message has been received [FIXED MODE]"
                    
                # Send response directly to avoid HTTP issues
                success = await send_message_direct(chat_id, response_message)
                if success:
                    response_sent = True
                
            elif "photo" in message:
                message_type = "photo"
                logger.info("Photo message detected!")
                photo_array = message["photo"]
                
                if isinstance(photo_array, list) and photo_array:
                    # Get the largest photo (last in array)
                    file_id = photo_array[-1].get("file_id", "unknown")
                    logger.info(f"Photo file_id: {file_id}")
                    
                    # Send response directly
                    success = await send_message_direct(chat_id, "📸 Your photo has been received! [FIXED MODE]")
                    if success:
                        response_sent = True
            
            elif "document" in message:
                message_type = "document"
                logger.info("Document message detected!")
                
                # Send response directly
                success = await send_message_direct(chat_id, "📎 Your document has been received! [FIXED MODE]")
                if success:
                    response_sent = True
            
            else:
                # Try to determine message type from keys
                for key in message:
                    if key in ["audio", "video", "voice", "sticker", "location", "contact"]:
                        message_type = key
                        logger.info(f"{key.capitalize()} message detected!")
                        
                        # Send generic response
                        success = await send_message_direct(chat_id, f"✅ Your {message_type} has been received! [FIXED MODE]")
                        if success:
                            response_sent = True
                        break
        
        # If we couldn't extract chat_id, try the more structured approach
        if not chat_id:
            logger.warning("Could not get chat_id directly from dict, trying structured approach")
            try:
                # Convert dict to Update object
                update = telegram.Update.de_json(update_data, bot)
                
                if update and update.message:
                    chat_id = update.message.chat_id
                    logger.info(f"Got chat_id from Update object: {chat_id}")
                    
                    # If we haven't sent a response yet, try to send one via the bot object
                    if not response_sent and chat_id:
                        await bot.send_message(
                            chat_id=chat_id,
                            text="✅ Your message has been received (fallback method) [FIXED MODE]"
                        )
                        response_sent = True
            except Exception as e:
                logger.error(f"Error in fallback processing: {e}")
        
        # Final fallback: try direct API access if we have chat_id but no response sent
        if chat_id and not response_sent:
            logger.warning("Using final fallback - direct API call")
            success = await send_message_direct(
                chat_id, 
                "✅ Message received (emergency fallback) [FIXED MODE]"
            )
            if success:
                response_sent = True
                
        return {
            "success": True if chat_id else False,
            "message_type": message_type,
            "chat_id": chat_id,
            "response_sent": response_sent
        }
            
    except Exception as e:
        logger.error(f"Error handling update: {e}")
        logger.error(f"Update data that caused the error: {json.dumps(update_data)[:300] if isinstance(update_data, dict) else str(update_data)[:300]}")
        
        # Try to send an error notification if we can determine the chat_id
        try:
            if isinstance(update_data, dict) and "message" in update_data and "chat" in update_data["message"]:
                recovery_chat_id = update_data["message"]["chat"]["id"]
                
                # Use direct sending to avoid any HTTP issues
                await send_message_direct(
                    recovery_chat_id,
                    "⚠️ Sorry, there was an error processing your message. [FIXED MODE]"
                )
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {recovery_error}")
            
        return {"success": False, "error": str(e)}

# Vercel serverless function entry point
async def initialize():
    """Initialize the bot and webhook"""
    if not bot:
        logger.error("Bot not initialized - missing TELEGRAM_TOKEN")
        return {"success": False, "error": "Bot not initialized"}
    
    # Test Supabase connection
    supabase_result = test_supabase_connection()
    logger.info(f"Supabase connection test: {'Success' if supabase_result else 'Failed'}")
    
    # Set webhook
    webhook_result = await set_webhook()
    logger.info(f"Webhook setup result: {webhook_result}")
    
    return {
        "success": True,
        "supabase_connected": supabase_result,
        "webhook_setup": webhook_result
    }

# This is the main handler Vercel will call
def handler(request, context):
    """Vercel serverless function handler"""
    method = request.get('method', '')
    logger.info(f"Handler called with method: {method}")
    
    # Log entire request structure
    logger.info("🔍 COMPLETE REQUEST STRUCTURE: 🔍")
    logger.info(dump_object(request, "request"))
    
    # Health check endpoint
    if method == 'GET':
        try:
            # Run the async function synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            webhook_info = None
            if bot:
                try:
                    webhook_info = loop.run_until_complete(bot.get_webhook_info()).to_dict()
                except Exception as e:
                    logger.error(f"Error getting webhook info: {e}")
                    webhook_info = {"error": str(e)}
                    
            response = {
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
            }
            
            loop.close()
            
            return {
                'statusCode': 200,
                'body': json.dumps(response)
            }
        except Exception as e:
            logger.error(f"Error in GET handler: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }
    
    # Webhook endpoint
    elif method == 'POST':
        try:
            # Get raw body data and log it
            body_raw = request.get('body', '{}')
            logger.info(f"RAW BODY TYPE: {type(body_raw).__name__}")
            
            if isinstance(body_raw, str):
                logger.info(f"RAW BODY (STRING): {body_raw[:500]}")  # First 500 chars for safety
            elif isinstance(body_raw, dict):
                logger.info(f"RAW BODY (DICT): {json.dumps(body_raw)[:500]}")
            else:
                logger.info(f"RAW BODY (OTHER): {str(body_raw)[:500]}")
            
            # Parse body if it's a string
            if isinstance(body_raw, str):
                try:
                    body = json.loads(body_raw)
                    logger.info("Successfully parsed body as JSON")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse body as JSON: {e}")
                    # Try to extract the error location
                    lines = body_raw.split("\n")
                    error_line = e.lineno - 1 if e.lineno <= len(lines) else len(lines) - 1
                    error_context = lines[max(0, error_line-2):min(len(lines), error_line+3)]
                    logger.error(f"Error context: {error_context}")
                    
                    return {
                        'statusCode': 200,  # Still return 200 to avoid Telegram retries
                        'body': json.dumps({
                            'error': 'Invalid JSON',
                            'details': str(e),
                            'body_preview': body_raw[:100] + "..." if len(body_raw) > 100 else body_raw
                        })
                    }
            else:
                body = body_raw
                
            # Process the update
            logger.info(f"🔄 PROCESSING WEBHOOK UPDATE")
            
            # Run the async function synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Process the update
            result = loop.run_until_complete(handle_telegram_update(body))
            
            # Always close the loop
            loop.close()
            
            # Return a success response
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'processed': result
                })
            }
            
        except Exception as e:
            logger.error(f"Error in POST handler: {e}")
            # Include traceback for better debugging
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return {
                'statusCode': 200,  # Still return 200 to acknowledge to Telegram
                'body': json.dumps({'error': str(e)})
            }
            
    # Handle other methods
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }

# Initialize the bot and webhook on cold start
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    init_result = loop.run_until_complete(initialize())
    loop.close()
    logger.info(f"Initialization complete: {init_result}")
except Exception as e:
    logger.error(f"Error during initialization: {e}") 