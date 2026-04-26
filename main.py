import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import threading
import logging
from flask import Flask

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
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
            help_command=commands.DefaultHelpCommand(no_category="Thinking Security Bot")
        )

    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("Slash commands synced successfully.")
        except Exception as e:
            print(f"Slash sync error: {e}")

bot = ThinkingSecurityBot()

# --- WEB SERVER (For Render Health Check) ---
app = Flask('')

@app.route('/')
def home():
    return "Thinking Security Bot is Live!"

def run_web():
    # Render provides a PORT environment variable
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Thinking Security System Active')

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    # Skip admins for security checks
    if message.author.guild_permissions.administrator:
        await bot.process_commands(message)
        return
    
    # Basic security check example (Anti-Invite)
    if "discord.gg/" in message.content or "discord.com/invite/" in message.content:
        try:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, invite links are not allowed here!", delete_after=5)
        except: pass
        return

    await bot.process_commands(message)

# --- COMMANDS ---
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

# --- MAIN STARTUP ---
if __name__ == '__main__':
    # Start web server in a separate thread
    threading.Thread(target=run_web, daemon=True).start()
    
    if TOKEN:
        print("Starting Bot...")
        bot.run(TOKEN)
    else:
        print("ERROR: BOT_TOKEN not found!")
