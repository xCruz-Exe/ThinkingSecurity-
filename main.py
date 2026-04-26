import socket

# --- CRITICAL: FORCE IPv4 BEFORE ANY OTHER IMPORTS ---
orig_getaddrinfo = socket.getaddrinfo
def filtered_getaddrinfo(*args, **kwargs):
    res = orig_getaddrinfo(*args, **kwargs)
    return [r for r in res if r[0] == socket.AF_INET]
socket.getaddrinfo = filtered_getaddrinfo

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
import sys
import aiohttp
from flask import Flask
from modules import anti_phishing, anti_spam, anti_image_scam

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID_RAW = os.getenv('LOG_CHANNEL_ID')
LOG_CHANNEL_ID = int(LOG_CHANNEL_ID_RAW) if LOG_CHANNEL_ID_RAW and LOG_CHANNEL_ID_RAW.strip().isdigit() else None
PREFIX = os.getenv('PREFIX', '!')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')
logger = logging.getLogger('ThinkingSecurity')

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class ThinkingSecurityBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX, 
            intents=intents,
            help_command=commands.DefaultHelpCommand(no_category="Thinking Security Bot Commands")
        )

    async def setup_hook(self):
        print("Hooking into system and syncing commands...")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands.")
        except Exception as e:
            print(f"Sync Error: {e}")

bot = ThinkingSecurityBot()

# --- DATABASE MOCK ---
CONFIG = {"log_channel": LOG_CHANNEL_ID, "strikes": {}}

def set_config(key, value): CONFIG[key] = value
def get_config(key): return CONFIG.get(key)
def add_strike(user_id, reason):
    user_id = str(user_id)
    if user_id not in CONFIG["strikes"]: CONFIG["strikes"][user_id] = []
    CONFIG["strikes"][user_id].append({"reason": reason, "time": str(datetime.datetime.now())})
    return len(CONFIG["strikes"][user_id])

# --- HELPERS ---
async def send_log(guild, embed):
    channel_id = get_config("log_channel")
    if channel_id:
        try:
            channel = guild.get_channel(int(channel_id))
            if channel: await channel.send(embed=embed)
        except Exception as e: print(f"Log Error: {e}")

async def apply_strike(member, reason, message=None):
    strike_count = add_strike(member.id, reason)
    embed = discord.Embed(title="Security Alert: Strike Applied", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Total Strikes", value=str(strike_count), inline=True)
    if message:
        embed.add_field(name="Message", value=message.content[:1024], inline=False)
        try: await message.delete()
        except: pass
    await send_log(member.guild, embed)
    if strike_count >= 3:
        try: await member.timeout(discord.utils.utcnow() + datetime.timedelta(hours=24), reason="3+ Strikes")
        except: pass

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Thinking Security System Active and Online!")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    if message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return
    if "discord.gg/" in message.content or "discord.com/invite/" in message.content:
        await apply_strike(message.author, "Invite Link", message)
        return
    is_spam, reason = anti_spam.is_spamming(message.author.id, message.content)
    if is_spam:
        await apply_strike(message.author, f"Spam: {reason}", message)
        return
    urls = anti_phishing.extract_urls(message.content)
    for url in urls:
        is_phish, res = await anti_phishing.is_phishing(url)
        if is_phish:
            await apply_strike(message.author, f"Phishing: {res}", message)
            return
    if message.attachments:
        for attachment in message.attachments:
            is_scam, res = await anti_image_scam.is_scam_image(attachment)
            if is_scam:
                await apply_strike(message.author, f"Scam Image: {res}", message)
                return
    await bot.process_commands(message)

# --- COMMANDS ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_logs(ctx, channel: discord.TextChannel):
    set_config("log_channel", channel.id)
    await ctx.send(f"✅ Logs set to {channel.mention}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Thinking Security Bot is live!"
def run_web(): app.run(host='0.0.0.0', port=7860)

# --- STARTUP ---
async def start_bot():
    if not TOKEN:
        print("ERROR: BOT_TOKEN is missing!")
        return
    
    # Force IPv4 in aiohttp session
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with bot:
            print("Starting bot session with IPv4 force...")
            await bot.start(TOKEN)

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    try:
        asyncio.run(start_bot())
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import time
        while True: time.sleep(10)
