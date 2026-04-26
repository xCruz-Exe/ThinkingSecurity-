print("--- SCRIPT INITIALIZING... ---")

import sys
import traceback

try:
    print("--- IMPORTING LIBRARIES ---")
    import socket
    import discord
    from discord.ext import commands
    from discord.ui import Button, View
    import os
    from dotenv import load_dotenv
    import json
    import datetime
    import asyncio
    import re
    import threading
    import logging
    import io
    import aiohttp
    from flask import Flask
    # These might be heavy
    from modules import anti_phishing, anti_spam, anti_image_scam
    print("--- ALL LIBRARIES IMPORTED SUCCESSFULLY ---")
except Exception as e:
    print(f"--- IMPORT ERROR: {e} ---")
    traceback.print_exc()
    sys.exit(1)

# --- FORCE IPv4 ---
orig_getaddrinfo = socket.getaddrinfo
def filtered_getaddrinfo(*args, **kwargs):
    res = orig_getaddrinfo(*args, **kwargs)
    return [r for r in res if r[0] == socket.AF_INET]
socket.getaddrinfo = filtered_getaddrinfo

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
PREFIX = os.getenv('PREFIX', '!')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class ThinkingSecurityBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=intents)

    async def setup_hook(self):
        print("--- SETUP HOOK STARTING ---")
        try:
            synced = await self.tree.sync()
            print(f"--- SLASH COMMANDS SYNCED: {len(synced)} ---")
        except Exception as e:
            print(f"--- SYNC ERROR: {e} ---")

bot = ThinkingSecurityBot()

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Diagnostic Mode"
def run_web(): app.run(host='0.0.0.0', port=7860)

# --- STARTUP ---
async def start_bot():
    print("--- STARTING NETWORK DIAGNOSTICS ---")
    headers = {'User-Agent': 'Mozilla/5.0'}
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        print("Testing internet access...")
        try:
            async with session.get("https://www.google.com", timeout=10) as resp:
                print(f"GOOGLE STATUS: {resp.status}")
        except Exception as e:
            print(f"INTERNET TEST FAILED: {e}")

        if not TOKEN:
            print("FATAL: TOKEN MISSING")
            return

        async with bot:
            print("Attempting login...")
            try:
                await asyncio.wait_for(bot.login(TOKEN), timeout=60)
                print("Login successful! Connecting...")
                await bot.connect()
            except Exception as e:
                print("BOT LOGIN FAILED!")
                traceback.print_exc()

if __name__ == '__main__':
    print("--- SCRIPT ENTRY POINT ---")
    threading.Thread(target=run_web, daemon=True).start()
    try:
        asyncio.run(start_bot())
    except Exception as e:
        traceback.print_exc()
        import time
        while True: time.sleep(10)
