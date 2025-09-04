from discord.ext import commands

roles = {}
roles[1362484007714951349] = 1362306221281120287
roles[1387837470300835900] = 1362306409789915147
roles["📢"] = 1336384963767173170
roles["⚙️"] = 1336379853829705781
roles["📊"] = 1313604458143420526
roles["🚨"] = 1313604650372563016
roles["🍎"] = 1412722373777428500
roles["🍃"] = 1412722480593899622

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
            if plyd.emoji.id is None and plyd.emoji.name in roles.keys():
                role = user.guild.get_role(roles[plyd.emoji.name])
                if role:
                    print(f"Added role {role.name} to {user.display_name}")
                    await user.add_roles(role)
                    await user.send(f"Added role {role.name}!")
            if plyd.emoji.id in roles.keys():
                role = user.guild.get_role(roles[plyd.emoji.id])
                if role:
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
            if plyd.emoji.id is None and plyd.emoji.name in roles.keys():
                role = user.guild.get_role(roles[plyd.emoji.name])
                if role:
                    print(f"Removed role {role.name} from {user.display_name}")
                    await user.remove_roles(role)
                    await user.send(f"Removed role {role.name}!")
            if plyd.emoji.id in roles.keys():
                role = self.bot.get_guild(1279143050496442469).get_role(roles[plyd.emoji.id])
                if role:
                    print(f"Removed role {role.name} from {user.display_name}")
                    await user.remove_roles(role)
                    await user.send(f"Removed role {role.name}!")
    
    @commands.command()
    async def updaterolesmsg(self, ctx):
        with open(roles_file) as file:
            content = file.read()

        msg = await self.bot.get_channel(1412708336536653886).fetch_message(1413137650063511674)
        await msg.edit(content=content)
            
async def setup(bot):
    await bot.add_cog(RolesCog(bot))
