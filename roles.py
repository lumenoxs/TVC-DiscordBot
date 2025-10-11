from discord.ext import commands

roles = {}
roles["📢"] = 1336384963767173170
roles["⚙️"] = 1336379853829705781
roles["📊"] = 1313604458143420526
roles["🚨"] = 1313604650372563016
roles["🍎"] = 1412722373777428500
roles["🍃"] = 1412722480593899622
roles[1355953585543713059] = 1424466785431716031 # 1.8
roles[1426619624602079342] = 1424463163805536366 # 1.9+
roles[1426620072914325625] = 1424463049393442989 # mace
roles[1426620730002641116] = 1426621910070067210 # pots

roles_file = "rolesmsg.txt"

class RolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, plyd):
        user = plyd.member
        if user.bot:
            return
        message = await self.bot.get_channel(plyd.channel_id).fetch_message(plyd.message_id)
        if message.channel.id == 1412708336536653886 and not message.id == 0:
            if plyd.emoji.name in roles.keys():
                role = user.guild.get_role(roles[plyd.emoji.name])
                if role in user.roles:
                    await user.send(f"You already have the role {role.name}!")
                    return
                print(f"Added role {role.name} to {user.display_name}")
                await user.add_roles(role)
                await user.send(f"Added role {role.name}!")
            elif plyd.emoji.id in roles.keys():
                role = user.guild.get_role(roles[plyd.emoji.id])
                if role in user.roles:
                    await user.send(f"You already have the role {role.name}!")
                    return
                print(f"Added role {role.name} to {user.display_name}")
                await user.add_roles(role)
                await user.send(f"Added role {role.name}!")
                    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, plyd):
        user = self.bot.get_guild(1279143050496442469).get_member(plyd.user_id)
        if user.bot:
            return
        message = await self.bot.get_channel(plyd.channel_id).fetch_message(plyd.message_id)
        if message.channel.id == 1412708336536653886 and not message.id == 0:
            if plyd.emoji.name in roles.keys():
                role = user.guild.get_role(roles[plyd.emoji.name])
                if role not in user.roles:
                    await user.send(f"You don't have the role {role.name}!")
                    return
                print(f"Removed role {role.name} from {user.display_name}")
                await user.remove_roles(role)
                await user.send(f"Removed role {role.name}!")
            elif plyd.emoji.id in roles.keys():
                role = user.guild.get_role(roles[plyd.emoji.id])
                if role not in user.roles:
                    await user.send(f"You don't have the role {role.name}!")
                    return
                print(f"Removed role {role.name} from {user.display_name}")
                await user.remove_roles(role)
                await user.send(f"Removed role {role.name}!")
    
    @commands.command()
    async def roles_message(self, ctx):
        if ctx.author.guild_permissions.administrator == False: return

        with open(roles_file) as file:
            content = file.read()

        msg = await self.bot.get_channel(1412708336536653886).fetch_message(1413137650063511674)
        await msg.edit(content=content)

    @commands.command()
    async def roles_reactions(self, ctx):
        if ctx.author.guild_permissions.administrator == False: return
        
        msg = await self.bot.get_channel(1412708336536653886).fetch_message(1413137650063511674)
        for reaction in msg.reactions:
            if reaction.emoji not in roles.keys():
                continue
            async for user in reaction.users():
                if user.bot:
                    continue
                member = ctx.guild.get_member(user.id)
                role = ctx.guild.get_role(roles[reaction.emoji])
                if role not in member.roles:
                    print(f"Added role {role.name} to {member.display_name}")
                    await member.add_roles(role)
                    await member.send(f"The bot was down when you reacted to the message. Added role {role.name}!")

    @commands.command()
    async def roles_add_reactions(self, ctx):
        if ctx.author.guild_permissions.administrator == False: return
        
        msg = await self.bot.get_channel(1412708336536653886).fetch_message(1413137650063511674)
        for emoji in roles.keys():
            if type(emoji) == int:
                emoji = self.bot.get_emoji(emoji)
            await msg.add_reaction(emoji)
            
async def setup(bot):
    await bot.add_cog(RolesCog(bot))
