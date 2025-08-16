import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import requests
import datetime
from dotenv import load_dotenv
from tickets.tickets import TicketView, CloseTicket, load_tickets_data
from itertools import cycle
    
# --------------------------------------------------------------------------
# Discord shenanigans
# --------------------------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

bot = commands.Bot(command_prefix="!", intents=intents)
modbot = commands.Bot(command_prefix="-", intents=intents)


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

guild = bot.get_guild(1279143050496442469)

join_data_file = "join_roles.json"
news_file = "news_data.json"

# --------------------------------------------------------------------------
# @new role
# --------------------------------------------------------------------------

def load_join_data():
    with open(join_data_file, "r") as f:
        return json.load(f)

def save_join_data(data):
    with open(join_data_file, "w") as f:
        json.dump(data, f, indent=4)

join_data = load_join_data()

@tasks.loop(minutes=30)
async def check_new_role():
    now = datetime.datetime.now()
    role = guild.get_role(1376242160042512575)
    to_remove = []

    for user_id, expiry_str in join_data.items():
        expiry = datetime.datetime.fromisoformat(expiry_str)
        if now >= expiry:
            member = guild.get_member(int(user_id))
            if member:
                if role in member.roles:
                    await member.remove_roles(role)
                    print(f"Removed expired role from {member.display_name}")
            to_remove.append(user_id)

    for user_id in to_remove:
        del join_data[user_id]
    if to_remove:
        save_join_data(join_data)

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
# Welcome channel
# --------------------------------------------------------------------------

# Boosts

@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        print(f"HYPE HYPE HYPE HYPE\n{after} just boosted the server!")
        msg = f"# 🎉 DISCORD BOOST! 🎉\n### {after.mention} JUST BOOSTED THE SERVER!!!"
        channel = bot.get_channel(1279143050496442471)
        if channel:
            await channel.send(msg)
        else:
            print("boost command channel not found")

# Member join message

@bot.event
async def on_member_join(member):
    role_id = 1376242160042512575
    role = member.guild.get_role(role_id)
    if role:
        await member.add_roles(role)
        print(f"Assigned \'new\' role to {member.display_name}")
        
        join_data[str(member.id)] = (datetime.datetime.utcnow() + datetime.timedelta(days=14)).isoformat()
        save_join_data(join_data)

    welcome = discord.Embed(
        title="Welcome to **True Vanilla Network**!",
        description=(
            "**Java:**\n"
            "**IP:** `mc.truevanilla.net`\n"
            "**Versions:** `1.19.x-1.21.x` (the latest version)\n"
            "**Bedrock:**\n"
            "**IP:** `bedrock.truevanilla.net`\n"
            "**PORT:** `25588`\n"
            "**Versions:** `1.21.70 - 1.21.93` (the latest version)\n"
            "For reference, most bedrock launchers automatically update to the latest version\n"
            "Go to https://discord.com/channels/1279143050496442469/1279147286286307419 for info & rules\n**Hacking is not allowed**\n\n"
        ),
        color=discord.Color.dark_blue()
    )
    welcome.set_footer(text="THIS IS NOT A CRACKED SERVER")
    message = f"Welcome {member.mention} (*{member.display_name}*) to **True Vanilla**!"
    
    try:
        await member.send(embed=welcome)
    except Exception as err:
        print(err)
        message += "\nPlease check https://discord.com/channels/1279143050496442469/1375185161980739797 on how to join and what versions we support."
    
    channel = bot.get_channel(1279361679192231996)
    if channel:
        msg_module = await channel.send(message)
        
        overfill = msg_module.guild.member_count%50
        if overfill == 0:
            await msg_module.pin()
            await channel.send(f"# We have reached {msg_module.guild.member_count} members!")
        
# Member leave message

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(1279361679192231996)
    if channel:
        await channel.send(f"User {member.mention} (*{member.display_name}*) left.")
        
@bot.event
async def on_message(message):
    if (
        message.channel.id == 1279363971639545896
        and not message.reference
        and message.author.id != 1225709819890110604
    ):
        url = "http://localhost:11434/api/generate"
        prompt = (
            "You are a message classifier for a Discord moderation bot.\n"
            "Determine if the following message is a HELP REQUEST.\n"
            "A help request includes: asking to get unbanned, reporting a bug, or asking a question about the server.\n"
            "If the message is a help request, reply with ONLY: YES\n"
            "If the message is not a help request (e.g. just chatting or replying), reply with ONLY: NO\n"
            "Here is the message:\n"
            f"\"{message.content}\""
        )

        data = {
            "model": "llama3.2:latest",
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(url, json=data)

        if response.status_code == 200:
            print("MESSAGE!!!")
            print(response.json()["response"].strip())
            if response.json()["response"].strip() == "YES":
                await message.reply(
                    "Please open a ticket in https://discord.com/channels/1279143050496442469/1338143330286043259 to:\n"
                    "- Appeal a ban\n"
                    "- Report bugs\n"
                    "- Ask for rollback/items due to lag or glitches"
                )
        else:
            print(f"ERROR: {response.status_code}\nMore info:\n{response.text}")
    elif "tenor.com" in message.content:
        await message.reply(
            "Please make sure to send all memes or gifs in <#1405892733129855032>"
        )
    

# --------------------------------------------------------------------------
# MODERATION COMMANDS
# --------------------------------------------------------------------------
    
# Purge an amount of messages

@modbot.command()
async def purge(ctx, number: int):
    if staff(ctx.author):
        number = int(number)
        await ctx.channel.purge(limit=number+1)
    
@modbot.command()
async def nuke(ctx):
    if staff(ctx.author):
        for i in range(1, 5):
            await ctx.channel.purge(limit=100)

# --------------------------------------------------------------------------
# COMMANDS
# --------------------------------------------------------------------------

# Test command

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Server IP

@bot.command()
async def ip(ctx):
    if ctx.channel.id != INFO["CHANNELS"]["BOT"]:
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await ctx.send(f"Please use all commands in <#{INFO['CHANNELS']['BOT']}>.", delete_after=5)
        return
    main = discord.Embed(
        title="Server IP",
        description=f"**IP:** `{INFO['IP']}`",
        color=discord.Color.blue()
    )
    await ctx.send(embed=main)
    
# Server join info

@bot.command()
async def join(ctx):
    if ctx.channel.id != INFO["CHANNELS"]["BOT"]:
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await ctx.send(f"Please use all commands in <#{INFO['CHANNELS']['BOT']}>.", delete_after=5)
        return
    main = discord.Embed(
        title="Server IP",
        description=f"**IP:** `{INFO['IP']}`\n**Version:** `{INFO['VERSIONS']}`",
        color=discord.Color.blue()
    )
    await ctx.send(embed=main)
    
# Server info

@bot.command()
async def info(ctx):
    if ctx.channel.id != INFO["CHANNELS"]["BOT"]:
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await ctx.send(f"Please use all commands in <#{INFO['CHANNELS']['BOT']}>.", delete_after=5)
        return
    url = f"https://api.mcstatus.io/v2/status/java/{INFO['IP']}"
    data = get_data(url)
    
    server_status = "**Status:** `Offline`" if not data or not data["online"] else "**Status:** `Online`"
    
    embed = discord.Embed(
        title="Server Info",
        description=f"**IP:** `{INFO['IP']}`\n**Version:** `{INFO['VERSIONS']}`\n{server_status}",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed)
    
# Vote links

@bot.command()
async def vote(ctx):
    main = discord.Embed(
        title="Vote",
        description="**Thank you for voting!**\n[1 - VOTE](https://example.com)",
        color=discord.Color.blue()
    )
    await ctx.send(embed=main)

# Server status

@bot.command()
async def status(ctx):
    if ctx.channel.id != INFO["CHANNELS"]["BOT"]:
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await ctx.send(f"Please use all commands in <#{INFO['CHANNELS']['BOT']}>.", delete_after=5)
        return
    url = f"https://api.mcstatus.io/v2/status/java/{INFO['IP']}"
    data = get_data(url)
    
    if data and data["online"]:
        embed = discord.Embed(
            title="Server is online",
            description="",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="Server is offline",
            description="",
            color=discord.Color.red()
        )

    await ctx.send(embed=embed)

# Discord member count

@bot.command()
async def members(ctx):
    if ctx.channel.id != INFO["CHANNELS"]["BOT"]:
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await ctx.send(f"Please use all commands in <#{INFO['CHANNELS']['BOT']}>.", delete_after=5)
        return
    member_count = ctx.guild.member_count
    embed = discord.Embed(
        title="Discord Member Count",
        description=f"Total Members: `{member_count}`",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send("Not a command >:|")
        print(f"Wrong command ran by {ctx.author.display_name}, {ctx.author.name}")
    else:
        raise error

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
        await channel.purge(limit=100)
        for embed in embeds:
            await channel.send(embed=embed)

@tree.command(name="verify", description="Verify your discord account")
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
# Statuses
# --------------------------------------------------------------------------

@tasks.loop(seconds=5)
async def status_loop():
    ticket_numbers = 0 

    for ticket_id, ticket_value in load_tickets_data().items():
        if ticket_value:
            ticket_numbers += 1
            
    bot_statuses = cycle([f"Watching {ticket_numbers} tickets", "Playing on True Vanilla Network", "Watching over {guild.member_count} members"])
    await bot.change_presence(activity=discord.Game(next(bot_statuses)))

# --------------------------------------------------------------------------
# Start the bot
# --------------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    
    bot.tree.add_command(minecraft_user)
    
    try: 
        await bot.load_extension("tickets.tickets")
        bot.add_view(TicketView(bot=bot))
        bot.add_view(CloseTicket(bot=bot))
    except Exception as e:
        print(f"Couldn't load Ticket extension: {e}")
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")
    
    await schedule_news_loop()
    check_new_role.start()
    status_loop.start()

# Run the bot
bot.run(TOKEN)