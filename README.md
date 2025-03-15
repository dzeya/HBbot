# Telegram Bot with Supabase Integration

This project implements a Telegram bot that stores user messages in a Supabase PostgreSQL database.

## Setup Instructions

### Prerequisites

- Python 3.9+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- A Supabase account and project

### Environment Setup

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with the following variables:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

### Database Setup

There are two ways to set up the database tables:

#### Option 1: Using the Supabase SQL Editor

1. Log in to your Supabase dashboard
2. Go to the SQL Editor
3. Copy the contents of `setup_database.sql` and run it in the SQL Editor

#### Option 2: Using the REST API

1. Make sure your IP address is whitelisted in Supabase
2. Run the setup script:
   ```bash
   python setup_with_client.py
   ```

### Running the Bot

You can run the bot using either the Supabase client library or direct REST API calls:

#### Using Supabase Client (if you have connectivity issues, try the REST API version)

```bash
python bot.py
```

#### Using REST API (more reliable if you have connectivity issues)

```bash
python simple_bot_rest.py
```

## Troubleshooting

### Connection Issues

If you encounter "No route to host" errors:

1. Make sure your IP address is whitelisted in Supabase
2. Check if you're using IPv6 and try disabling it temporarily
3. Try using the REST API version of the bot which avoids direct PostgreSQL connections

### Database Issues

If tables don't exist or you can't access them:

1. Run the `create_tables_rest.py` script to check connectivity
2. Use the Supabase SQL Editor to run the `setup_database.sql` script manually

## Files in this Project

- `bot.py` - Main bot using Supabase client
- `simple_bot_rest.py` - Alternative bot using REST API
- `setup_database.sql` - SQL script to set up database tables
- `setup_with_client.py` - Script to set up database using Supabase client
- `create_tables_rest.py` - Script to check REST API connectivity
- `list_tables.py` - Script to list existing tables
- `minimal_test.py` - Minimal test for Supabase connectivity
- `requirements.txt` - Python dependencies

## License

MIT 