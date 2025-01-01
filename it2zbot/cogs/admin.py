import io
import textwrap
import traceback
from asyncio import TimeoutError
from contextlib import redirect_stdout
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class AdminCog(commands.Cog):
    def __init__(self, bot: "MyBot"):
        self.bot = bot
        self._last_result = None

    def cleanup_code(self, content: str) -> str:
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

    @commands.command(pass_context=True, hidden=True, name="eval")
    # @commands.is_owner()
    async def _eval(self, ctx: commands.Context, *, body: str):
        """Evaluates a code"""

        # get my approval to execute code from other members
        if ctx.author.id != 958611742118785125:
            # guard priv messages as i cant approve in those
            if ctx.guild is None:
                return

            for r in ["\u2705", "\u274C"]:
                await ctx.message.add_reaction(r)

            def check(reaction: discord.Reaction, user: discord.User):
                is_owner = user.id == 958611742118785125
                if is_owner and reaction.emoji == "\u274C":
                    raise TimeoutError
                return is_owner and reaction.emoji == "\u2705"

            try:
                await self.bot.wait_for("reaction_add", check=check)
            except TimeoutError:
                return
            finally:
                await ctx.message.clear_reactions()

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
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("\u2705")
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                self._last_result = ret
                await ctx.send(f"```py\n{value}{ret}\n```")
