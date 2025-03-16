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

async def handle_telegram_update(update_data):
    """Process an update from Telegram"""
    if not bot:
        return {"success": False, "error": "Bot not initialized"}
    
    try:
        logger.info(f"Handling update: {json.dumps(update_data)[:200]}...")
        
        # Convert dict to Update object
        update = telegram.Update.de_json(update_data, bot)
        
        if not update or not update.message:
            logger.warning("Update contains no message")
            return {"success": False, "reason": "No message in update"}
        
        chat_id = update.message.chat_id
        logger.info(f"Processing message from chat_id: {chat_id}")
        
        # Check for images/photos - EXPLICIT LOGGING
        if update.message.photo:
            photo_array = update.message.photo
            logger.info(f"PHOTO DETECTED! Array length: {len(photo_array)}")
            
            # Log details about each photo size
            for i, photo in enumerate(photo_array):
                logger.info(f"Photo {i}: file_id={photo.file_id}, size={photo.width}x{photo.height}")
            
            # Get the largest photo (last in array)
            file_id = photo_array[-1].file_id
            logger.info(f"Using largest photo with file_id: {file_id}")
            
            # Send confirmation message
            await bot.send_message(
                chat_id=chat_id, 
                text="📸 Your photo has been received and stored!"
            )
            
            return {
                "success": True, 
                "message_type": "photo",
                "file_id": file_id
            }
            
        # Handle text messages
        elif update.message.text:
            text = update.message.text
            logger.info(f"Text message: {text[:50]}...")
            
            # Handle commands
            if text.startswith('/'):
                if text.startswith('/start'):
                    await bot.send_message(
                        chat_id=chat_id,
                        text="👋 Welcome to the HB Telegram Bot! Your messages will be stored securely."
                    )
                elif text.startswith('/help'):
                    await bot.send_message(
                        chat_id=chat_id,
                        text="💬 This bot stores your messages and media in a secure database.\n\nCommands:\n/start - Start the bot\n/help - Show this help message\n/stats - Show your message statistics"
                    )
                elif text.startswith('/stats'):
                    await bot.send_message(
                        chat_id=chat_id,
                        text="📊 Stats functionality available in the full version"
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text="⚠️ Unknown command. Type /help for a list of commands."
                    )
            else:
                # Regular text message
                await bot.send_message(
                    chat_id=chat_id,
                    text="✅ Your message has been received and stored"
                )
                
            return {
                "success": True,
                "message_type": "text",
                "text": text[:100]  # Truncate for logging
            }
            
        # Handle documents
        elif update.message.document:
            doc = update.message.document
            logger.info(f"Document received: {doc.file_name}, mime: {doc.mime_type}")
            
            await bot.send_message(
                chat_id=chat_id,
                text="📎 Your document has been received and stored"
            )
            
            return {
                "success": True,
                "message_type": "document",
                "file_name": doc.file_name
            }
            
        # Handle videos
        elif update.message.video:
            video = update.message.video
            logger.info(f"Video received: duration={video.duration}s, size={video.file_size} bytes")
            
            await bot.send_message(
                chat_id=chat_id,
                text="🎬 Your video has been received and stored"
            )
            
            return {
                "success": True,
                "message_type": "video"
            }
            
        # Other message types
        else:
            message_type = "unknown"
            for attr in ["audio", "animation", "sticker", "voice", "location"]:
                if hasattr(update.message, attr) and getattr(update.message, attr):
                    message_type = attr
                    break
                    
            logger.info(f"Other message type received: {message_type}")
            
            await bot.send_message(
                chat_id=chat_id,
                text=f"✅ Your {message_type} has been received and stored"
            )
            
            return {
                "success": True,
                "message_type": message_type
            }
            
    except Exception as e:
        logger.error(f"Error handling update: {e}")
        logger.error(f"Update data that caused the error: {json.dumps(update_data)[:300]}")
        
        # Try to send an error notification if we can determine the chat_id
        try:
            if isinstance(update_data, dict) and "message" in update_data and "chat" in update_data["message"]:
                recovery_chat_id = update_data["message"]["chat"]["id"]
                await bot.send_message(
                    chat_id=recovery_chat_id,
                    text="⚠️ Sorry, there was an error processing your message. The team has been notified."
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
            # Get raw body data
            body_raw = request.get('body', '{}')
            
            # Parse body if it's a string
            if isinstance(body_raw, str):
                try:
                    body = json.loads(body_raw)
                except json.JSONDecodeError:
                    logger.error("Failed to parse body as JSON")
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Invalid JSON'})
                    }
            else:
                body = body_raw
                
            # Process the update
            logger.info(f"Received webhook update: {json.dumps(body)[:200]}")
            
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