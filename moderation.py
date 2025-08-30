from discord.ext import commands
import json

warns_file = "warns.json"

def load_warns_data():
    with open(warns_file, "r") as f:
        return json.load(f)

def load_warns(user_id):
    with open(warns_file, "r") as f:
        data = json.load(f)
        return data.get(user_id, {})

def number_warns(user_id):
    return len(load_warns(user_id).keys())

def save_warns_data(user_id, warning):
    data = load_warns_data()
    if user_id not in data:
        data[str(user_id)] = {} 
    data[str(user_id)][str(number_warns(user_id))] = warning
    with open(warns_file, "w") as f:
        json.dump(data, f, indent=4)

class ModerationCog(commands.Cog):
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def warn(self, ctx, *args):
        user = ctx.message.mentions[0]
        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"
        save_warns_data(user.id, reason)
        await ctx.send(f"Warned user <@{user.id}> for reason: {reason}")
    
    
async def setup(bot):
    await bot.add_cog(ModerationCog(bot))