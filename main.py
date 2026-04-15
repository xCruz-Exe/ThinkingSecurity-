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
from flask import Flask
from modules import anti_phishing, anti_spam, anti_image_scam
import logging
import io
import sys

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')
PREFIX = "!"

# Setup logging to capture terminal output for !logs command
log_stream = io.StringIO()
logging.basicConfig(level=logging.INFO, stream=log_stream, format='%(asctime)s: %(message)s')
class WebLogger(io.StringIO):
    def write(self, s):
        log_stream.write(s)
        sys.__stdout__.write(s)
sys.stdout = WebLogger()

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
        # Database/Config Initialization if needed
        pass

bot = ThinkingSecurityBot()

# --- DATABASE MOCK (Using simple JSON or config for demo) ---
CONFIG = {"log_channel": LOG_CHANNEL_ID, "strikes": {}}

def set_config(key, value): CONFIG[key] = value
def get_config(key): return CONFIG.get(key)
def add_strike(user_id, reason):
    user_id = str(user_id)
    if user_id not in CONFIG["strikes"]: CONFIG["strikes"][user_id] = []
    CONFIG["strikes"][user_id].append({"reason": reason, "time": str(datetime.datetime.now())})
    return len(CONFIG["strikes"][user_id])

# ─── SECURITY HELPER LOGIC ────────────────────────────────────────

async def send_log(guild, embed):
    """Helper to send logs to the configured channel."""
    channel_id = get_config("log_channel")
    if channel_id:
        channel = guild.get_channel(int(channel_id))
        if channel:
            await channel.send(embed=embed)

async def apply_strike(member, reason, message=None):
    """Apply a strike and handle punishments."""
    strike_count = add_strike(member.id, reason)
    
    embed = discord.Embed(
        title="⚠️ Security Alert: Strike Applied",
        color=discord.Color.orange(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Total Strikes", value=str(strike_count), inline=True)
    embed.set_footer(text="Thinking Security Bot")
    
    if message:
        embed.add_field(name="Message Content", value=message.content[:1024], inline=False)
        await message.delete()

    await send_log(member.guild, embed)

    if strike_count >= 3:
        await member.timeout(discord.utils.utcnow() + datetime.timedelta(hours=24), reason="3+ Security Strikes")
        punish_embed = discord.Embed(title="🔇 User Timed Out", description=f"{member.mention} timed out for 24h.", color=discord.Color.red())
        await send_log(member.guild, punish_embed)

# ─── BOT EVENTS ───────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Thinking Security System Active')

@bot.event
async def on_member_join(member):
    """Log when a new member joins the server."""
    embed = discord.Embed(
        title="📥 New Member Joined",
        description=f"{member.mention} has joined the server.",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url if member.display_avatar else None)
    embed.add_field(name="User", value=f"{member.name}", inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.set_footer(text="Thinking Security Bot | Join Log")
    
    await send_log(member.guild, embed)

@bot.event
async def on_message_delete(message):
    """Log when a single message is deleted."""
    if message.author.bot: return  # Ignore bot deletions
    
    embed = discord.Embed(
        title="🗑️ Message Deleted",
        description=f"A message from {message.author.mention} was deleted in {message.channel.mention}.",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    if message.content:
        embed.add_field(name="Content", value=message.content[:1024], inline=False)
    
    embed.set_footer(text=f"User ID: {message.author.id} | Thinking Security")
    await send_log(message.guild, embed)

@bot.event
async def on_bulk_message_delete(messages):
    """Log when multiple messages are deleted at once."""
    if not messages: return
    guild = messages[0].guild
    channel = messages[0].channel
    
    embed = discord.Embed(
        title="🧹 Bulk Messages Deleted",
        description=f"**{len(messages)}** messages were cleared/deleted in {channel.mention}.",
        color=discord.Color.dark_red(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="Thinking Security Bot | Audit Log")
    await send_log(guild, embed)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    if message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return

    # 1. Anti-Invite
    if "discord.gg/" in message.content or "discord.com/invite/" in message.content:
        await apply_strike(message.author, "Internal Discord Invite", message)
        return

    # 2. Anti-Spam
    is_spam, spam_reason = anti_spam.is_spamming(message.author.id, message.content)
    if is_spam:
        await apply_strike(message.author, f"Spam: {spam_reason}", message)
        return

    # 3. Phishing Links
    urls = anti_phishing.extract_urls(message.content)
    for url in urls:
        is_phish, phish_reason = await anti_phishing.is_phishing(url)
        if is_phish:
            await apply_strike(message.author, f"Phishing: {phish_reason}", message)
            return

    # 4. Scam Images
    if message.attachments:
        for attachment in message.attachments:
            is_scam, res = await anti_image_scam.is_scam_image(attachment)
            if is_scam:
                await apply_strike(message.author, f"Scam Image: {res}", message)
                return
            elif res:
                debug_embed = discord.Embed(title="🔍 Scanner Debug", description=f"Image from {message.author.mention}\nResult: `{res}`", color=discord.Color.blue())
                await send_log(message.guild, debug_embed)

    await bot.process_commands(message)

# ─── COMMANDS ─────────────────────────────────────────────────────

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_logs(ctx, channel: discord.TextChannel):
    set_config("log_channel", channel.id)
    await ctx.send(f"✅ Security logs will be sent to {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def logs(ctx):
    log_data = log_stream.getvalue()
    lines = log_data.strip().split('\n')
    output = "\n".join(lines[-15:])
    await ctx.send(f"```\n{output or 'No logs yet.'}\n```")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

# Web Server
app = Flask('')
@app.route('/')
def home(): return "Thinking Security Bot is live!"
def run(): app.run(host='0.0.0.0', port=7860)
def keep_alive(): threading.Thread(target=run).start()

if __name__ == '__main__':
    if TOKEN:
        keep_alive()
        bot.run(TOKEN)
    else:
        print("Set BOT_TOKEN in .env!")
