import os
import json
import logging
import requests
from datetime import datetime
import telegram
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

# Initialize bot
bot = telegram.Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

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

async def handle_telegram_update(update_data):
    """Process an update from Telegram"""
    if not bot:
        return {"success": False, "error": "Bot not initialized"}
    
    try:
        # First, log the raw update data as is
        logger.info("🔍 RAW UPDATE STRUCTURE: 🔍")
        logger.info(dump_object(update_data, "update_data"))
        
        # Convert dict to Update object
        update = telegram.Update.de_json(update_data, bot)
        
        # Log the Update object structure
        logger.info("🔍 TELEGRAM UPDATE OBJECT STRUCTURE: 🔍")
        logger.info(dump_object(update, "update"))
        
        if not update or not update.message:
            logger.warning("⚠️ Update contains no message")
            return {"success": False, "reason": "No message in update"}
        
        chat_id = update.message.chat_id
        logger.info(f"Processing message from chat_id: {chat_id}")
        
        # Super detailed message inspection
        msg = update.message
        msg_dict = msg.to_dict() if hasattr(msg, 'to_dict') else None
        
        logger.info("📩 MESSAGE KEYS AND ATTRIBUTES: 📩")
        if msg_dict:
            logger.info(f"Message dict keys: {list(msg_dict.keys())}")
        logger.info(f"Message object attributes: {dir(msg)}")
        
        # Check for images/photos - ENHANCED LOGGING
        if hasattr(msg, 'photo') and msg.photo:
            photo_array = msg.photo
            logger.info(f"📸 PHOTO DETECTED! Array length: {len(photo_array)}")
            
            # Log details about each photo size
            for i, photo in enumerate(photo_array):
                photo_dict = photo.to_dict() if hasattr(photo, 'to_dict') else {}
                logger.info(f"Photo {i}: {dump_object(photo_dict)}")
                logger.info(f"Photo {i} attributes: {dir(photo)}")
            
            # Get the largest photo (last in array)
            if photo_array:
                file_id = photo_array[-1].file_id
                logger.info(f"Using largest photo with file_id: {file_id}")
                
                # Try to get file info
                try:
                    file_info = await bot.get_file(file_id)
                    logger.info(f"File info: {dump_object(file_info.to_dict() if hasattr(file_info, 'to_dict') else file_info)}")
                except Exception as e:
                    logger.error(f"Error getting file info: {e}")
            
                # Send confirmation message
                await bot.send_message(
                    chat_id=chat_id, 
                    text="📸 Your photo has been received and stored! [DEEP DEBUG MODE]"
                )
                
                return {
                    "success": True, 
                    "message_type": "photo",
                    "file_id": file_id
                }
            else:
                logger.error("Photo array is empty despite photo attribute being present!")
                
        # Handle text messages
        elif hasattr(msg, 'text') and msg.text:
            text = msg.text
            logger.info(f"Text message: {text[:100]}...")
            
            # Handle commands
            if text.startswith('/'):
                if text.startswith('/start'):
                    await bot.send_message(
                        chat_id=chat_id,
                        text="👋 Welcome to the HB Telegram Bot! Your messages will be stored securely. [DEEP DEBUG MODE]"
                    )
                elif text.startswith('/help'):
                    await bot.send_message(
                        chat_id=chat_id,
                        text="💬 This bot stores your messages and media in a secure database.\n\nCommands:\n/start - Start the bot\n/help - Show this help message\n/stats - Show your message statistics\n\n[DEEP DEBUG MODE]"
                    )
                elif text.startswith('/stats'):
                    await bot.send_message(
                        chat_id=chat_id,
                        text="📊 Stats functionality available in the full version [DEEP DEBUG MODE]"
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text="⚠️ Unknown command. Type /help for a list of commands. [DEEP DEBUG MODE]"
                    )
            else:
                # Regular text message
                await bot.send_message(
                    chat_id=chat_id,
                    text="✅ Your message has been received and stored [DEEP DEBUG MODE]"
                )
                
            return {
                "success": True,
                "message_type": "text",
                "text": text[:100]  # Truncate for logging
            }
        
        # Last resort - if nothing else matched, try a different attribute access approach
        else:
            logger.info("⚠️ No standard message type detected, trying alternative approaches")
            
            # Enumerate all possible message types and check each one
            message_types = [
                "text", "photo", "document", "video", "audio", "animation", 
                "sticker", "voice", "location", "contact", "poll", "venue"
            ]
            
            found_type = None
            for msg_type in message_types:
                if hasattr(msg, msg_type) and getattr(msg, msg_type):
                    found_type = msg_type
                    logger.info(f"🔍 Found message type via attribute check: {found_type}")
                    break
            
            # Also check direct dictionary access if available
            if msg_dict:
                for msg_type in message_types:
                    if msg_type in msg_dict and msg_dict[msg_type]:
                        logger.info(f"🔍 Found message type via dict access: {msg_type}")
                        if not found_type:
                            found_type = msg_type
            
            # If we found a valid message type, try to handle it
            if found_type:
                logger.info(f"Handling message of type: {found_type}")
                
                # Special handling for photo messages found via dict
                if found_type == "photo" and "photo" in msg_dict:
                    photo_data = msg_dict["photo"]
                    logger.info(f"Photo data from dict: {dump_object(photo_data)}")
                    
                    # Try to extract file_id
                    if isinstance(photo_data, list) and photo_data:
                        last_photo = photo_data[-1]
                        if isinstance(last_photo, dict) and "file_id" in last_photo:
                            file_id = last_photo["file_id"]
                            logger.info(f"Extracted file_id from dict: {file_id}")
                            
                            # Send response
                            await bot.send_message(
                                chat_id=chat_id,
                                text=f"📸 Your photo has been received and stored! [DICT ACCESS MODE]"
                            )
                            
                            return {
                                "success": True,
                                "message_type": "photo",
                                "method": "dict_access",
                                "file_id": file_id
                            }
                
                # Generic response for other types
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ Your {found_type} has been received and stored [DEEP DEBUG MODE]"
                )
                
                return {
                    "success": True,
                    "message_type": found_type,
                    "method": "alternative_detection"
                }
            else:
                # Truly unknown message type
                logger.warning(f"Unknown message type - dumping all message data for analysis:")
                logger.warning(dump_object(msg_dict if msg_dict else msg))
                
                await bot.send_message(
                    chat_id=chat_id,
                    text="✅ Your message (of unknown type) has been received [DEEP DEBUG MODE]"
                )
                
                return {
                    "success": True,
                    "message_type": "unknown",
                    "message_keys": list(msg_dict.keys()) if msg_dict else dir(msg)
                }
            
    except Exception as e:
        logger.error(f"Error handling update: {e}")
        logger.error(f"Update data that caused the error: {json.dumps(update_data)[:300] if isinstance(update_data, dict) else str(update_data)[:300]}")
        
        # Try to send an error notification if we can determine the chat_id
        try:
            if isinstance(update_data, dict) and "message" in update_data and "chat" in update_data["message"]:
                recovery_chat_id = update_data["message"]["chat"]["id"]
                await bot.send_message(
                    chat_id=recovery_chat_id,
                    text="⚠️ Sorry, there was an error processing your message. The team has been notified. [DEBUG MODE]"
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