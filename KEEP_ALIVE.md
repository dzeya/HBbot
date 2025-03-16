# Keep-Alive Service for Telegram Bot

This document explains how to set up a keep-alive service to ensure your Telegram bot deployed on Vercel responds in real-time, without the delays caused by cold starts.

## Understanding the Problem

When deploying a Telegram bot on Vercel's serverless functions, you might experience delays in responses due to "cold starts". This happens because:

1. Vercel's serverless functions go "cold" (get unloaded from memory) after a period of inactivity
2. When a new request comes in, Vercel needs to "warm up" the function (load it into memory again)
3. This cold start process can take several seconds

If your bot isn't constantly receiving messages, it might only respond once every 20-30 minutes when Vercel's functions go cold.

## Solution: Keep-Alive Service

The solution is to use an external service to periodically ping your webhook URL, keeping the function "warm".

### Option 1: Using a Free Hosting Service

You can run the included `keep_alive.js` script on a free hosting service like:

- [Glitch.com](https://glitch.com/)
- [Replit.com](https://replit.com/)
- [Render.com](https://render.com/) (free tier)

#### Setup Instructions:

1. Create an account on one of the services above
2. Create a new Node.js project
3. Upload the `keep_alive.js` file from this repository
4. Set the environment variable `WEBHOOK_URL` to your Vercel deployment URL (e.g., `https://your-bot.vercel.app/api`)
5. Start the service

### Option 2: Using a Cron Job Service

You can use a free cron job service to ping your webhook URL regularly:

- [Cron-job.org](https://cron-job.org/)
- [UptimeRobot](https://uptimerobot.com/)
- [Pingdom](https://www.pingdom.com/) (has a free tier)

#### Setup Instructions:

1. Create an account on one of the services above
2. Set up a new monitoring job/cron job
3. Set the URL to your Vercel deployment URL (e.g., `https://your-bot.vercel.app/api`)
4. Set the interval to 5 minutes
5. Activate the monitoring

### Option 3: Using GitHub Actions

You can use GitHub Actions to periodically ping your webhook:

1. In your repository, create a directory `.github/workflows/`
2. Create a file named `keep-alive.yml` with the following content:

```yaml
name: Keep Alive

on:
  schedule:
    - cron: '*/5 * * * *'  # Run every 5 minutes

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
    - name: Ping webhook
      run: curl -sS ${{ secrets.WEBHOOK_URL }}
```

3. In your GitHub repository settings, add a secret named `WEBHOOK_URL` with your Vercel deployment URL

## Vercel Pro Plan Alternative

If you're using Vercel Pro, you can enable "Always On" functions to prevent cold starts:

1. Upgrade to Vercel Pro
2. In your project settings, enable "Always On" functions

## Troubleshooting

If you're still experiencing delays:

1. Check if your keep-alive service is running correctly
2. Ensure it's pinging the correct URL
3. Try decreasing the ping interval to 2-3 minutes
4. Verify that your Telegram webhook is set correctly

By implementing any of these solutions, your Telegram bot should respond in real-time instead of only processing messages every 20 minutes. 