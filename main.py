import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import requests
import datetime
from dotenv import load_dotenv
from tickets import TicketView, CloseTicket
from factions import FactionFloodCheckView
from requests import get as rget
    
# --------------------------------------------------------------------------
# Discord shenanigans
# --------------------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix=["!", "-"], intents=intents)

bot.client = client

load_dotenv("text.env")
TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    print("Error: TOKEN in text.env is missing")
    exit(1)

# --------------------------------------------------------------------------
# Baseline vars & funcs
# --------------------------------------------------------------------------

INFO = {
    "IP":"mc.truevanilla.net",
    "VERSIONS":"1.20.x - 1.21.x",
    "DIFFICULTY":"NORMAL",
    "WORLDBORDER":{
        "NUMBER": "80,000", 
        "HALF": "40,000"
    },
    "CHANNELS":{
        "BOT":1328017848143974524
    }
}

ADMIN = [
    1279362592300863530, # owner
    1360495023682093062, # admin
    1360495294856560741 # manager
]

STAFF = [
    1279362592300863530, # owner
    1360495023682093062, # admin
    1360495294856560741, # manager
    1325727434355773441, # moderator
    1362091819931926688, # developer
    1362668964177772565 # staff
]

bot.STAFF = STAFF

def admin(member):
    return any(role.id in ADMIN for role in member.roles)

def staff(member):
    return any(role.id in STAFF for role in member.roles)

bot.admin = admin
bot.staff = staff

join_data_file = "join_roles.json"
news_file = "news_data.json"
trivia_questions_file = "trivia_questions.json"
trivia_questions = {}

# --------------------------------------------------------------------------
# News
# --------------------------------------------------------------------------

def load_news_data():
    try:
        with open(news_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"announcement": "", "messages": [], "last_reset": str(datetime.date.today())}

def save_news_data(data):
    with open(news_file, "w") as f:
        json.dump(data, f, indent=4)
        
# News Message        

async def get_news():
    data = load_news_data()
        
    if not data['announcement']:
        news_announcement = "No new announcements"
    else:
        news_announcement = data['announcement']
            
    embed = discord.Embed(
        title="📢  Weekly News\n",
        description="‎",
        color=discord.Color.blue()
    )

    embed.add_field(name="📰  Announcements", value="‎\n"+news_announcement, inline=False)
        
    if not data["messages"]:
        embed.add_field(name="🔥  Posts", value="‎\nNo posts were added! Remember to use `!news_add`!\n‎", inline=False)
    else:
        news_billboard = ""
        for i, entry in enumerate(data["messages"], 1):
            user = await bot.fetch_user(entry["user_id"])
            news_billboard += f"{i}. {user.name}: {entry['message']}\n"
        embed.add_field(name="🔥  Posts", value="‎\n"+news_billboard+"‎\n", inline=False)
        
    embed.set_footer(text="Stay tuned for more updates!")
    return embed
        
# --------------------------------------------------------------------------
# News loops
# --------------------------------------------------------------------------

# Weekly news

@tasks.loop(hours=24)
async def send_news():
    if datetime.datetime.now().weekday() == 5:
        general_channel = bot.get_channel(1279143050496442471)
        
        await general_channel.send(embed=await get_news())

# Weekly news reset

@tasks.loop(hours=24)
async def weekly_news_reset():
    data = load_news_data()
    today = str(datetime.date.today())
    
    if today != data["last_reset"] and datetime.datetime.now().weekday() == 5:
        data["messages"] = []
        data["announcement"] = ""
        data["last_reset"] = today
        save_news_data(data)
        print("News round has been reset.")
        
# --------------------------------------------------------------------------
# News
# --------------------------------------------------------------------------

# Set news announcement (admin)

@bot.command()
@commands.has_permissions(administrator=True)
async def news_set(ctx, *, announcement):
    data = load_news_data()
    data["announcement"] = announcement
    save_news_data(data)
    await ctx.send(f"News announcement set to: {announcement}")
    
# No permission to set news announcement

@news_set.error
async def news_set_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to set the news announcement :|")

# Add news post (members)

@bot.command()
async def news_add(ctx, *, message):
    data = load_news_data()

    if any(m.get("user_id") == ctx.author.id for m in data["messages"]):
        await ctx.send("You've already added a post this week!")
        return

    if len(data["messages"]) < 10:
        data["messages"].append({"user_id": ctx.author.id, "message": message})
        save_news_data(data)
        await ctx.send(f"Your post has been added to this week's news: {message}")
    else:
        await ctx.send("The billboard is full for this week. Come back next Saturday!")

# Get latest news

@bot.command()
async def news(ctx):
    await ctx.send(embed=await get_news())

async def schedule_news_loop():
    now = datetime.datetime.now()
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    
    if now >= target:
        target += datetime.timedelta(days=1)

    wait_seconds = (target - now).total_seconds()
    print(f"Waiting {wait_seconds} seconds until 09:00")

    await asyncio.sleep(wait_seconds)
    
    send_news.start()
    weekly_news_reset.start()

# --------------------------------------------------------------------------
# Get data from URL
# --------------------------------------------------------------------------

def get_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"ERROR: Received status code {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"ERROR: Failed to retrieve data\n{e}")
        return None

# --------------------------------------------------------------------------
# Server rules
# --------------------------------------------------------------------------

def process_rules_file(filename):
    articles = []
    current_article = None
    current_paragraph = []

    with open(filename, 'r') as file:
        lines = file.readlines()

    for line in lines:

        if line.startswith("# "):  # check for title
            if current_article:
                if current_paragraph:
                    current_article["paragraphs"].append("".join(current_paragraph).strip())
                    current_paragraph = []
                articles.append(current_article)

            current_article = {
                "title": line[2:].strip() if line[2:].strip() else None,
                "subtitle": None,
                "subheadings": [],
                "paragraphs": []
            }

        elif line.startswith("## "):  # check for subtitle
            if current_article:
                if current_paragraph:
                    current_article["paragraphs"].append("".join(current_paragraph).strip())
                    current_paragraph = []

                current_article["subtitle"] = line[3:].strip() if line[3:].strip() else None

        elif line.startswith("### "):
            if current_article:
                if current_paragraph:
                    current_article["paragraphs"].append("".join(current_paragraph).strip())
                    current_paragraph = []

                current_article["subheadings"].append(line[4:].strip())

        elif line.startswith("// "):
            continue
        
        else:
            current_paragraph.append(line)

    if current_paragraph and current_article:
        current_article["paragraphs"].append("".join(current_paragraph).strip())

    if current_article:
        articles.append(current_article)

    return articles

def create_embed_from_article(article):
    embed = discord.Embed(
        title=article['title'] or "",
        description=article['subtitle'] or "",
        color=discord.Color.blue()
    )

    subheadings = article['subheadings']
    paragraphs = article['paragraphs']

    for i, subheading in enumerate(subheadings):
        paragraph = paragraphs[i] if i < len(paragraphs) else ""
        embed.add_field(name=f"{subheading}", value=paragraph or "", inline=False)

    return embed

@bot.command()
async def rules(ctx):
    await ctx.message.delete()

    filename = 'rules.txt'
    articles = process_rules_file(filename)
    embeds = []

    for article in articles:
        embed = create_embed_from_article(article)
        embeds.append(embed)
    channel = bot.get_channel(1279147286286307419)
    if admin(ctx.author):
        await channel.purge(limit=10)
        for embed in embeds:
            await channel.send(embed=embed)
        
@bot.tree.command(name="xkcd", description="Get a random comic from xkcd.com")
async def xkcd(interaction: discord.Interaction):
    r = rget("https://c.xkcd.com/random/comic/")
    for i in r.text.split("\n"):
        if i.startswith("<meta property=\"og:image\" content=\""):
            r = i.strip("<meta property=\"og:image\" content=\"").strip("\">")
            break
            
    await interaction.response.send_message(r)
    
@bot.tree.command(name="verify", description="Verify your discord account")
@app_commands.describe(ign="Your Minecraft IGN/In Game Name/Username")
async def minecraft_user(interaction: discord.Interaction, ign: str):
    channel_id = 1312528601253412945
    channel = bot.get_channel(channel_id)

    if channel is None:
        await interaction.response.send_message("Error: Channel not found.", ephemeral=True)
        return
    
    content = f"User {interaction.user.mention} wants to link their Minecraft account: **{ign}**"

    class AcceptButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Accept", style=discord.ButtonStyle.green)

        async def callback(self, button_interaction: discord.Interaction):
            # certain roles or permissions here

            user_id = int(self.custom_id.split(":")[1])
            mc_account = self.custom_id.split(":")[2]

            guild = button_interaction.guild
            member = guild.get_member(user_id)
            if member is None:
                await button_interaction.response.send_message("User not found in this guild.", ephemeral=True)
                return
            
            prev_nick = member.display_name
            new_nick = f"{prev_nick} ({mc_account})"

            eek = False
                
            if len(new_nick) > 32:
                new_nick = prev_nick
                eek = True

            role_id = 1382988826200248330
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role)
            else:
                print("Error: \'Linked\' role not found")
            
            await member.edit(nick=new_nick)
            await button_interaction.response.send_message(f"Nickname changed to: {new_nick}")
            
            bot_channel_id = 1328017848143974524
            bot_channel = bot.get_channel(bot_channel_id)
            
            if not eek:
                await bot_channel.send(f"{member.mention}, your request to link Minecraft account \'{mc_account}\' has been accepted!")
            else:
                await bot_channel.send(f"{member.mention}, your request to link Minecraft account \'{mc_account}\' has been accepted!\nUnfortunately, your nickname was too long, and we cant change it.")
            self.disabled = True
            await button_interaction.message.edit(view=self.view)

    class MinecraftAcceptView(discord.ui.View):
        def __init__(self, user_id, mc_account):
            super().__init__(timeout=None)
            accept_button = AcceptButton()
            accept_button.custom_id = f"accept_button:{user_id}:{mc_account}"
            self.add_item(accept_button)

    view = MinecraftAcceptView(interaction.user.id, ign)

    await channel.send(content=content, view=view)
    await interaction.response.send_message(f"Your request to link Minecraft account '{ign}' has been sent.")
    
# --------------------------------------------------------------------------
# Start the bot
# --------------------------------------------------------------------------

@bot.command()
async def echo(ctx, *, message):
    if staff(ctx.author):
        await ctx.send(message.replace("\\n", "\n").replace("@", "[@]").replace("<", "[<]").replace(">", "[>]"))

async def load_cogs():
    cogs = ["tickets", "factions", "moderation", "questions", "roles", "system", "commands"]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"Loaded {cog} extension")
        except Exception as e:
            print(f"Couldn't load {cog} extension: {e}")
            
async def load_views():
    views = [TicketView, CloseTicket, FactionFloodCheckView]
    
    for view in views:
        try:
            bot.add_view(view(bot=bot))
            print(f"Loaded {view.__name__} view")
        except Exception as e:
            print(f"Couldn't load {view.__name__} view: {e}")
    
async def load_tree():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")
    
@bot.event
async def on_ready():
    global guild
    print(f'Logged in as {bot.user}')
    
    try:
        bot.tree.add_command(minecraft_user)
    except Exception as e:
        print(f"Failed to load /verify: {e}")
    
    try:
        bot.tree.add_command(xkcd)
    except Exception as e:
        print(f"Failed to load /xkcd: {e}")
    
    guild = bot.get_guild(1279143050496442469)
    
    await load_cogs()
    await load_views()
    await load_tree()
    
    await schedule_news_loop()

# Run the bot
bot.run(TOKEN)
