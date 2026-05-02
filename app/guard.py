import os
import redis
import time
import requests

# Configuration from Environment Variables
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service')
DISCORD_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Redis Connection
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

def send_alert(ip, reason):
    """Sends a formatted embed alert to Discord."""
    if not DISCORD_URL:
        print("❌ CRITICAL: DISCORD_WEBHOOK_URL is not set.")
        return

    payload = {
        "embeds": [{
            "title": "🚨 Sentry Intrusion Alert",
            "description": "A malicious actor has been neutralized.",
            "color": 15548997, # Red
            "fields": [
                {"name": "Attacker IP", "value": f"`{ip}`", "inline": True},
                {"name": "Attack Type", "value": f"`{reason}`", "inline": True},
                {"name": "Status", "value": "🚫 **Permanently Banned**", "inline": False}
            ],
            "footer": {"text": "Active-Sentry v5 | Automated Defense"}
        }]
    }

    try:
        response = requests.post(DISCORD_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Discord Alert Failed: {e}")

def monitor():
    """Patrols the Redis 'security_events' queue."""
    print(f"🛡️ Guard active. Monitoring queue at {REDIS_HOST}...")
    
    while True:
        # Blocking pop: waits for data to appear in the list
        event = r.brpop("security_events", timeout=10)
        
        if event:
            # event is a tuple: (list_name, data)
            _, raw_data = event
            try:
                ip, reason = raw_data.split('|')
                print(f"🚨 ALERT: {ip} flagged for {reason}")
                send_alert(ip, reason)
            except ValueError:
                print(f"⚠️ Received malformed event data: {raw_data}")
        
        time.sleep(0.1)

if __name__ == "__main__":
    monitor()
