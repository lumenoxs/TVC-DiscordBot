from discord.ext import commands, tasks
import json
import datetime
import discord
import requests

users_file = "users.json"

# @commands.command()
# async def echo(ctx, *args):
#     if admin(ctx.author):
#         await ctx.send(args)
#         print(args)
join_data_file = "join_roles.json"

def load_users_data():
    with open(users_file, "r") as f:
        return json.load(f)

def save_users_data(data):
    with open(users_file, "w") as f:
        json.dump(data, f, indent=4)

def load_join_data():
    with open(join_data_file, "r") as f:
        return json.load(f)

def save_join_data(data):
    with open(join_data_file, "w") as f:
        json.dump(data, f, indent=4)

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

async def welcome_users(bot):
    stuff = load_users_data()
    members = []
    for id in bot.get_guild(1279143050496442469).members:
        id = id.id
        members.append(id)
        
    for id in stuff["0"]:
        if id not in members:
            # someone left
            channel = bot.get_channel(1279361679192231996)
            name = get_data("https://discordlookup.mesalytic.moe/v1/user/"+str(id))["global_name"]
            await channel.send(f"User <@{id}> (*{name}*) left.")
        
        stuff["0"].remove(id)
    
    for id in members:
        if id not in stuff["0"]:
            # someone joined
            member = bot.get_guild(1279143050496442469).get_member(id)
            join_data = load_join_data()
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
                    "Go to https://discord.com/channels/1279143050496442469/1279147286286307419 for rules\n\n"
                ),
                color=discord.Color.dark_blue()
            )
            welcome.set_footer(text="THIS IS NOT A CRACKED SERVER\nHACKING IS NOT ALLOWED\nWE DO NOT SUPPORT BEDROCK")
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
        stuff["0"].append(id)
    
    save_users_data(stuff)

class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_new_role.start()

    @tasks.loop(minutes=30)
    async def check_new_role(self):
        join_data = load_join_data()
        now = datetime.datetime.now()
        guild = self.bot.get_guild(1279143050496442469)
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
            
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.premium_since is None and after.premium_since is not None:
            print(f"HYPE HYPE HYPE HYPE\n{after} just boosted the server!")
            msg = f"# 🎉 DISCORD BOOST! 🎉\n### {after.mention} JUST BOOSTED THE SERVER!!!"
            channel = self.bot.get_channel(1279143050496442471)
            if channel:
                await channel.send(msg)
            else:
                print("boost command channel not found")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(member.id)
        join_data = load_join_data()
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
                "Go to https://discord.com/channels/1279143050496442469/1279147286286307419 for rules\n\n"
            ),
            color=discord.Color.dark_blue()
        )
        welcome.set_footer(text="THIS IS NOT A CRACKED SERVER\nHACKING IS NOT ALLOWED\nWE DO NOT SUPPORT BEDROCK")
        message = f"Welcome {member.mention} (*{member.display_name}*) to **True Vanilla**!"
        
        try:
            await member.send(embed=welcome)
        except Exception as err:
            print(err)
            message += "\nPlease check https://discord.com/channels/1279143050496442469/1375185161980739797 on how to join and what versions we support."
        
        channel = self.bot.get_channel(1279361679192231996)
        if channel:
            msg_module = await channel.send(message)
            
            overfill = msg_module.guild.member_count%50
            if overfill == 0:
                await msg_module.pin()
                await channel.send(f"# We have reached {msg_module.guild.member_count} members!")
        
        stuff = load_users_data()
        stuff["0"].append(str(id))
        save_users_data(stuff)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(member.id)
        channel = self.bot.get_channel(1279361679192231996)
        if channel:
            await channel.send(f"User {member.mention} (*{member.display_name}*) left.")
        
        stuff = load_users_data()
        stuff["0"].remove(str(id))
        save_users_data(stuff)

    @commands.Cog.listener()
    async def on_message(self, message):
        if (message.author.id == 1337890473188003893):
            return
        elif "tenor.com" in message.content:
            await message.reply(
                "Please make sure to send all memes or gifs in <#1405892733129855032>"
            )
        await self.bot.process_commands(message)

    # @commands.command()
    # async def setup_users(self, ctx):
    #     stuff = load_users_data()
    #     stuff["0"] = []
    #     for id in self.bot.get_guild(1279143050496442469).members:
    #         id = id.id
    #         stuff["0"].append(id)
    #         print(id)
    #     save_users_data(stuff)
        
async def setup(bot):
    await bot.add_cog(SystemCog(bot))
    await welcome_users(bot)