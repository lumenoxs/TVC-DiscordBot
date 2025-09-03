from discord.ext import commands
import json
from datetime import timedelta

warns_file = "warns.json"

punishments = {
    1: "none:0",
    2: "mute:1h",
    3: "mute:1d",
    4: "mute:1w",
    5: "kick:0",
    6: "mute:1m"
}

def load_warns_data():
    with open(warns_file, "r") as f:
        return json.load(f)

def load_warns(user_id):
    with open(warns_file, "r") as f:
        data = json.load(f)
        return data.get(str(user_id), {})

def number_warns(user_id):
    return len(load_warns(user_id).keys())+1

def save_warns_data(user_id, warning):
    data = load_warns_data()
    user_id_str = str(user_id)

    if user_id_str not in data:
        data[user_id_str] = {}

    data[user_id_str][str(number_warns(user_id))] = warning

    with open(warns_file, "w") as f:
        json.dump(data, f, indent=4)
        
def ordinal(n):
    return "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4]) # credit to copilot for this function :)

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def warn(self, ctx, *args):
        user = ctx.message.mentions[0]
        user = ctx.guild.get_member(user.id)
        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"
        numStrikes = number_warns(user.id)
        msg = f"Warned <@{user.id}> for reason: {reason}"
        save_warns_data(user.id, reason)
        
        if numStrikes in punishments.keys():
            action = punishments[numStrikes].split(":")[0]
            duration = punishments[numStrikes].split(":")[1]
            if action == "none":
                msg += f"\nThis is their {ordinal(numStrikes)} strike. No action was taken."
            elif action == "mute":
                if duration.endswith("h"):
                    hours = int(duration[:-1])
                    timeoutT = timedelta(hours=hours)
                    msg += f"\nMuted for {hours} hour(s) as this was their {ordinal(numStrikes)} strike."
                elif duration.endswith("d"):
                    days = int(duration[:-1])
                    timeoutT = timedelta(days=days)
                    msg += f"\nMuted for {days} day(s) as this was their {ordinal(numStrikes)} strike."
                elif duration.endswith("w"):
                    weeks = int(duration[:-1])
                    timeoutT = timedelta(weeks=weeks)
                    msg += f"\nMuted for {weeks} week(s) as this was their {ordinal(numStrikes)} strike."
                elif duration.endswith("min"):
                    minutes = int(duration[:-3])
                    timeoutT = timedelta(minutes=minutes)
                    msg += f"\nMuted for {minutes} minute(s) as this was their {ordinal(numStrikes)} strike."
                elif duration.endswith("m"):
                    months = int(duration[:-1])
                    timeoutT = timedelta(days=31*months)
                    msg += "\nMuted for {months} month(s)."
                await user.timeout(timeoutT, reason=f"{ordinal(numStrikes)} strike. Reason: {reason}")
            elif action == "kick":
                await user.kick(reason=f"{ordinal(numStrikes)} strikes. Reason: {reason}")
                msg += "\nKicked."
            else:
                msg += f"\nThis is their {ordinal(numStrikes)} strike. No action was taken."
        else:
            msg += f"\nThis is their {ordinal(numStrikes)} strike. No action was taken."
        
        await ctx.send(msg)
    
    @commands.Cog.listener()
    async def on_raw_message_delete(self, plyd):
        if plyd.cached_message:
            return
        channel = self.bot.get_channel(1312528601253412945)
        dchannel = self.bot.get_channel(plyd.channel_id)
        await channel.send(f"Message deleted in {dchannel.mention}")
        
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        channel = self.bot.get_channel(1312528601253412945)
        await channel.send(f"Message by {message.author.name} deleted in {message.channel.mention}:\n```{message.content}```")
    
    @commands.Cog.listener()
    async def on_raw_message_edit(self, plyd):
        if plyd.cached_message:
            return
        channel = self.bot.get_channel(1312528601253412945)
        await channel.send(f"Message by {plyd.message.author.name} edited in {plyd.message.channel.mention}\nMessage:\n```{plyd.message.content}```")
    
    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        if message_before.author.bot:
            return
        channel = self.bot.get_channel(1312528601253412945)
        if message_after.content == message_before.content:
            return
        elif message_after.content.startswith("http"):
            return
        await channel.send(f"Message by {message_after.author.name} edited in {message_after.channel.mention}\nOld message:\n```{message_before.content}```\nNew message:\n```{message_after.content}```")
    
    
    @commands.command()
    async def purge(self, ctx, number: int):
        if self.bot.admin(ctx.author):
            number = int(number)
            await ctx.channel.purge(limit=number+1)
        
    @commands.command()
    async def nuke(self, ctx):
        if self.bot.admin(ctx.author):
            for i in range(1, 5):
                await ctx.channel.purge(limit=100)
    
    
async def setup(bot):
    await bot.add_cog(ModerationCog(bot))