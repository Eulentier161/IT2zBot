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
