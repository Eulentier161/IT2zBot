import io
import os
import re
import textwrap
import traceback
from contextlib import redirect_stdout

import config
import discord
from discord.ext import commands
from discord.ext.commands import TextChannelConverter
from util.converters import Converter
from util.util import Utils


class AdminCog(commands.Cog):
    """various administrative commands"""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    def cleanup_code(self, content: str):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

    # check if author has higher role than targeted role/member
    async def check_role_hierarchy(self, ctx, author, target):

        if ctx.message.author.id in config.Config.instance().get_admin_ids():
            return True

        role_hierarchy = ctx.guild.roles
        author_top_role = author.top_role

        if isinstance(target, discord.Member):
            target = target.top_role

        try:
            if role_hierarchy.index(author_top_role) > role_hierarchy.index(target):
                return True
            else:
                return False
        except Exception:
            return True

    @commands.command(pass_context=True, hidden=True, name="eval")
    @commands.is_owner()
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code block"""

        if isinstance(ctx.channel, discord.DMChannel):
            env = {
                "bot": self.bot,
                "ctx": ctx,
                "channel": ctx.channel,
                "author": ctx.author,
                "message": ctx.message,
                "_": self._last_result,
            }

        if isinstance(ctx.channel, discord.TextChannel):
            env = {
                "bot": self.bot,
                "ctx": ctx,
                "channel": ctx.channel,
                "author": ctx.author,
                "guild": ctx.guild,
                "message": ctx.message,
                "_": self._last_result,
            }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("\u2705")
            except Exception:
                pass

            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                self._last_result = ret
                await ctx.send(f"```py\n{value}{ret}\n```")

    @commands.command(name="gitpull", hidden=True)
    @commands.is_owner()
    async def _gitpull_cmd(self):
        project_dir = Utils.get_project_root()
        os.system(f"git -C {project_dir} pull")
        await self.bot.close()

    @commands.command("ban")
    @commands.has_guild_permissions(ban_members=True)
    async def ban_cmd(self, ctx, *_users):

        users = []
        for user in _users:
            string_for_mention = re.sub("<|!|@|>", "", user)
            try:
                user = await self.bot.fetch_user(int(string_for_mention))
                users.append(user)
            except Exception:
                pass

        response_confirm = ""
        response_deny = ""

        for user in users:
            if not await self.check_role_hierarchy(ctx, ctx.message.author, user):
                response_deny += f" `{user.name}#{user.discriminator}`"
            else:
                try:
                    await ctx.guild.ban(user)
                    response_confirm += f" `{user.name}#{user.discriminator}`"
                except Exception:
                    pass

        if response_confirm:
            await ctx.message.channel.send(f"banned{response_confirm}")
            await ctx.message.add_reaction("🔨")
        if response_deny:
            await ctx.message.channel.send(f"couldnt ban{response_deny}")
            await ctx.message.add_reaction("❌")

    @commands.command("unban")
    @commands.has_guild_permissions(ban_members=True)
    async def unban_cmd(self, ctx, *users: discord.User):

        response_confirm = ""
        response_deny = ""

        for user in users:
            if not await self.check_role_hierarchy(ctx, ctx.message.author, user):
                response_deny += f" `{user.name}#{user.discriminator}`"
            else:
                try:
                    await ctx.guild.unban(user)
                    response_confirm += f" `{user.name}#{user.discriminator}`"
                except Exception:
                    pass

        if response_confirm:
            await ctx.message.channel.send(f"unbanned{response_confirm}")
            await ctx.message.add_reaction("♻️")
        if response_deny:
            await ctx.message.channel.send(f"couldnt unban{response_deny}")
            await ctx.message.add_reaction("❌")

    @commands.command("kick")
    @commands.has_guild_permissions(kick_members=True)
    async def kick_cmd(self, ctx, *users):

        users_converted = []
        for user in users:
            user = await Converter.convert_member(ctx, user)
            users_converted.append(user)

        response_confirm = ""
        response_deny = ""
        for user in users_converted:
            if not await self.check_role_hierarchy(ctx, ctx.message.author, user):
                response_deny += f" `{user.name}#{user.discriminator}`"
            else:
                try:
                    await ctx.guild.kick(user)
                    response_confirm += f" `{user.name}#{user.discriminator}`"
                except Exception:
                    pass

        if response_confirm:
            await ctx.message.channel.send(f"kicked{response_confirm}")
            await ctx.message.add_reaction("👢")
        if response_deny:
            await ctx.message.channel.send(f"couldnt kick{response_deny}")
            await ctx.message.add_reaction("❌")

    @commands.command("setnick")
    @commands.has_guild_permissions(manage_nicknames=True)
    async def setnick_cmd(self, ctx, member, *, nick=None):

        member = await Converter.convert_member(ctx, member)
        if not member:
            await ctx.message.add_reaction("❌")
            return

        if not await self.check_role_hierarchy(ctx, ctx.message.author, member):
            await ctx.message.add_reaction("❌")
            return

        await member.edit(nick=nick)
        await ctx.message.add_reaction("☑️")

    @commands.command(aliases=["setchannelname", "schn"])
    @commands.has_guild_permissions(manage_channels=True)
    async def setchannelname_cmd(self, ctx, *, name=None):

        if name.startswith("<#"):
            channelid = name.partition("<#")[2].partition(">")[0]
            channel = self.bot.get_channel(int(channelid))
            await channel.edit(name=name.partition(">")[2])
        else:
            channel = ctx.message.channel
            await channel.edit(name=name)

        await ctx.message.add_reaction("☑️")

    @commands.command(aliases=["setchanneltopic", "scht"])
    @commands.has_guild_permissions(manage_channels=True)
    async def setchanneltopic_cmd(self, ctx, *, topic=None):

        if topic.startswith("<#"):
            channelid = topic.partition("<#")[2].partition(">")[0]
            channel = self.bot.get_channel(int(channelid))
            await channel.edit(topic=topic.partition(">")[2])
        else:
            channel = ctx.message.channel
            await channel.edit(topic=topic)

        await ctx.message.add_reaction("☑️")

    @commands.command(aliases=["setrole", "sr"])
    @commands.has_guild_permissions(manage_roles=True)
    async def setrole_cmd(self, ctx, user, *, role):

        user = await Converter.convert_member(ctx, user)
        if not user:
            await ctx.message.add_reaction("❌")
            return

        role = await Converter.convert_role(ctx, role)
        if not role:
            await ctx.message.add_reaction("❌")
            return

        if not await self.check_role_hierarchy(ctx, ctx.message.author, role):
            await ctx.message.add_reaction("❌")
            return

        await user.add_roles(role)
        await ctx.message.add_reaction("☑️")

    @commands.command(aliases=["removerole", "rr"])
    @commands.has_guild_permissions(manage_roles=True)
    async def removerole_cmd(self, ctx, user, *, role):

        user = await Converter.convert_member(ctx, user)
        if not user:
            await ctx.message.add_reaction("❌")
            return

        role = await Converter.convert_role(ctx, role)
        if not role:
            await ctx.message.add_reaction("❌")
            return

        if not await self.check_role_hierarchy(ctx, ctx.message.author, role):
            await ctx.message.add_reaction("❌")
            return

        await user.remove_roles(role)
        await ctx.message.add_reaction("☑️")

    @commands.command(aliases=["createrole", "cr"])
    @commands.has_guild_permissions(manage_roles=True)
    async def createrole_cmd(self, ctx, *, role=None):
        if not role:
            await ctx.message.add_reaction("❌")
            return

        await ctx.guild.create_role(name=role)
        await ctx.message.add_reaction("☑️")

    @commands.command(aliases=["deleterole", "dr"])
    @commands.has_guild_permissions(manage_roles=True)
    async def deleterole_cmd(self, ctx, *, role=None):
        if not role:
            await ctx.message.add_reaction("❌")
            return

        role = await Converter.convert_role(ctx, role)
        if not role:
            await ctx.message.add_reaction("❌")
            return

        await role.delete()
        await ctx.message.add_reaction("☑️")

    @commands.command("addemote")
    @commands.has_guild_permissions(manage_emojis=True)
    async def addemote_cmd(self, ctx, emote: discord.PartialEmoji, name=None):
        """
        adds an emote to the current server\n
        only works with existing discord emotes
        """
        if not name:
            await ctx.message.add_reaction("❌")

        emote = emote.url_as()
        emote = await emote.read()
        await ctx.guild.create_custom_emoji(name=name, image=emote)
        await ctx.message.add_reaction("☑️")

    @commands.command(aliases=["removeemote", "rmemote"])
    @commands.has_guild_permissions(manage_emojis=True)
    async def removeemote_cmd(self, ctx, emote: discord.Emoji):
        if not emote:
            await ctx.message.add_reaction("❌")
            return

        await emote.delete()
        await ctx.message.add_reaction("☑️")

    @commands.command("lock")
    @commands.has_guild_permissions(manage_guild=True)
    async def lock_cmd(self, ctx, channel=None):

        # if user didnt input an argument, default to current channel
        if not channel:
            channel = ctx.message.channel

        # if channel isnt current channel try to convert the argument to a channel object
        if channel != ctx.message.channel:
            try:
                channel = await TextChannelConverter().convert(ctx, channel)
            except Exception as e:
                await ctx.message.add_reaction("❌")
                dm_channel = await Utils.get_dm_channel(ctx.author)
                await dm_channel.send(
                    f"Error in command: {ctx.message.jump_url}\n```py\n{e}\n```"
                )
                return

        # do the actual lock
        permission = channel.overwrites_for(ctx.guild.default_role)
        permission.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=permission)

        # confirm lock
        await ctx.message.add_reaction("🔒")
        await ctx.message.add_reaction("🤫")

    @commands.command("unlock")
    @commands.has_guild_permissions(manage_guild=True)
    async def unlock_cmd(self, ctx, channel=None):

        if not channel:
            channel = ctx.message.channel

        if channel != ctx.message.channel:
            try:
                channel = await TextChannelConverter().convert(ctx, channel)
            except Exception as e:
                await ctx.message.add_reaction("❌")
                dm_channel = await Utils.get_dm_channel(ctx.author)
                await dm_channel.send(
                    f"Error in command: {ctx.message.jump_url}\n```py\n{e}\n```"
                )
                return

        permission = channel.overwrites_for(ctx.guild.default_role)
        permission.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=permission)

        await ctx.message.add_reaction("🔓")
        await ctx.message.add_reaction("📣")

    @commands.command(aliases=["setslowmode", "slowmode"])
    @commands.has_guild_permissions(manage_channels=True)
    async def setslowmode_cmd(self, ctx, *, duration=None):

        try:
            if duration.startswith("<#"):
                channelid = duration.partition("<#")[2].partition(">")[0]
                channel = self.bot.get_channel(int(channelid))
                await channel.edit(slowmode_delay=int(duration.partition(">")[2]))
            else:
                channel = ctx.message.channel
                await channel.edit(slowmode_delay=int(duration))
            await ctx.message.add_reaction("☑️")
        except Exception as e:
            await ctx.message.add_reaction("❌")
            dm_channel = await Utils.get_dm_channel(ctx.author)
            await dm_channel.send(
                f"Error in command: {ctx.message.jump_url}\n```py\n{e}\n```"
            )

    @commands.command(aliases=["roleclr", "rolecolour", "rolecolor"])
    @commands.has_guild_permissions(manage_roles=True)
    async def roleclr_cmd(self, ctx, role, color=None):
        if not color:
            await ctx.message.add_reaction("❌")
            return

        try:
            role = await Converter.convert_role(ctx, role)
        except Exception as e:
            await ctx.message.add_reaction("❌")
            dm_channel = await Utils.get_dm_channel(ctx.author)
            await dm_channel.send(
                f"Error in command: {ctx.message.jump_url}\n```py\n{e}\n```"
            )
            return

        if color == "default":
            color = discord.Colour.default()
        else:
            rgb = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))
            color = discord.Colour.from_rgb(rgb[0], rgb[1], rgb[2])

        await role.edit(color=color)
        await ctx.message.add_reaction("☑️")

    @commands.command(aliases=["deletetextchannel", "dtch"])
    @commands.has_guild_permissions(manage_channels=True)
    async def deletetextchannel_cmd(self, ctx, *, channel=None):
        if not channel:
            channel = ctx.channel
        else:
            try:
                channel = await Converter.convert_textchannel(ctx, channel)
            except Exception as e:
                dm_channel = await Utils.get_dm_channel(ctx.author)
                await dm_channel.send(
                    f"Error in command: {ctx.message.jump_url}\n```py\n{e}\n```"
                )
                return

        await channel.delete()
        try:
            await ctx.message.add_reaction("☑️")
        except Exception:
            pass

    @commands.command(aliases=["createtextchannel", "ctch"])
    @commands.has_guild_permissions(manage_channels=True)
    async def createtextchannel_cmd(self, ctx, *, name=None):
        if not name:
            await ctx.message.add_reaction("❌")
            return

        channel = await ctx.guild.create_text_channel(name)
        await ctx.message.add_reaction("☑️")
        await channel.send("first lmao 😎")
        await ctx.send(f"created new channel: {channel.mention}")

    @commands.command("prune")
    @commands.has_guild_permissions(administrator=True)
    async def prune_cmd(self, ctx, amount=None):
        try:
            amount = int(amount)
        except Exception as e:
            dm_channel = await Utils.get_dm_channel(ctx.author)
            await dm_channel.send(
                f"Error in command: {ctx.message.jump_url}\n```py\n{e}\n```"
            )
            return
        await ctx.channel.purge(limit=amount)
