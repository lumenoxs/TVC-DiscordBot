from discord.ext import commands
import json
from main import staff, admin

warns_file = "warns.json"

def load_warns_data():
    with open(warns_file, "r") as f:
        return json.load(f)

def load_warns(user_id):
    with open(warns_file, "r") as f:
        data = json.load(f)
        return data.get(str(user_id), {})

def number_warns(user_id):
    return len(load_warns(user_id).keys())

def save_warns_data(user_id, warning):
    data = load_warns_data()
    user_id_str = str(user_id)

    if user_id_str not in data:
        data[user_id_str] = {}

    data[user_id_str][str(number_warns(user_id))] = warning

    with open(warns_file, "w") as f:
        json.dump(data, f, indent=4)
        
def ordinal(n):
    return "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

class ModerationCog(commands.Cog):
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def warn(self, ctx, *args):
        user = ctx.message.mentions[0]
        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"
        save_warns_data(user.id, reason)
        await ctx.send(f"Warned <@{user.id}> for reason: {reason}\nThis is their {ordinal(number_warns(user.id))} strike.")
        
    @commands.command()
    async def purge(self, ctx, number: int):
        if admin(ctx.author):
            number = int(number)
            await ctx.channel.purge(limit=number+1)
        
    @commands.command()
    async def nuke(self, ctx):
        if admin(ctx.author):
            for i in range(1, 5):
                await ctx.channel.purge(limit=100)
    
    
async def setup(bot):
    await bot.add_cog(ModerationCog(bot))