from discord.ext import commands
import discord

channels = {}
channels["general"] = 1279143050496442471
channels["welcome"] = 0
channels["help"] = 0
channels["promo"] = 0
channels["memes"] = 0
channels["spam"] = 0
channels["dank"] = 0
channels["alerts"] = 0
channels["staff_spam"] = 0
channels["join_cmd"] = [channels["general"], channels["spam"], channels["help"], channels["staff_spam"]]

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("🏓 Pong!")
        
    # Server join info

    @commands.command()
    async def join(self, ctx):
        if ctx.channel.id not in channels["join_cmd"]:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            await ctx.send(f"Please use all commands in <#{INFO["CHANNELS"]["BOT"]}>.", delete_after=5)
            return
        main = discord.Embed(
            title="Server IP",
            description=f"**IP:** `{INFO["IP"]}`\n**Version:** `{INFO["VERSIONS"]}`",
            color=discord.Color.blue()
        )
        await ctx.send(embed=main)
        
    # Server info

    @commands.command()
    async def info(self, ctx):
        if ctx.channel.id != INFO["CHANNELS"]["BOT"]:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            await ctx.send(f"Please use all commands in <#{INFO["CHANNELS"]["BOT"]}>.", delete_after=5)
            return
        url = f"https://api.mcstatus.io/v2/status/java/{INFO["IP"]}"
        data = get_data(url)
        
        server_status = "**Status:** `Offline`" if not data or not data["online"] else "**Status:** `Online`"
        
        embed = discord.Embed(
            title="Server Info",
            description=f"**IP:** `{INFO["IP"]}`\n**Version:** `{INFO["VERSIONS"]}`\n{server_status}",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
        
    # Vote links

    @commands.command()
    async def vote(self, ctx):
        main = discord.Embed(
            title="Vote",
            description="**Thank you for voting!**\n[1 - VOTE](https://example.com)",
            color=discord.Color.blue()
        )
        await ctx.send(embed=main)

    # Server status

    @commands.command()
    async def status(self, ctx):
        if ctx.channel.id != INFO["CHANNELS"]["BOT"]:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            await ctx.send(f"Please use all commands in <#{INFO["CHANNELS"]["BOT"]}>.", delete_after=5)
            return
        url = f"https://api.mcstatus.io/v2/status/java/{INFO["IP"]}"
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

    @commands.command()
    async def members(self, ctx):
        if ctx.channel.id != INFO["CHANNELS"]["BOT"]:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            await ctx.send(f"Please use all commands in <#{INFO["CHANNELS"]["BOT"]}>.", delete_after=5)
            return
        member_count = ctx.guild.member_count
        embed = discord.Embed(
            title="Discord Member Count",
            description=f"Total Members: `{member_count}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.event
    async def on_command_error(ctx, error):
        if isinstance(error, discord.ext.commands.errors.CommandNotFound):
            await ctx.send("Not a command >:|")
            print(f"Wrong command ran by {ctx.author.display_name}, {ctx.author.name}")
        else:
            raise error

def setup(bot):
    commands.add_cog(CommandsCog(bot))