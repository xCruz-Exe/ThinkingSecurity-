import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import threading
import aiohttp
import logging
import traceback
from flask import Flask

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
PREFIX = "!"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

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
    print("--- STARTING NETWORK TEST (NO IPV4 FORCE) ---")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # NO custom connector here - let the system decide (IPv4 or IPv6)
    async with aiohttp.ClientSession(headers=headers) as session:
        print("Testing Google...")
        try:
            async with session.get("https://www.google.com", timeout=10) as resp:
                print(f"GOOGLE STATUS: {resp.status}")
        except Exception as e:
            print(f"GOOGLE FAILED: {e}")

        print("Testing Discord API...")
        try:
            async with session.get("https://discord.com/api/v10/gateway", timeout=15) as resp:
                print(f"DISCORD API STATUS: {resp.status}")
        except Exception as e:
            print(f"DISCORD API FAILED: {e}")

        if not TOKEN:
            print("FATAL: TOKEN MISSING")
            return

        async with bot:
            print("Attempting login...")
            try:
                await asyncio.wait_for(bot.login(TOKEN), timeout=45)
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
