import socket

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
def home(): return "Bot Status Check"
def run_web(): app.run(host='0.0.0.0', port=7860)

# --- STARTUP ---
async def start_bot():
    print("--- STARTING CONNECTION TEST ---")
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # TEST CONNECTION TO DISCORD API
        try:
            print("Testing Discord API reachability...")
            async with session.get("https://discord.com/api/v10/gateway", timeout=15) as resp:
                print(f"API Response Status: {resp.status}")
                data = await resp.json()
                print(f"API Data: {data}")
        except Exception as e:
            print(f"API TEST FAILED: {e}")

        async with bot:
            print("Attempting to login to Discord...")
            try:
                # Increased timeout to 60 seconds
                await asyncio.wait_for(bot.login(TOKEN), timeout=60)
                print("Login successful! Connecting to gateway...")
                await bot.connect()
            except asyncio.TimeoutError:
                print("FATAL: LOGIN TIMEOUT (The server is blocking Discord)")
            except Exception as e:
                print(f"FATAL LOGIN ERROR: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    try:
        asyncio.run(start_bot())
    except Exception as e:
        print(f"GLOBAL CRASH: {e}")
        import time
        while True: time.sleep(10)
