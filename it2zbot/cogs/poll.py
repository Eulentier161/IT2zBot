from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
from unicodedata import lookup

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


@dataclass
class Option:
    text: str
    emote: str

    def as_list_item(self):
        return f"- {self.emote}: {self.text}"

# TODO: db to manage poll state
class PollCog(commands.GroupCog, name="poll"):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="create")
    async def create_poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: Optional[str],
        option4: Optional[str],
        option5: Optional[str],
        option6: Optional[str],
        option7: Optional[str],
        option8: Optional[str],
        option9: Optional[str],
        option10: Optional[str],
    ):
        options = [option1, option2, option3, option4, option5, option6, option7, option8, option9, option10]
        options: list[str] = [o for o in options if o is not None]
        options: list[Option] = [Option(text=o, emote=lookup(f"REGIONAL INDICATOR SYMBOL LETTER {chr(i+97)}")) for i, o in enumerate(options)]

        embed = discord.Embed(title=question, description="\n".join(option.as_list_item() for option in options))

        await interaction.response.send_message(embed=embed)
        m = await interaction.original_response()
        for option in options:
            await m.add_reaction(option.emote)

    @commands.Cog.listener("on_raw_reaction_add")
    async def vote_add_listener(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        print(payload)

    @commands.Cog.listener("on_raw_reaction_remove")
    async def vote_remove_listener(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        print(payload)
