import socket
import traceback

# --- FORCE IPv4 ---
orig_getaddrinfo = socket.getaddrinfo
def filtered_getaddrinfo(*args, **kwargs):
    res = orig_getaddrinfo(*args, **kwargs)
    return [r for r in res if r[0] == socket.AF_INET]
socket.getaddrinfo = filtered_getaddrinfo

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import threading
import aiohttp
import logging
from flask import Flask

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
PREFIX = "!"

# Setup DEBUG logging for discord to see exactly where it hangs
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(message)s')
logger = logging.getLogger('ThinkingSecurity')

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Diagnostic Mode"
def run_web(): app.run(host='0.0.0.0', port=7860)

# --- STARTUP ---
async def start_bot():
    print("--- STARTING ADVANCED NETWORK DIAGNOSTICS ---")
    headers = {'User-Agent': 'Mozilla/5.0'}
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        # TEST 1: GOOGLE (Baseline)
        print("Testing Google...")
        try:
            async with session.get("https://www.google.com", timeout=10) as resp:
                print(f"GOOGLE STATUS: {resp.status}")
        except Exception as e:
            print(f"GOOGLE FAILED: {e}")

        # TEST 2: DISCORD GATEWAY ENDPOINT
        print("Testing Discord Gateway Endpoint manually...")
        try:
            async with session.get("https://discord.com/api/v10/gateway", timeout=20) as resp:
                print(f"DISCORD API STATUS: {resp.status}")
                print(f"DISCORD API RESPONSE: {await resp.text()}")
        except Exception as e:
            print(f"DISCORD API FAILED: {e}")
            traceback.print_exc()

        if not TOKEN:
            print("FATAL: TOKEN MISSING")
            return

        async with bot:
            print("Attempting bot.login(TOKEN)...")
            try:
                # Login only (REST call)
                await asyncio.wait_for(bot.login(TOKEN), timeout=30)
                print("Login successful! Attempting bot.connect()...")
                # Connect only (WebSocket)
                await bot.connect()
            except Exception as e:
                print("BOT LOGIN/CONNECT FAILED!")
                traceback.print_exc()

if __name__ == '__main__':
    print("--- SCRIPT START ---")
    threading.Thread(target=run_web, daemon=True).start()
    try:
        asyncio.run(start_bot())
    except Exception:
        traceback.print_exc()
        import time
        while True: time.sleep(10)
