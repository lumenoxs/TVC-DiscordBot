import discord
from discord.ext import commands
import json

factions_file = "factions.json"

def load_factions_data():
    try:
        with open(factions_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_faction(faction_thread_id):
    try:
        with open(factions_file, "r") as f:
            data = json.load(f)
            return data.get(faction_thread_id, False)
    except FileNotFoundError:
        return False

def save_factions_data(faction_thread_id, role_id):
    data = load_factions_data()
    data[str(faction_thread_id)] = role_id
    with open(factions_file, "w") as f:
        json.dump(data, f, indent=4)

class FactionFloodCheckView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Active", custom_id="active_faction", style=discord.ButtonStyle.secondary, row=0, emoji="❓")
    async def active_faction(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.floodcheck_response(interaction, button, "active")

    @discord.ui.button(label="Inactive/Suspended", custom_id="inactive_faction", style=discord.ButtonStyle.secondary, row=0, emoji="👤")
    async def inactive_faction(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.floodcheck_response(interaction, button, "inactive")

    @discord.ui.button(label="Dead/Disbanded", custom_id="dead_faction", style=discord.ButtonStyle.secondary, row=0, emoji="⚙️")
    async def dead_faction(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.floodcheck_response(interaction, button, "dead")

    async def floodcheck_response(self, interaction: discord.Interaction, button: discord.ui.Button, rtype: str):
        if any(load_faction(interaction.channel.id) == role.id for role in interaction.user.roles):
            await interaction.followup.send(
                "You are not part of this faction 🤔"
            )
            return
            
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        # I couldnt find anything online on how to disable all the buttons on a view, so the for loop above was done by chatgpt
        
        embed = discord.Embed(
            title="Faction Flood Check",
            description=f"A staff member triggered a faction flood check to update all currently existing factions.\n~~If you are a member of this faction, please select the button below that is the most relevant to this faction.~~\nThis was answered with the response: {rtype}",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.message.reply(
            f"This was marked by <@{interaction.user.id}> as {rtype}."
        )
        await interaction.followup.send(
            "Done! Thanks for replying."
        )
        await self.bot.get_channel(1312528601253412945).send(f"Please check the followup on https://discord.com/channels/1279143050496442469/1346851805665169469{interaction.channel.id}")

class FactionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def set_faction(self, ctx, fid: int, rid: int):
        save_factions_data(fid, rid)
    
    @commands.command()
    async def floodcheck(self, ctx):
        print("it ran")
        if ctx.author.id != 1225709819890110604:
            print("nono")
            return
        embed = discord.Embed(
            title="Faction Flood Check",
            description="A staff member triggered a faction flood check to update all currently existing factions.\nIf you are a member of this faction, please select the button below that is the most relevant to this faction.",
            color=discord.Color.blue()
        )

        factions_channel = self.bot.get_channel(1346851805665169469)

        threadies = []
        for thread in factions_channel.threads:
            threadies.append(thread)
        async for thread in factions_channel.archived_threads(limit=None):
            threadies.append(thread)
            
        print(len(threadies))

        for thread in threadies:
            thread_tags = []
            for thread_tag in thread.applied_tags:
                thread_tags.append(thread_tag.id)
            print("looped")
            print(thread_tags)
            if 1346887697595236452 in thread_tags and 1381717937320231083 not in thread_tags and 1387883441550528653 not in thread_tags and 1388028437490307122 not in thread_tags and load_faction(str(thread.id)):
                print("loop authorised")
                await thread.send(embed=embed, view=FactionFloodCheckView(bot=self.bot))
                await thread.send(f"<@&{load_faction(thread.id)}>")

async def setup(bot):
    await bot.add_cog(FactionsCog(bot))