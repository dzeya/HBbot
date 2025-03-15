#!/usr/bin/env python
# This program is dedicated to the public domain under the CC0 license.

"""
Telegram Bot based on the python-telegram-bot library with Supabase database integration.
This bot will store user data and message history in Supabase while providing basic functionality.

To run this bot:
1. Make sure you have installed dependencies: pip install -r requirements.txt
2. Ensure your .env file contains SUPABASE_URL, SUPABASE_ANON_KEY, and TELEGRAM_TOKEN
3. Run this script: python my_telegram_bot.py
"""

import logging
import os
import datetime
import json
import uuid
from dotenv import load_dotenv

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Import our database module
import db

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    
    # Store user in database
    db.save_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    await update.message.reply_html(
        rf"Hello {user.mention_html()}! I'm your Telegram bot with Supabase integration. "
        rf"Send me any message and I'll echo it back to you while storing it in the database.",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "This bot will echo back any messages you send and store them in Supabase.\n\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/history - Show your most recent messages\n"
        "/stats - Show your usage statistics\n"
        "/test_db - Test the Supabase database connection\n"
        "/diagnostic - Run diagnostics to check bot health\n"
        "/setup_tables - Create the required database tables"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message and store it in the database."""
    user = update.effective_user
    message = update.message
    
    # Store message in database
    timestamp = datetime.datetime.now().isoformat()
    db.save_message(
        user_id=user.id,
        message_text=message.text,
        message_id=message.message_id,
        timestamp=timestamp
    )
    
    # Echo the message back
    await update.message.reply_text(update.message.text)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's message history."""
    user = update.effective_user
    
    # Retrieve user's message history
    messages = db.get_user_messages(user.id, limit=5)
    
    if not messages:
        await update.message.reply_text("You don't have any message history yet.")
        return
    
    # Format and send the history
    history_text = "Your most recent messages:\n\n"
    for msg in messages:
        # Format the timestamp for display
        try:
            timestamp = datetime.datetime.fromisoformat(msg["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        except:
            timestamp = msg["timestamp"]
            
        history_text += f"[{timestamp}] {msg['message_text']}\n"
    
    await update.message.reply_text(history_text)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show usage statistics for the user."""
    user = update.effective_user
    
    # Get user data from database
    user_data = db.get_user(user.id)
    if not user_data:
        await update.message.reply_text("No user data found.")
        return
    
    # Count total messages from this user
    messages = db.get_user_messages(user.id, limit=1000)  # Set a high limit to get all messages
    message_count = len(messages)
    
    # Save the stat
    db.save_user_data(user.id, "total_messages", message_count)
    
    # Send stats to user
    await update.message.reply_text(
        f"Stats for {user.first_name}:\n"
        f"Total messages sent: {message_count}\n"
        f"User since: {user_data.get('created_at', 'Unknown')}"
    )


async def test_db_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test the Supabase database connection and create test data."""
    user = update.effective_user
    
    try:
        # Step 1: Test the Supabase connection
        await update.message.reply_text("🔍 Testing Supabase connection...")
        connection_ok = db.test_connection()
        
        if not connection_ok:
            await update.message.reply_text(
                "❌ Could not connect to Supabase. Please check your credentials and network connection."
            )
            return
        
        await update.message.reply_text("✅ Supabase connection successful!")
        
        # Step 2: Test user operations
        await update.message.reply_text("👤 Testing user operations...")
        user_result = db.save_user(
            user_id=user.id, 
            username=user.username or "", 
            first_name=user.first_name, 
            last_name=user.last_name
        )
        
        if not user_result:
            await update.message.reply_text("⚠️ User was saved but no data was returned.")
        else:
            await update.message.reply_text(f"✅ User saved successfully with ID: {user_result.get('user_id')}")
        
        # Step 3: Create some test message data
        await update.message.reply_text("📝 Creating test messages...")
        message_ids = []
        test_messages = [
            f"Test message 1 - {uuid.uuid4()}",
            f"Test message 2 - {uuid.uuid4()}",
            f"Test message 3 - {uuid.uuid4()}"
        ]
        
        for i, msg_text in enumerate(test_messages):
            timestamp = (datetime.datetime.now() + datetime.timedelta(minutes=i)).isoformat()
            fake_msg_id = i+1000  # Fake message ID
            message_result = db.save_message(
                user_id=user.id,
                message_text=msg_text,
                message_id=fake_msg_id,
                timestamp=timestamp
            )
            if message_result:
                message_ids.append(message_result.get('id'))
        
        await update.message.reply_text(f"✅ Created {len(message_ids)} test messages")
        
        # Step 4: Save some test user preferences
        await update.message.reply_text("⚙️ Saving test user preferences...")
        preferences = {
            "theme": "dark",
            "notifications": True,
            "language": "en",
            "created_at": datetime.datetime.now().isoformat()
        }
        preferences_result = db.save_user_data(user.id, "preferences", preferences)
        
        if preferences_result:
            await update.message.reply_text("✅ User preferences saved successfully")
        else:
            await update.message.reply_text("⚠️ User preferences were saved but no data was returned")
        
        # Step 5: Verify we can retrieve the data
        await update.message.reply_text("🔍 Verifying data retrieval...")
        
        # Get user
        retrieved_user = db.get_user(user.id)
        if not retrieved_user:
            await update.message.reply_text("❌ Failed to retrieve user data")
            return
        
        # Get messages
        retrieved_messages = db.get_user_messages(user.id, limit=10)
        
        # Get preferences
        retrieved_prefs = db.get_user_data(user.id, "preferences")
        
        # Format results
        results = {
            "user": {
                "user_id": retrieved_user.get("user_id"),
                "username": retrieved_user.get("username"),
                "first_name": retrieved_user.get("first_name"),
                "created_at": retrieved_user.get("created_at")
            },
            "message_count": len(retrieved_messages),
            "latest_messages": [msg.get("message_text", "")[:30] + "..." for msg in retrieved_messages[:3]],
            "preferences": retrieved_prefs
        }
        
        # Send success message with the retrieved data
        await update.message.reply_text(
            "✅ Data verification successful!\n\n"
            f"Retrieved data:\n{json.dumps(results, indent=2)}"
        )
        
        # Final success message
        await update.message.reply_text(
            "🎉 Supabase integration test completed successfully!\n\n"
            "You can use these commands to interact with the data:\n"
            "/history - View your message history\n"
            "/stats - View your usage statistics"
        )
        
    except Exception as e:
        # If anything goes wrong, send an error message
        logger.error(f"Error testing Supabase: {str(e)}")
        await update.message.reply_text(
            f"❌ Error testing Supabase connection:\n{str(e)}\n\n"
            "Please check:\n"
            "1. Your .env configuration is correct\n"
            "2. The Supabase tables are set up correctly\n"
            "3. Your network connection to Supabase is working\n\n"
            "You can use the SQL in supabase_setup.sql to create the required tables."
        )


async def diagnostic_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run diagnostic checks on the bot and database connection."""
    user = update.effective_user
    
    await update.message.reply_text("🔍 Running diagnostics...")
    
    # Check environment variables
    env_check = []
    env_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
        "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN")
    }
    
    for var_name, var_value in env_vars.items():
        if not var_value:
            env_check.append(f"❌ {var_name} is missing")
        else:
            masked_value = var_value[:5] + "..." + var_value[-5:] if len(var_value) > 10 else "***"
            env_check.append(f"✅ {var_name} is set (value: {masked_value})")
    
    # Check Supabase connection
    try:
        connection_ok = db.test_connection()
        if connection_ok:
            supabase_check = "✅ Connected to Supabase successfully"
        else:
            supabase_check = "❌ Could not connect to Supabase"
    except Exception as e:
        supabase_check = f"❌ Error connecting to Supabase: {str(e)}"
    
    # Check database tables
    tables_check = []
    try:
        # Try to fetch user to check if user table exists
        user_data = db.get_user(user.id)
        if user_data:
            tables_check.append("✅ 'users' table accessible")
        else:
            tables_check.append("⚠️ 'users' table accessible but no data for current user")
        
        # Try some operations to test permissions
        test_result = db.save_user(user.id, user.username or "", user.first_name, user.last_name)
        if test_result:
            tables_check.append("✅ Write permission to 'users' table")
        else:
            tables_check.append("⚠️ Could write to 'users' table but no data returned")
            
    except Exception as e:
        tables_check.append(f"❌ Database operation error: {str(e)}")
    
    # Format and send diagnostic results
    diagnostic_result = (
        "📊 Bot Diagnostic Results\n\n"
        "🔑 Environment Variables:\n" + "\n".join(env_check) + "\n\n"
        "🗄️ Supabase Connection:\n" + supabase_check + "\n\n"
        "📋 Database Tables:\n" + "\n".join(tables_check) + "\n\n"
        "💻 System Info:\n"
        f"Python version: {'.'.join(map(str, __import__('sys').version_info[:3]))}\n"
        f"python-telegram-bot version: {__import__('telegram').__version__}\n"
        f"httpx version: {__import__('httpx').__version__}\n"
    )
    
    await update.message.reply_text(diagnostic_result)
    
    # Provide recommendations based on diagnostics
    if not connection_ok:
        await update.message.reply_text(
            "🔧 Troubleshooting recommendations:\n\n"
            "1. Check if your Supabase URL and key are correct\n"
            "2. Verify that the database tables are created\n"
            "3. Check if Supabase is running and accessible\n"
            "4. Try running the setup SQL script again\n"
            "5. Check if the environment variables are loaded correctly\n"
        )


async def setup_tables_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Setup the required Supabase tables."""
    user = update.effective_user
    
    # Check if user is the bot owner (only allow specific user to create tables)
    # Add your Telegram user ID here
    OWNER_USER_ID = user.id  # By default allow the current user, but you can restrict this
    
    if user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sorry, only the bot owner can run this command.")
        return
    
    await update.message.reply_text("🔧 Setting up database tables...")
    
    try:
        # First check if we can connect to Supabase at all
        if not db.test_connection():
            await update.message.reply_text(
                "❌ Cannot connect to Supabase. Please check your credentials in the .env file."
            )
            return
        
        # Try to create tables directly via REST API
        sql_statements = """
-- Enable UUID extension if not already enabled
create extension if not exists "uuid-ossp";

-- Users Table
create table public.users (
  id uuid not null default uuid_generate_v4(),
  created_at timestamp with time zone not null default now(),
  user_id bigint not null primary key,
  username text,
  first_name text not null,
  last_name text
);

-- Add row level security policies
alter table public.users enable row level security;

-- Create policy to allow insert and select for authenticated users
create policy "Allow full access to authenticated users"
  on public.users
  for all
  to authenticated
  using (true);
  
-- Create policy to allow public read access
create policy "Allow public read access"
  on public.users
  for select
  to anon
  using (true);

-- Message History Table
create table public.message_history (
  id uuid not null default uuid_generate_v4(),
  created_at timestamp with time zone not null default now(),
  user_id bigint not null references public.users(user_id),
  message_text text not null,
  message_id bigint not null,
  timestamp text not null
);

-- Create index on user_id for faster queries
create index message_history_user_id_idx on public.message_history(user_id);

-- Add row level security policies
alter table public.message_history enable row level security;

-- Create policy to allow insert and select for authenticated users
create policy "Allow full access to authenticated users"
  on public.message_history
  for all
  to authenticated
  using (true);

-- User Data Table for preferences, settings, etc.
create table public.user_data (
  id uuid not null default uuid_generate_v4(),
  created_at timestamp with time zone not null default now(),
  user_id bigint not null references public.users(user_id),
  data_key text not null,
  data_value jsonb not null,
  primary key (user_id, data_key)
);

-- Add row level security policies
alter table public.user_data enable row level security;

-- Create policy to allow insert and select for authenticated users
create policy "Allow full access to authenticated users"
  on public.user_data
  for all
  to authenticated
  using (true);
"""

        # The SQL API isn't directly accessible through REST API without admin rights
        # Instead, show the SQL to the user and provide instructions
        await update.message.reply_text(
            "⚠️ The bot cannot create tables directly.\n\n"
            "Please follow these steps to set up your database:\n\n"
            "1. Log in to your Supabase dashboard at https://app.supabase.io\n"
            "2. Go to your project\n"
            "3. Click on 'SQL Editor'\n"
            "4. Create a new query\n"
            "5. Copy and paste the SQL below\n"
            "6. Click 'Run' to execute the query\n\n"
            "After completing these steps, run the /test_db command to check if everything is working."
        )
        
        # Split the SQL into smaller messages if needed
        max_message_length = 4000
        sql_parts = [sql_statements[i:i+max_message_length] for i in range(0, len(sql_statements), max_message_length)]
        
        for part in sql_parts:
            await update.message.reply_text(f"```sql\n{part}\n```")
        
        await update.message.reply_text(
            "Once you've executed the SQL above, use /test_db to check if everything is working."
        )
        
    except Exception as e:
        logger.error(f"Error setting up tables: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN must be set in .env file")
    
    # Monkey patch httpx to avoid proxy issues
    import inspect
    import telegram.request._httpxrequest
    from telegram.request import HTTPXRequest
    
    # Override the HTTPXRequest class to fix proxy issues
    original_init = HTTPXRequest.__init__
    
    def patched_init(self, *args, **kwargs):
        # Remove proxy from kwargs if it exists
        if 'proxy' in kwargs:
            logger.warning("Removing proxy parameter from HTTPXRequest to avoid compatibility issues")
            kwargs.pop('proxy', None)
        # Call the original init without the proxy parameter
        if 'proxy_url' in inspect.signature(original_init).parameters:
            original_init(self, *args, **kwargs)
        else:
            # If no proxy_url parameter exists, remove it from kwargs if present
            if 'proxy_url' in kwargs:
                kwargs.pop('proxy_url', None)
            original_init(self, *args, **kwargs)
    
    # Apply the patch
    HTTPXRequest.__init__ = patched_init
    
    # Now build the application with base_url explicitly set to avoid proxy issues
    application = Application.builder().token(token).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("test_db", test_db_command))
    application.add_handler(CommandHandler("diagnostic", diagnostic_command))
    application.add_handler(CommandHandler("setup_tables", setup_tables_command))

    # Register message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    print("Bot started with Supabase integration! Press Ctrl+C to stop.")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except TypeError as e:
        if "got an unexpected keyword argument 'proxy'" in str(e):
            logger.error("Proxy error detected. Trying again with a different approach...")
            # Alternative method if patching doesn't work
            import telegram.ext
            telegram.ext._applicationbuilder._ApplicationBuilder.build = lambda self: None
            print("Please restart the bot with 'python my_telegram_bot.py'")
        else:
            raise


if __name__ == "__main__":
    main() 