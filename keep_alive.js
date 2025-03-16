// A simple Node.js script to keep the Vercel function warm by pinging it regularly
// You can run this on any server, including a free service like Glitch.com or Replit.com

const https = require('https');
const url = process.env.WEBHOOK_URL || 'https://your-vercel-app.vercel.app/api';

// Ping interval in milliseconds (5 minutes)
const PING_INTERVAL = 5 * 60 * 1000;

/**
 * Function to ping the webhook URL
 */
function pingWebhook() {
  console.log(`[${new Date().toISOString()}] Pinging webhook: ${url}`);
  
  https.get(url, (res) => {
    const { statusCode } = res;
    
    if (statusCode !== 200) {
      console.error(`Failed to ping webhook. Status Code: ${statusCode}`);
      return;
    }
    
    let rawData = '';
    res.on('data', (chunk) => { rawData += chunk; });
    
    res.on('end', () => {
      try {
        console.log(`[${new Date().toISOString()}] Webhook ping successful`);
      } catch (e) {
        console.error(`Error parsing response: ${e.message}`);
      }
    });
  }).on('error', (e) => {
    console.error(`Error pinging webhook: ${e.message}`);
  });
}

// Initial ping
pingWebhook();

// Set up interval for regular pings
setInterval(pingWebhook, PING_INTERVAL);

console.log(`Keep-alive service started. Pinging ${url} every ${PING_INTERVAL / 1000} seconds.`); 