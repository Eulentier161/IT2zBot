import discord
from discord.ext import commands

from util.util import Utils


class SelfmanagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command("setclr")
    async def setcolor_cmd(self, ctx, color_hex: str = None):
        if not color_hex:
            return
        try:
            color = discord.Color.from_rgb(*[int(color_hex[i: i + 2], 16) for i in (0, 2, 4)])
        except Exception as e:
            await ctx.message.add_reaction("❌")
            dm_channel = await Utils.get_dm_channel(ctx.author)
            await dm_channel.send(f"```py\n{e}\n```")
            return
        uid = str(ctx.author.id)
        existing_roles = await ctx.guild.fetch_roles()
        if uid in [role.name for role in existing_roles]:
            for role in existing_roles:
                if role.name != uid:
                    continue
                await role.edit(color=color, reason="color role")
        else:
            new_role = await ctx.guild.create_role(name=uid, color=color, reason="color role")
            await ctx.author.add_roles(new_role)
        await ctx.message.add_reaction("✅")
