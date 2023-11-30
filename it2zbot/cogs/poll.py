import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
from unicodedata import lookup
import re

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


def get_bar(n: int, total: int):
    if total == 0:
        return f"{'▒' * 10} {0:.2f}%"
    return f"{'▓' * round(n/total*10):▒<10} {n/total*100:.2f}%"


@dataclass
class Option:
    text: str
    emote: str

    def as_list_item(self):
        return f"- {self.emote}: {self.text}"


@dataclass
class Poll:
    poll_id: int
    guild_id: int
    channel_id: int
    message_id: int
    author_id: int


class PollCog(commands.GroupCog, name="poll"):
    def __init__(self, bot: "MyBot") -> None:
        self.db = "bot.db"
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS poll (
                    poll_id     INTEGER  PRIMARY KEY  AUTOINCREMENT,
                    guild_id    INTEGER,
                    channel_id  INTEGER,
                    message_id  INTEGER,
                    author_id   INTEGER,
                    UNIQUE (guild_id, channel_id, message_id) ON CONFLICT IGNORE
                );
                """
            )
        self.bot = bot
        super().__init__()

    def db_create_poll(self, guild_id: int, channel_id: int, message_id: int, author_id: int) -> int:
        with sqlite3.connect(self.db) as connection:
            poll_id = connection.execute(
                "INSERT INTO poll (guild_id, channel_id, message_id, author_id) VALUES (?, ?, ?, ?)",
                (guild_id, channel_id, message_id, author_id),
            ).lastrowid
            return poll_id

    def get_db_poll(self, payload: discord.RawReactionActionEvent):
        with sqlite3.connect(self.db) as connection:
            res = connection.execute(
                "SELECT * FROM poll WHERE guild_id = ? AND channel_id = ? AND message_id = ?",
                (payload.guild_id, payload.channel_id, payload.message_id),
            ).fetchone()

        return None if not res else Poll(*res)

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
        if not interaction.guild:
            return interaction.response.send_message("this command can only be used in guilds")
        options = [option1, option2, option3, option4, option5, option6, option7, option8, option9, option10]
        options: list[str] = [o for o in options if o is not None]
        options: list[Option] = [
            Option(text=f"{o}\n\t- {get_bar(0, 0)}", emote=lookup(f"REGIONAL INDICATOR SYMBOL LETTER {chr(i+97)}")) for i, o in enumerate(options)
        ]

        embed = discord.Embed(title=question, description="\n".join(option.as_list_item() for option in options))

        await interaction.response.send_message(embed=embed)
        m = await interaction.original_response()
        self.db_create_poll(m.guild.id, m.channel.id, m.id, interaction.user.id)
        for option in options:
            await m.add_reaction(option.emote)
        await m.add_reaction("❌")

    @commands.Cog.listener("on_raw_reaction_add")
    @commands.Cog.listener("on_raw_reaction_remove")
    async def vote_add_listener(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        if payload.emoji.name not in [lookup(f"REGIONAL INDICATOR SYMBOL LETTER {chr(i+97)}") for i in range(10)] + ["❌"]:
            return

        if not (poll := self.get_db_poll(payload)):
            return

        channel = self.bot.get_channel(payload.channel_id) or await self.bot.fetch_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        if payload.emoji.name == "❌" and payload.event_type == "REACTION_ADD":
            if poll.author_id != payload.user_id:
                return

            await channel.get_partial_message(payload.message_id).clear_reactions()
            with sqlite3.connect(self.db) as connection:
                connection.execute("DELETE FROM poll WHERE poll_id = ?", (poll.poll_id,))
            return

        message = await channel.fetch_message(payload.message_id)
        if not isinstance(message, discord.Message):
            return

        current_embed = next(iter(message.embeds), None)
        if not isinstance(current_embed, discord.Embed):
            return

        total_votes = sum(r.count - 1 for r in message.reactions if r.emoji in re.findall(r"- (.+?):", current_embed.description))

        options = [
            Option(emote=o[0], text=f"{o[1]}\n\t- {get_bar([r.count-1 for r in message.reactions if r.emoji==o[0]][0], total_votes)}")
            for o in re.findall(r"- (.+?): (.+?)\n", current_embed.description)
        ]
        embed = discord.Embed(title=current_embed.title, description="\n".join(option.as_list_item() for option in options))
        await message.edit(embed=embed)
