import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

OWNER_ID = 332262693626970112  # batzy ID

# Load the token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env")

# Intents: slash commands don't need message content
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Robust, instant guild sync + logging ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.event
async def setup_hook():
    try:
        gid = os.getenv("GUILD_ID")
        if gid:
            guild = discord.Object(id=int(gid))
            # Copy all global commands into this guild (instant)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"[SYNC] {len(synced)} commands synced to guild {gid}:")
        else:
            # Global sync (can take a few minutes the first time)
            synced = await bot.tree.sync()
            print(f"[SYNC] {len(synced)} global commands synced:")

        # List what Discord says is registered
        for c in bot.tree.get_commands():
            print("  -", c.name)
    except Exception as e:
        print("[SYNC ERROR]", repr(e))

@bot.tree.command(description="Force sync commands (owner only)")
async def sync(interaction: discord.Interaction):
    # ✅ Only you can run it
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You are not allowed to use this.", ephemeral=True)
        return # I dont think this works btw!! you are returning nothing you will get an error - Ayumi

    # ✅ Acknowledge immediately
    await interaction.response.defer(ephemeral=True)

    try:
        gid = os.getenv("GUILD_ID")
        if gid:
            guild = discord.Object(id=int(gid))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            msg = f"✅ Synced {len(synced)} commands to guild {gid}"
        else:
            synced = await bot.tree.sync()
            msg = f"✅ Synced {len(synced)} global commands"

        print("[SYNC] Commands now registered:", [c.name for c in bot.tree.get_commands()])

        # ✅ Use followup (safe after defer)
        await interaction.followup.send(msg, ephemeral=True)

    except Exception as e:
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Sync failed: `{e}`", ephemeral=True)

# /hello — greet someone by name

@app_commands.describe(name="Who should I greet?")
@bot.tree.command(description="Say hello to someone")
async def hello(interaction: discord.Interaction, name: str):
    await interaction.response.send_message(f"Hey {name}! 👋", ephemeral=False)

# /serverinfo — basic server stats (no privileged intents needed)
@bot.tree.command(description="Show basic info about this server")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    if not g:
        await interaction.response.send_message("This only works in servers.", ephemeral=False)
        return
    msg = (
        f"**Server:** {g.name}\n"
        f"**ID:** {g.id}\n"
        f"**Members:** {g.member_count}\n"
        f"**Created:** {g.created_at:%Y-%m-%d}"
    )
    await interaction.response.send_message(msg, ephemeral=True)

# /roll — simple dice roller: /roll sides:20
@app_commands.describe(sides="Number of sides on the die (2–100000)")
@bot.tree.command(description="Roll a die")
async def roll(interaction: discord.Interaction, sides: int = 6):
    if not 2 <= sides <= 100000:
        await interaction.response.send_message("Choose between 2 and 100000 sides.", ephemeral=False)
        return
    import random
    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 You rolled **{result}** (1–{sides})", ephemeral=False)

# /purge — delete last N messages (admin-only)
@app_commands.describe(count="How many recent messages to delete (1–100)")
@bot.tree.command(description="Delete recent messages (requires Manage Messages)")
async def purge(interaction: discord.Interaction, count: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You need **Manage Messages**.", ephemeral=True)
        return
    if not 1 <= count <= 100:
        await interaction.response.send_message("Pick 1–100.", ephemeral=True)
        return
    deleted = await interaction.channel.purge(limit=count)
    # Purge deletes the command prompt too; send a follow-up
    await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)

bot.run(TOKEN)

