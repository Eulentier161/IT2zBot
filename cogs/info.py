from util.util import Utils
import re
import discord
from discord.ext import commands


class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["collab", "collaborate"])
    async def collab_cmd(self, ctx):
        desc = (
            "[This bot](https://github.com/Eulentier161/IT2zBot) is public on [GitHub](https://github.com).\n"
            + "Fork -> edit -> create a Pull Request, if you'd like to improve the bot.\nThis is supposed to be a community project. <3"
        )
        embed = discord.Embed(
            title="Collaborate",
            url="https://github.com/Eulentier161/IT2zBot",
            description=desc,
            color=0x039307,
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["aktuelle_aufgaben", "current_tasks"])
    async def current_tasks_cmd(self, ctx, *, inp: str):
        guild: discord.Guild = await self.bot.fetch_guild(958611525541720064)
        channel: discord.TextChannel = [channel for channel in await guild.fetch_channels() if channel.id == 959429833425825812][0]
        message: discord.Message = await channel.fetch_message(959547365512065036)
        try:
            matches = re.findall(r"field:.*?{(.+?)}", inp, re.DOTALL)
            embed = discord.Embed(title="Aktuelle Aufgaben", color=0x008000)
            for match in matches:
                name = re.findall(r"name:(.+?)value:", match, re.DOTALL)[0]
                value = re.findall(r"value:(.+)$", match, re.DOTALL)[0]
                embed.add_field(name=name, value=value, inline=False)
            await message.edit(embed=embed)
        except Exception as e:
            author_dm = await Utils.get_dm_channel(ctx.author)
            await author_dm.send(f"```py\n{e}\n```")
