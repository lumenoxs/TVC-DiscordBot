import discord
from discord.ext import commands, tasks
import json
import datetime
import asyncio
from random import choice

news_file = "news_data.json"

def load_news_data():
    with open(news_file, "r") as f:
        return json.load(f)

def save_news_data(data):
    with open(news_file, "w") as f:
        json.dump(data, f, indent=4)     

async def get_latest_news(bot):
    data = load_news_data()

    if not data['announcement']:
        news_announcement = "No new announcements"
    else:
        news_announcement = data['announcement']
    
    if not data["messages"]:
        news_billboard = "No posts were added! Remember to use `!news_add`!"
    else:
        news_billboard = ""
        for i, entry in enumerate(data["messages"], 1):
            user = await bot.fetch_user(entry["user_id"])
            news_billboard += f"{i}. {user.name}: {entry['message']}\n"

    return news_announcement, news_billboard

async def get_latest_news_embed(bot):
    news_announcement, news_billboard = await get_latest_news(bot)
            
    embed = discord.Embed(
        title="📢  Weekly News\n",
        description="‎",
        color=discord.Color.blue()
    )

    embed.add_field(name="📰  Announcements", value="‎\n"+news_announcement, inline=False)
    embed.add_field(name="🔥  Posts", value="‎\n"+news_billboard+"‎\n", inline=False)
    embed.set_footer(text="Stay tuned for more updates!")
    return embed

async def get_top_tip():
    with open("top_tips.txt", "r") as f:
        tip = choice(f.readlines().split("\n")).strip()
    return tip

class NewsCog(commands.Cog):
    async def __init__(self, bot):
        self.bot = bot
        await self.schedule_news_loop()

    @tasks.loop(hours=24)
    async def send_news(self):
        if datetime.datetime.now().weekday() == 0:
            general_channel = self.bot.get_channel(1279143050496442471)
            
            await general_channel.send("Tip: "+await get_top_tip())
        elif datetime.datetime.now().weekday() == 4:
            general_channel = self.bot.get_channel(1279143050496442471)
            
            await general_channel.send(embed=await get_latest_news_embed(self.bot))
                
            data = load_news_data()
            data["announcement"] = data["next_announcement"]
            data["messages"] = data["next_messages"]
            data["next_announcement"] = ""
            data["next_messages"] = []
            save_news_data(data)
            
            print("News round has been reset.")

    @commands.Cog.command()
    @commands.has_permissions(administrator=True)
    async def news_set(self, ctx, *, announcement):
        data = load_news_data()
        data["next_announcement"] = announcement
        save_news_data(data)
        await ctx.send(f"Next news announcement set to: {announcement}")

    @commands.Cog.command()
    async def add_news(self, ctx, *, message):
        await ctx.send("Its !news_add you idiot but Ill be kind and do it for you this time.")
        await self.news_add(ctx, message=message)

    @commands.Cog.command()
    async def news_add(self, ctx, *, message):
        data = load_news_data()
        message.replace("\\n", "\n").replace("@", "[@]").replace("<", "[<]").replace(">", "[>]")

        if any(i_message.get("user_id") == ctx.author.id for i_message in data["next_messages"]):
            await ctx.send("You've already added a post for next week!")
            return

        if len(data["next_messages"]) < 10:
            data["next_messages"].append({"user_id": ctx.author.id, "message": message})
            save_news_data(data)
            await ctx.send(f"Your post has been added to next week's news: {message}")
        else:
            await ctx.send("The billboard is full for next week. Come back after Friday!")

    @commands.Cog.command()
    async def news(self, ctx):
        await ctx.send(embed=await get_latest_news_embed(self.bot))

    async def schedule_news_loop(self):
        now = datetime.datetime.now()
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # if its later than 9am, schedule for next day
        if now >= target: target += datetime.timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        print(f"Waiting {wait_seconds} seconds until 09:00")

        await asyncio.sleep(wait_seconds)
        
        await self.send_news.start()

async def setup(bot):
    await bot.add_cog(NewsCog(bot))