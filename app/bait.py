import os
import re
import redis
import logging
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Redis Connection
r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis-service'), port=6379, decode_responses=True)

# Attack Patterns (Signatures)
ATTACK_PATTERNS = {
    "SQL_Injection": r"('|\-\-|UNION|SELECT|DROP|OR 1=1)",
    "XSS": r"(<script>|alert\(|onerror=)",
    "Path_Traversal": r"(\.\.\/|\.\.\\)"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sentry Node | Secure Access</title>
    <style>
        body { background-color: #0f172a; color: #e2e8f0; font-family: 'Courier New', Courier, monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-container { background: #1e293b; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 350px; border-top: 4px solid #3b82f6; }
        .logo { text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; color: #3b82f6; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-size: 14px; color: #94a3b8; }
        input { width: 100%; padding: 10px; border: 1px solid #334155; border-radius: 4px; background: #0f172a; color: white; box-sizing: border-box; }
        .hidden { display: none; } /* Honeypot: Hidden from humans */
        button { width: 100%; padding: 12px; background: #3b82f6; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; transition: background 0.3s; }
        button:hover { background: #2563eb; }
        .warning { font-size: 11px; text-align: center; margin-top: 15px; color: #ef4444; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">🛡️ SENTRY OMNI-NODE</div>
        <form method="POST" action="/login">
            <div class="form-group">
                <label>AUTHORIZED IDENTIFIER</label>
                <input type="text" name="u" autocomplete="off" required>
            </div>
            <!-- HONEYPOT FIELD -->
            <input type="text" name="token_id" class="hidden" autocomplete="off">
            
            <div class="form-group">
                <label>ACCESS TOKEN</label>
                <input type="password" name="p" autocomplete="off" required>
            </div>
            <button type="submit">AUTHENTICATE</button>
        </form>
        <div class="warning">SYSTEM STATUS: ACTIVE. ALL UNAUTHORIZED ATTEMPTS ARE BANNED INSTANTLY.</div>
    </div>
</body>
</html>
"""

@app.before_request
def check_ban():
    # Capture the Real IP
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
    if r.exists(f"banned:{client_ip}"):
        return "<h1>403 Forbidden</h1><p>Node access revoked for this IP.</p>", 403

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
    user_val = request.form.get('u', '')
    honeypot_val = request.form.get('token_id', '') # Bot trap
    
    # 1. Check Honeypot (Behavioral Detection)
    if honeypot_val:
        ban_reason = "Bot/Honeypot Triggered"
        r.set(f"banned:{client_ip}", ban_reason)
        r.lpush("security_events", f"{client_ip}|{ban_reason}") # Notify Guard
        return "Security Violation.", 403

    # 2. Check Signatures (Pattern Detection)
    for name, pattern in ATTACK_PATTERNS.items():
        if re.search(pattern, user_val, re.IGNORECASE):
            r.set(f"banned:{client_ip}", name)
            r.lpush("security_events", f"{client_ip}|{name}") # Notify Guard
            return "Security Violation.", 403
            
    return "Authentication Failed.", 401

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
