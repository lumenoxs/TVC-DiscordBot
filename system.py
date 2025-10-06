from discord.ext import commands, tasks
import json
import datetime
import discord
import requests

users_file = "users.json"
join_data_file = "join_roles.json"
hi_file = "hi_data.json"

def load_users_data():
    with open(users_file, "r") as f:
        return json.load(f)

def save_users_data(data):
    with open(users_file, "w") as f:
        json.dump(data, f, indent=4)
        
def load_hi_data():
    with open(hi_file, "r") as f:
        return json.load(f)

def save_hi_data(data):
    with open(hi_file, "w") as f:
        json.dump(data, f, indent=4)

def add_hi(hi):
    data = load_hi_data()
    data["0"].append(hi)
    save_hi_data(data)
    
def load_join_data():
    with open(join_data_file, "r") as f:
        return json.load(f)

def save_join_data(data):
    with open(join_data_file, "w") as f:
        json.dump(data, f, indent=4)

class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_new_role.start()
        self.bump_reminder.start()

    @commands.command()
    async def welcome_users(self, ctx):
        if ctx.author.guild_permissions.administrator == False: return
        users_data = load_users_data()
        members = []
        for user_id in self.bot.get_guild(1279143050496442469).members:
            user_id = user_id.id
            members.append(user_id)
            
        for user_id in users_data["0"]:
            if user_id not in members:
                # someone left
                channel = self.bot.get_channel(1279361679192231996)
                name = await self.bot.fetch_user(user_id)
                print(f"User {name} (*{user_id}*) left.")
                await channel.send(f"User <@{user_id}> (*{name}*) left.")
                users_data["0"].remove(user_id)
        
        for user_id in members:
            if user_id not in users_data["0"]:
                # someone joined
                member = self.bot.get_guild(1279143050496442469).get_member(user_id)
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
                users_data["0"].append(user_id)
        
        save_users_data(users_data)
        await ctx.send("Welcomed users.")

    @commands.command()
    async def resync_users(self, ctx):
        if ctx.author.guild_permissions.administrator == False: return
        save_users_data({"0": []})
        stuff = load_users_data()
        for member in self.bot.get_guild(1279143050496442469).members:
            stuff["0"].append(member.id)
        save_users_data(stuff)
        await ctx.send("Resynced users.")

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
        stuff["0"].append(member.id)
        save_users_data(stuff)
    
    @tasks.loop(minutes=1)
    async def bump_reminder(self):
        channel = self.bot.get_channel(1328017848143974524)
        with open("bump_data.txt", "r") as f:
            data = f.read().split(":::")
            last_bump = datetime.datetime.fromisoformat(data[1].strip())
            user = await self.bot.fetch_user(int(data[0].strip()))
            now = datetime.datetime.utcnow()
            if (now - last_bump).total_seconds() > 2:
                await channel.send(f"Hey {user.mention}! It's been two hours since you last bumped, so you can bump the server again! Please consider bumping the server using `/bump`!")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(member.id)
        channel = self.bot.get_channel(1279361679192231996)
        if channel:
            await channel.send(f"User {member.mention} (*{member.display_name}*) left.")
        
        stuff = load_users_data()
        stuff["0"].remove(member.id)
        save_users_data(stuff)

    @commands.Cog.listener()
    async def on_message(self, message):
        new_role = self.bot.get_guild(1279143050496442469).get_role(1376242160042512575)
        ip_kyws = ["whats the ip", "wats the ip", "wat the ip", "how do i join", "how to join", "wheres the ip"]
        hi_kwys = ["hi", "hello", "hey", "sup", "yo", "good morning", "good afternoon", "good evening", "greetings", "howdy"]
        if message.channel.id == 1328017848143974524 and message.interaction_metadata and message.author.id == 302050872383242240:
            await message.reply("Thanks for bumping our server! You rock! :D")
            await message.add_reaction("🎉")
            with open("bump_data.txt", "w") as f:
                f.write(f"{message.interaction_metadata.user.id}:::{datetime.datetime.utcnow().isoformat()}\n")
        elif message.author.bot:
            return
        elif "tenor.com" in message.content and message.channel.id != 1405892733129855032:
            await message.reply("Please make sure to send all memes or gifs in <#1405892733129855032>")
        elif any(kyw in message.content.lower() for kyw in hi_kwys):
            if new_role in message.author.roles and message.author.id not in load_hi_data()["0"]:
                await message.reply("Hi there, and welcome to True Vanilla Community!\nCheck <#1375185161980739797> on how to join, and get your roles in <#1412708336536653886>.")
                add_hi(message.author.id)
            elif message.author.id == 1047608245172326530:
                await message.reply("Hi there, and welcome to True Vanilla Community!\nCheck <#1375185161980739797> on how to join, and get your roles in <#1412708336536653886>.\n-# this was purposefully asked by stunslams, this is not a bug\n-# if you wanted this removed stunslams, just dm me ok")
        elif any(kyw in message.content.lower() for kyw in ip_kyws) and new_role in message.author.roles:
            await message.reply("Hi there! Check <#1375185161980739797> for info on how to join.")
        
async def setup(bot):
    await bot.add_cog(SystemCog(bot))