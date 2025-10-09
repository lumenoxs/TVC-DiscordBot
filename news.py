import discord
from discord.ext import commands, tasks
import json
import datetime
import asyncio

news_file = "news_data.json"

def load_news_data():
    try:
        with open(news_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"announcement": "", "messages": [], "last_reset": str(datetime.date.today())}

def save_news_data(data):
    with open(news_file, "w") as f:
        json.dump(data, f, indent=4)     

async def get_news(bot):
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

class NewsCog(commands.Cog):
    async def __init__(self, bot):
        self.bot = bot
        await self.schedule_news_loop()

    @tasks.loop(hours=24)
    async def send_news(self):
        if datetime.datetime.now().weekday() == 5:
            general_channel = self.bot.get_channel(1279143050496442471)
            
            await general_channel.send(embed=await get_news(self.bot))

    @tasks.loop(hours=24)
    async def weekly_news_reset(self):
        data = load_news_data()
        today = str(datetime.date.today())
        
        if today != data["last_reset"] and datetime.datetime.now().weekday() == 5:
            data["messages"] = []
            data["announcement"] = ""
            data["last_reset"] = today
            save_news_data(data)
            print("News round has been reset.")

    @commands.Cog.command()
    @commands.has_permissions(administrator=True)
    async def news_set(self, ctx, *, announcement):
        data = load_news_data()
        data["announcement"] = announcement
        save_news_data(data)
        await ctx.send(f"News announcement set to: {announcement}")

    @commands.Cog.command()
    async def news_add(self, ctx, *, message):
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

    @commands.Cog.command()
    async def news(self, ctx):
        await ctx.send(embed=await get_news(self.bot))

    async def schedule_news_loop(self):
        now = datetime.datetime.now()
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        
        if now >= target:
            target += datetime.timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        print(f"Waiting {wait_seconds} seconds until 09:00")

        await asyncio.sleep(wait_seconds)
        
        await self.send_news.start()
        await self.weekly_news_reset.start()

async def setup(bot):
    await bot.add_cog(NewsCog(bot))