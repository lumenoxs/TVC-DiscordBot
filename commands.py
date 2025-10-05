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
channels["alerts"] = 1312528601253412945

class CommandsCog(commands.Cog):
    @commands.command()
    async def ping(self, ctx):
        await ctx.send("🏓 Pong!")
    
    # Discord member count

    @commands.command()
    async def members(self, ctx):
        if ctx.channel.id != channels["bot"]:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            await ctx.send(f"Please use all commands in <#{channels['bot']}>.", delete_after=3)
            return
        member_count = ctx.guild.member_count
        embed = discord.Embed(
            title="Discord Member Count",
            description=f"Total Members: `{member_count}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def get_message(self, ctx, message_id: int):
        if ctx.author.guild_permissions.administrator == False:
            await ctx.send("You do not have permission to use this command.")
            return
        try:
            message = await ctx.channel.fetch_message(message_id)
            await ctx.send(f"Message content: {message.content}")
        except discord.NotFound:
            await ctx.send("Message not found.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to fetch messages.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.CommandNotFound):
            await ctx.send("Couldnt find that command :/")
            print(f"Wrong command ran by {ctx.author.display_name}, {ctx.author.name}")
        else:
            await ctx.send("An error occurred while processing the command.")
            await self.bot.get_channel(channels["alerts"]).send(f"Error occurred: {str(error)}")
            raise error
        
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(CommandsCog(bot))