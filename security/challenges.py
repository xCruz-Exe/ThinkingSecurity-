import time
import hashlib
import random
import string
from fastapi.responses import HTMLResponse

class ChallengeManager:
    def __init__(self, secret="change-this-secret"):
        self.secret = secret

    def generate_token(self, ip: str) -> str:
        # Simple time-based token
        ts = int(time.time() // 3600)  # Valid for 1 hour
        data = f"{ip}:{ts}:{self.secret}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_token(self, ip: str, token: str) -> bool:
        expected = self.generate_token(ip)
        return token == expected

    def get_challenge_page(self, target_url: str) -> HTMLResponse:
        # A simple JS challenge that requires the browser to wait 3 seconds and then redirect
        # This filters out most simple botnets that don't execute JS or handle complex flows.
        
        # In a real professional version, we would use a more complex math challenge.
        html = f"""
        <html>
        <head>
            <title>Thinking Security - Browser Check</title>
            <style>
                body {{ font-family: sans-serif; text-align: center; padding: 50px; background: #010409; color: white; }}
                .spinner {{ border: 4px solid rgba(255,255,255,0.1); border-left-color: #58a6ff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }}
                @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <h1>Thinking Security Checking...</h1>
            <p>Please wait specialized protection is securing your session.</p>
            <div class="spinner"></div>
            <script>
                setTimeout(function() {{
                    window.location.reload();
                }}, 2500);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=403)
