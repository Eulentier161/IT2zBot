import re

import discord
from config import Config
from discord.ext import commands
from util.db import Database


class InfoCog(commands.Cog):
    """
    various info related commands
    """

    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = Database()
        self.task_channel_id = Config.instance().get_tasks_channel()

    @commands.command(aliases=["collab", "collaborate"])
    async def collab_cmd(self, ctx):
        """
        get info about how you can improve the bot
        """
        desc = (
            "[This bot](https://github.com/Eulentier161/IT2zBot) is public on [GitHub](https://github.com).\n"
            + "Fork -> edit -> create a Pull Request, if you'd like to improve the bot.\nThis is supposed to be a community project. <3"
        )
        embed = discord.Embed(title="Collaborate", url="https://github.com/Eulentier161/IT2zBot", description=desc, color=0x039307)
        await ctx.send(embed=embed)

    @commands.command("create_task")
    async def create_new_task_cmd(self, ctx, *, inp: str = None):
        """
        create a new task and store it in the database; this will be broadcasted to the current-tasks channel
        """
        try:
            title, details = map(lambda s: s.strip(), inp.split("--title")[1].split("--details"))
        except (ValueError, IndexError):
            return await ctx.send("malformed input arguments. `?create_new_task --title my title --description my description`")
        channel: discord.TextChannel = await self.bot.fetch_channel(self.task_channel_id)
        embed = discord.Embed(title=title, description=details, color=0x008000)
        msg: discord.Message = await channel.send(embed=embed)
        self.db.create_tasks_entry(str(msg.id), title, details)
        await ctx.message.add_reaction("☑️")

    @commands.command("delete_task")
    async def delete_task_cmd(self, ctx, message_id: str = None):
        """
        delete a task from the current-tasks channel
        """
        channel: discord.TextChannel = await self.bot.fetch_channel(self.task_channel_id)
        try:
            msg: discord.Message = await channel.fetch_message(int(message_id))
        except ValueError:
            return await ctx.send(f"parameter `message_id` has to be a number")
        except discord.NotFound:
            return await ctx.send(f"`message_id={int(message_id)}` not found")

        self.db.mark_task_deleted(msg.id)
        await msg.delete()
        await ctx.message.add_reaction("☑️")

    @commands.command("edit_task")
    async def edit_task_cmd(self, ctx, message_id: str = None, *, inp: str = None):
        """
        edit a currently active task
        """
        kwargs = {}
        title = None
        details = None
        try:
            if "--title" in inp:
                title = inp.split("--title")[1]
                if "--details" in title:
                    title = title.split("--details")[0]
                kwargs["title"] = title
            if "--details" in inp:
                details = inp.split("--details")[1]
                kwargs["details"] = details
        except (ValueError, IndexError):
            return await ctx.send("malformed input arguments.")
        channel: discord.TextChannel = await self.bot.fetch_channel(self.task_channel_id)
        try:
            msg: discord.Message = await channel.fetch_message(int(message_id))
        except ValueError:
            return await ctx.send(f"parameter `message_id` has to be a number")
        except discord.NotFound:
            return await ctx.send(f"`message_id={int(message_id)}` not found")

        task = self.db.get_active_task(msg.id)
        embed = discord.Embed(title=title if title else task["title"], description=details if details else task["details"], color=0x008000)

        if not kwargs:
            return

        await msg.edit(embed=embed)
        self.db.update_task(msg_id=msg.id, **kwargs)
        await ctx.message.add_reaction("☑️")
