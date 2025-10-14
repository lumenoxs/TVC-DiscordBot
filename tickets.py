import discord
from discord.ext import commands
import json
import random
import aiohttp
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

class TicketModel(discord.ui.Modal, title="Tickets"):
    issue = discord.ui.TextInput(
        label="Issue",
        placeholder="Enter your issue here...",
        style=discord.TextStyle.paragraph
    )

    def __init__(self, user: discord.User, channel: discord.abc.Messageable, ticket_type: str, bot):
        super().__init__()
        self.bot = bot
        self.user = user
        self.channel = channel
        self.ticket_type = ticket_type

    async def on_submit(self, interaction: discord.Interaction):
        ticket_type = self.ticket_type
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        data = load_tickets_data()
        
        if user.id in data.values():
            await interaction.followup.send("You already have a ticket open!", ephemeral=True)
            return

        number_ticket = random.randint(1, 999)
        thread = await interaction.channel.create_thread(
            name=f"Ticket - {ticket_type} - {str(number_ticket).zfill(3)}",
            type=discord.ChannelType.private_thread,
            invitable=True
        )


        await thread.send(user.mention, delete_after=1)

        # Add staff members
        role = interaction.guild.get_role(1362668964177772565)
        await thread.send(role.mention, delete_after=1)
        

        embed = discord.Embed(
            description=f"**A {ticket_type} ticket opened by {user.mention}.\nThey entered this issue:\n```{self.issue.value}```**\nSupport will be with you shortly.",
            color=discord.Color.blue()
        )

        await thread.send(embed=embed, view=CloseTicket(self.bot))
        save_tickets_data(thread.id, user.id)
        await interaction.followup.send(f"✅ Your ticket has been created: {thread.mention}", ephemeral=True)
        

class PlayerAlertModal(discord.ui.Modal, title="Tickets"):
    player = discord.ui.TextInput(
        label="Player",
        placeholder="Enter the player name here...",
        style=discord.TextStyle.short,
        required=True
    )
    problem = discord.ui.TextInput(
        label="Problem",
        placeholder="Enter what the player is doing wrong here...",
        style=discord.TextStyle.paragraph,
        default="Hacking",
        required=True
    )
    proof = discord.ui.TextInput(
        label="Proof",
        placeholder="Enter any proof you have here (not needed but recommended)",
        style=discord.TextStyle.short,
        required=False
    )

    def __init__(self, user: discord.User, channel: discord.abc.Messageable, bot):
        super().__init__()
        self.bot = bot
        self.user = user
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        alerts_channel = self.bot.get_channel(1312528601253412945)

        await alerts_channel.send(f"# 🚨 Player Alert from {user.mention}\n**Player causing issue:** {self.player.value.replace("@", "[@]").replace("<", "[<]").replace(">", "[>]")}\n**Issue:** ```{self.problem.value.replace("@", "[@]").replace("<", "[<]").replace(">", "[>]")}```\n**Proof:**: `{self.proof.value.replace("@", "[@]").replace("<", "[<]").replace(">", "[>]")}`\n-# <@&1362668964177772565>")

        await interaction.followup.send("✅ An alert has been sent. Thanks!", ephemeral=True)

class AppealModal(discord.ui.Modal, title="Appeal"):
    mcign = discord.ui.TextInput(label="Minecraft IGN", placeholder="Enter your Minecraft Username/IGN here...", style=discord.TextStyle.short)
    temppermaban = discord.ui.TextInput(label="Temporary or permanent ban?", placeholder="Enter the type of your ban here...", style=discord.TextStyle.short)
    reasonban = discord.ui.TextInput(label="Reason for ban", placeholder="Enter the reason for your ban here...", style=discord.TextStyle.short)
    excuse = discord.ui.TextInput(label="Why do you think the ban was injustified?", placeholder="Enter the reason why you think you shouldn't have been banned here...", style=discord.TextStyle.long)
 
    def __init__(self, user: discord.User, channel: discord.abc.Messageable, bot):
        super().__init__()
        self.bot = bot
        self.user = user
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        data = load_tickets_data()
        
        if user.id in data.values():
            await interaction.followup.send("You already have an ticket/appeal open!", ephemeral=True)
            return

        thread = await interaction.channel.create_thread(
            name=f"Ticket - Appeal - {user.name}",
            type=discord.ChannelType.private_thread,
            invitable=True
        )

        await thread.send(user.mention, delete_after=1)

        # Add staff members
        role = interaction.guild.get_role(1362668964177772565)
        await thread.send(role.mention, delete_after=1)
        
        embed = discord.Embed(
            description=f"**An appeal has been opened by {user.mention}.**\n\n**They entered the below information:**\n**Their Minecraft IGN:**\n`{self.mcign.value}`\n**The reason for their ban:**\n{self.reasonban.value}\n**If its permanent or temporary and for how long if its temporary:**\n{self.temppermaban.value}\n**Why they believe they shouldn't have been banned:**\n{self.excuse.value}\n\nPlease also @mention any users that are witnesses or related to the ban.",
            color=discord.Color.blue()
        )

        await thread.send(embed=embed, view=CloseTicket(self.bot))
        save_tickets_data(thread.id, user.id)
        await interaction.followup.send(f"✅ Your appeal has been created: {thread.mention}", ephemeral=True)

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
            await webhook.send(role.mention, allowed_mentions=discord.AllowedMentions(roles=True))
        await interaction.response.send_message("✅ Alert sent!", ephemeral=True)

class SuggestModal(discord.ui.Modal, title="Suggestions"):
    alert = discord.ui.TextInput(
        label="Suggestion",
        placeholder="Enter your suggestion here...",
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

class QuestionReplyModal(discord.ui.Modal, title="Reply"):
    alert = discord.ui.TextInput(
        label="Reply",
        placeholder="Enter your reply here...",
        style=discord.TextStyle.paragraph
    )

    def __init__(self, user: discord.User, message: int):
        super().__init__()
        self.user = user
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        content = self.alert.value
        embed = discord.Embed(
            title="Response:",
            description=content,
            color=discord.Color.blue()
        )
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(alerts_webhook, session=session)
            await webhook.send(embed=embed)
        await interaction.response.send_message("✅ Suggestion sent!", ephemeral=True)

class QuestionModal(discord.ui.Modal, title="Questions"):
    alert = discord.ui.TextInput(
        label="Question",
        placeholder="Enter your question here... (this will be anonymous)",
        style=discord.TextStyle.paragraph
    )

    def __init__(self, user: discord.User, channel: discord.abc.Messageable):
        super().__init__()
        self.user = user
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        content = self.alert.value
        embed = discord.Embed(
            title="❓ Question:",
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

    @discord.ui.button(label="Support", custom_id="general_ticket", style=discord.ButtonStyle.success, row=0)
    async def support_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModel(user=interaction.user, channel=interaction.channel, ticket_type="Support", bot=self.bot))

    @discord.ui.button(label="Server", custom_id="server_ticket", style=discord.ButtonStyle.success, row=0)
    async def server_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModel(user=interaction.user, channel=interaction.channel, ticket_type="Server", bot=self.bot))

    @discord.ui.button(label="Appeal", custom_id="appeal_ticket", style=discord.ButtonStyle.success, row=0)
    async def appeal_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AppealModal(user=interaction.user, channel=interaction.channel, bot=self.bot))

    @discord.ui.button(label="Player Alert", custom_id="player_alert", style=discord.ButtonStyle.success, row=1)
    async def player_alert(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PlayerAlertModal(user=interaction.user, channel=interaction.channel, bot=self.bot))

    @discord.ui.button(label="Quick Alert", custom_id="quick_alert", style=discord.ButtonStyle.success, row=1)
    async def quick_alert(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AlertModal(user=interaction.user, channel=interaction.channel))

    @discord.ui.button(label="Suggestion", custom_id="suggest_alert", style=discord.ButtonStyle.success, row=1)
    async def suggest_alert(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestModal(user=interaction.user, channel=interaction.channel))


class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def tickets(self, ctx):
        channel = self.bot.get_channel(1338143330286043259)
        await ctx.message.delete()
        await channel.purge(limit=20)

        embed = discord.Embed(
            title="Tickets",
            description="### Please choose the most relevant topic below.\n\n**Support:**\nGeneral issues\n**Server:**\nAnything to do with the server itself - lag, server is down, cant join\n**Appeal:**\nAppealing a minecraft ban\n\n**Player alert:**\nPlayer related issues - hacking, combat logging, racist/discriminatory language\n**Quick alert:**\nUrgent issues that should be immediate\n**Suggestion:**\nAny suggestions you have for the server or discord :D\n\n### Our team will get back to you shortly.",
            color=discord.Color.blue()
        )

        await ctx.send(embed=embed, view=TicketView(bot=self.bot))

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
