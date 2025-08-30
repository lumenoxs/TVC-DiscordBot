import discord
from discord.ext import commands
import json
import random
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

tickets_file = "tickets.json"

load_dotenv("webhooks.env")
alerts_webhook = os.getenv("ALERTS")

def load_tickets_data():
    try:
        with open(tickets_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_ticket(ticket_id):
    try:
        with open(tickets_file, "r") as f:
            data = json.load(f)
            return data.get(ticket_id, False)
    except FileNotFoundError:
        return False

def save_tickets_data(ticket_id, user):
    data = load_tickets_data()
    data[str(ticket_id)] = user
    with open(tickets_file, "w") as f:
        json.dump(data, f, indent=4)

class AlertModal(discord.ui.Modal, title="Send Quick Alert"):
    alert = discord.ui.TextInput(
        label="Quick Alert",
        placeholder="Type your alert here...",
        style=discord.TextStyle.paragraph
    )

    def __init__(self, user: discord.User, channel: discord.abc.Messageable):
        super().__init__()
        self.user = user
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        content = self.alert.value
        embed = discord.Embed(
            title=f"🚨 Alert from {self.user.display_name}:",
            description=content,
            color=discord.Color.dark_red()
        )

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(alerts_webhook, session=session)
            await webhook.send(embed=embed)
            role = interaction.guild.get_role(1362668964177772565)
            if role:
                await webhook.send(role.mention, allowed_mentions=discord.AllowedMentions(roles=True))
            else:
                await webhook.send("Error: Can't ping the role")
        await interaction.response.send_message("✅ Alert sent!", ephemeral=True)

class SuggestModal(discord.ui.Modal, title="Suggestions"):
    alert = discord.ui.TextInput(
        label="Suggestion",
        placeholder="Type your suggestion here...",
        style=discord.TextStyle.paragraph
    )

    def __init__(self, user: discord.User, channel: discord.abc.Messageable):
        super().__init__()
        self.user = user
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        content = self.alert.value
        embed = discord.Embed(
            title=f"💡 Suggestion from {self.user.display_name}:",
            description=content,
            color=discord.Color.blue()
        )
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(alerts_webhook, session=session)
            await webhook.send(embed=embed)
        await interaction.response.send_message("✅ Suggestion sent!", ephemeral=True)

class CloseTicket(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.grey, custom_id="close_ticket", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if isinstance(interaction.channel, discord.Thread):
            embed = discord.Embed(
                description=f"Ticket closed by {interaction.user.mention}",
                color=discord.Color.blue()
            )
            await interaction.channel.send(embed=embed)
            await interaction.channel.edit(archived=True)
            save_tickets_data(interaction.channel.id, False)
            await interaction.response.defer()
        else:
            await interaction.response.send_message("This can only be used in a thread.", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Support", custom_id="general_ticket", style=discord.ButtonStyle.secondary, row=0, emoji="❓")
    async def support_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Support")

    @discord.ui.button(label="Player", custom_id="player_ticket", style=discord.ButtonStyle.secondary, row=0, emoji="👤")
    async def player_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Player")

    @discord.ui.button(label="Server", custom_id="server_ticket", style=discord.ButtonStyle.secondary, row=0, emoji="⚙️")
    async def server_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Server")

    @discord.ui.button(label="Quick Alert", custom_id="quick_alert", style=discord.ButtonStyle.success, row=1, emoji="🚨")
    async def alert_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AlertModal(user=interaction.user, channel=interaction.channel))

    @discord.ui.button(label="Suggestion", custom_id="suggest_alert", style=discord.ButtonStyle.success, row=1, emoji="💡")
    async def suggest_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestModal(user=interaction.user, channel=interaction.channel))

    @discord.ui.button(label="Appeal", custom_id="appeal_ticket", style=discord.ButtonStyle.success, row=1, emoji="📩")
    async def appeal_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Appeal")

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        data = load_tickets_data()
        
        if user.id in data.values():
            await interaction.followup.send("You already have a ticket open!", ephemeral=True)
            return

        if ticket_type == "Appeal":
            thread = await interaction.channel.create_thread(
                name=f"Ticket - {ticket_type} - {user.name}",
                type=discord.ChannelType.private_thread,
                invitable=False
            )
        else:
            number_ticket = random.randint(1, 999)
            thread = await interaction.channel.create_thread(
                name=f"Ticket - {ticket_type} - {str(number_ticket).zfill(3)}",
                type=discord.ChannelType.private_thread,
                invitable=False
            )
        
        # Ensure thread members are fetched once
        await thread.fetch_members()
        thread_member_ids = {member.id for member in thread.members}

        # Collect users to add
        to_add = set()

        # Add the main user if not in thread
        if user.id not in thread_member_ids:
            to_add.add(user)

        # Add staff role members
        for role_id in self.bot.STAFF:
            role = interaction.guild.get_role(role_id)
            if role:
                for member in role.members:
                    if member.id not in thread_member_ids:
                        to_add.add(member)

        for member in to_add:
            try:
                await thread.add_user(member)
            except Exception as e:
                print(f"Failed to add {member.display_name}: {e}")
                await asyncio.sleep(0.5)
                await thread.add_user(member)

        embed = discord.Embed(
            description=f"**Ticket opened by {user.mention} for `{ticket_type}`.**\nSupport will be with you shortly.",
            color=discord.Color.blue()
        )
        
        if ticket_type == "Appeal":
            embed = discord.Embed(
                description=f"**An appeal has been opened by {user.mention}.**\n\n**Please, provide the below information first:**\n- Your Minecraft IGN\n- The reason for your ban\n- If its permanent or temporary\n- Why you believe you shouldn't have been banned\n\nPlease also @mention any users that are witnesses or related to the ban.",
                color=discord.Color.blue()
            )

        await thread.send(embed=embed, view=CloseTicket(self.bot))
        save_tickets_data(thread.id, user.id)
        if ticket_type == "Appeal":
            await interaction.followup.send(f"✅ Your appeal has been created: {thread.mention}", ephemeral=True)
        else:
            await interaction.followup.send(f"✅ Your ticket has been created: {thread.mention}", ephemeral=True)


class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def tickets(self, ctx):
        channel = self.bot.get_channel(1338143330286043259)
        await ctx.message.delete()
        if channel:
            await channel.purge(limit=20)

        embed = discord.Embed(
            title="Tickets",
            description="Please choose the most relevant topic below.\n\nSupport - **ONLY FOR ANYTHING NOT LISTED BELOW**\nPlayer - Player related issues - hacking, combat logging\nServer - Anything to do with the hardware - lag, rollback\nQuick alert - Something that doesnt need a conversation, but is urgent\nSuggestion - Any suggestions you may have for the server or discord!\nAppeal - To appeal a discord/minecraft ban/mute\n\nOur team will get back to you shortly.",
            color=discord.Color.blue()
        )

        await ctx.send(embed=embed, view=TicketView(bot=self.bot))

    @commands.command()
    async def get_id(self, ctx):
        await ctx.send(f"ID: {ctx.channel.id}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_ticket(self, ctx, user_id):
        save_tickets_data(ctx.channel.id, user_id)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clean(self, ctx, keep_thread: int):
        channel = self.bot.get_channel(1338143330286043259)
        if not channel:
            await ctx.send("Channel not found.")
            return

        threads = await channel.threads(limit=None)
        for thread in threads:
            if thread.id == keep_thread:
                continue
            try:
                await thread.delete()
                save_tickets_data(thread.id, False)
                await ctx.send(f"🧹 Deleted: {thread.name}")
            except Exception:
                await ctx.send(f"Couldn't delete {thread.name}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx):
        if isinstance(ctx.channel, discord.Thread):
            await ctx.send("Deleting this ticket...")
            await ctx.channel.delete()
            save_tickets_data(ctx.channel.id, False)
        else:
            await ctx.send("This can only be used in a thread.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx):
        if isinstance(ctx.channel, discord.Thread):
            await ctx.channel.edit(locked=True)
            await ctx.send("This ticket is now locked.")
        else:
            await ctx.send("This can only be used in a thread.")

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
