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
from flask import Flask

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
PREFIX = "!"

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
    print("--- STARTING NETWORK DIAGNOSTICS ---")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        # TEST 1: DISCORD API
        print("Testing connection to Discord API...")
        try:
            async with session.get("https://discord.com/api/v10/gateway", timeout=20) as resp:
                print(f"DISCORD API STATUS: {resp.status}")
                print(f"DISCORD API BODY: {await resp.text()}")
        except Exception:
            print("DISCORD API TEST FAILED!")
            traceback.print_exc()

        # TEST 2: GOOGLE (To check if external networking works at all)
        print("Testing general internet access (Google)...")
        try:
            async with session.get("https://www.google.com", timeout=10) as resp:
                print(f"GOOGLE STATUS: {resp.status}")
        except Exception:
            print("GENERAL INTERNET ACCESS FAILED!")
            traceback.print_exc()

        if not TOKEN or len(TOKEN) < 30:
            print("FATAL: BOT_TOKEN is missing or too short! Please check HF Secrets.")
            return

        async with bot:
            print(f"Attempting login with token: {TOKEN[:10]}...{TOKEN[-5:]}")
            try:
                await asyncio.wait_for(bot.login(TOKEN), timeout=60)
                print("Login successful! Connecting...")
                await bot.connect()
            except Exception:
                print("BOT LOGIN FAILED!")
                traceback.print_exc()

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    try:
        asyncio.run(start_bot())
    except Exception:
        traceback.print_exc()
        import time
        while True: time.sleep(10)
