import socket

# --- CRITICAL: FORCE IPv4 BEFORE ANY OTHER IMPORTS ---
orig_getaddrinfo = socket.getaddrinfo
def filtered_getaddrinfo(*args, **kwargs):
    res = orig_getaddrinfo(*args, **kwargs)
    return [r for r in res if r[0] == socket.AF_INET]
socket.getaddrinfo = filtered_getaddrinfo

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import datetime
import asyncio
import threading
import logging
import sys
import aiohttp
from flask import Flask
from modules import anti_phishing, anti_spam, anti_image_scam

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID_RAW = os.getenv('LOG_CHANNEL_ID')
LOG_CHANNEL_ID = int(LOG_CHANNEL_ID_RAW) if LOG_CHANNEL_ID_RAW and LOG_CHANNEL_ID_RAW.strip().isdigit() else None
PREFIX = "!"

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

# --- DATABASE MOCK ---
CONFIG = {"log_channel": LOG_CHANNEL_ID, "strikes": {}}
def get_config(key): return CONFIG.get(key)
def add_strike(user_id, reason):
    user_id = str(user_id)
    if user_id not in CONFIG["strikes"]: CONFIG["strikes"][user_id] = []
    CONFIG["strikes"][user_id].append({"reason": reason, "time": str(datetime.datetime.now())})
    return len(CONFIG["strikes"][user_id])

# --- HELPERS ---
async def send_log(guild, embed):
    cid = get_config("log_channel")
    if cid:
        c = guild.get_channel(int(cid))
        if c: await c.send(embed=embed)

async def apply_strike(member, reason, message=None):
    sc = add_strike(member.id, reason)
    emb = discord.Embed(title="Security Alert", color=discord.Color.orange())
    emb.add_field(name="User", value=f"{member.mention}")
    emb.add_field(name="Reason", value=reason)
    if message: await message.delete()
    await send_log(member.guild, emb)

# --- EVENTS ---
@bot.event
async def on_ready():
    print("================================")
    print(f"BOT IS ONLINE AS: {bot.user}")
    print(f"ID: {bot.user.id}")
    print("================================")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    if message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return
    # Simple invite check
    if "discord.gg/" in message.content:
        await apply_strike(message.author, "Invite Link", message)
        return
    await bot.process_commands(message)

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is live!"
def run_web(): app.run(host='0.0.0.0', port=7860)

# --- STARTUP ---
async def start_bot():
    print("--- START_BOT FUNCTION CALLED ---")
    if not TOKEN:
        print("FATAL: TOKEN MISSING")
        return
    
    print("--- CREATING CONNECTOR ---")
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        async with bot:
            print("--- LOGGING IN... ---")
            try:
                # Use a smaller timeout for the login request
                await asyncio.wait_for(bot.login(TOKEN), timeout=30)
                print("--- LOGIN SUCCESSFUL! CONNECTING TO GATEWAY... ---")
                await bot.connect()
            except asyncio.TimeoutError:
                print("FATAL: LOGIN TIMEOUT (Check Token or Network)")
            except Exception as e:
                print(f"FATAL LOGIN ERROR: {e}")

if __name__ == '__main__':
    print("--- SCRIPT STARTED ---")
    threading.Thread(target=run_web, daemon=True).start()
    print("--- WEB SERVER THREAD STARTED ---")
    try:
        asyncio.run(start_bot())
    except Exception as e:
        print(f"GLOBAL CRASH: {e}")
        import time
        while True: time.sleep(10)
