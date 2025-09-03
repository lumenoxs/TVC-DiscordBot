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
    
    # Discord member count

    @commands.command()
    async def members(self, ctx):
        if ctx.channel.id != channels["bot"]:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            await ctx.send(f"Please use all commands in <#{channels["bot"]}>.", delete_after=3)
            return
        member_count = ctx.guild.member_count
        embed = discord.Embed(
            title="Discord Member Count",
            description=f"Total Members: `{member_count}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(ctx, error):
        if isinstance(error, discord.ext.commands.errors.CommandNotFound):
            await ctx.send("Couldnt find that command :/")
            print(f"Wrong command ran by {ctx.author.display_name}, {ctx.author.name}")
        else:
            raise error

def setup(bot):
    commands.add_cog(CommandsCog(bot))