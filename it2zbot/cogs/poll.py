import sqlite3
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


class PollCog(commands.GroupCog, name="poll"):
    def __init__(self, bot: "MyBot") -> None:
        self.db = "bot.db"
        with sqlite3.connect(self.db) as connection:
            connection.execute("DROP TABLE IF EXISTS poll;")
            connection.execute("DROP TABLE IF EXISTS poll_option;")
            connection.execute("DROP TABLE IF EXISTS poll_option_vote;")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS poll (
                    poll_id     INTEGER  PRIMARY KEY  AUTOINCREMENT,
                    question    TEXT     NOT NULL,
                    is_open     BOOLEAN  NOT NULL  DEFAULT 1  CHECK (is_open IN (0, 1)),
                    guild_id    INTEGER,
                    channel_id  INTEGER,
                    message_id  INTEGER
                );
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS poll_option (
                    option_id   INTEGER  PRIMARY KEY  AUTOINCREMENT,
                    poll_id     INTEGER  NOT NULL,
                    value       TEXT NOT NULL,
                    symbol      TEXT NOT NULL,
                    FOREIGN KEY (poll_id) REFERENCES poll(poll_id) ON DELETE CASCADE
                );
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS poll_option_vote (
                    vote_id    INTEGER  PRIMARY KEY  AUTOINCREMENT,
                    option_id  INTEGER  NOT NULL,
                    user_id    INTEGER  NOT NULL,
                    UNIQUE (option_id, user_id) ON CONFLICT IGNORE,
                    FOREIGN KEY (option_id) REFERENCES poll_option(option_id) ON DELETE CASCADE
                );
                """
            )
        self.bot = bot
        super().__init__()

    def db_create_poll(self, question: str, guild_id: int, channel_id: int, message_id: int, options: list[Option]):
        with sqlite3.connect(self.db) as connection:
            poll_id = connection.execute(
                "INSERT INTO poll (question, guild_id, channel_id, message_id) VALUES (?, ?, ?, ?)", (question, guild_id, channel_id, message_id)
            ).lastrowid
            connection.executemany(
                "INSERT INTO poll_option (poll_id, value, symbol) VALUES (?, ?, ?)", [(poll_id, option.text, option.emote) for option in options]
            )
            return poll_id

    def get_option_id(self, payload: discord.RawReactionActionEvent) -> int | None:
        with sqlite3.connect(self.db) as connection:
            option_id = connection.execute(
                """
                SELECT option_id 
                FROM poll_option po 
                JOIN poll p ON po.poll_id = p.poll_id
                WHERE p.guild_id = ?
                AND p.channel_id = ?
                AND p.message_id = ?
                AND po.symbol = ?
                """,
                (payload.guild_id, payload.channel_id, payload.message_id, payload.emoji.name),
            ).fetchone()
        if not option_id:
            return None
        else:
            return option_id[0]

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
        poll_id = self.db_create_poll(question, m.guild.id, m.channel.id, m.id, options)
        embed.set_footer(text=f"poll id: {poll_id}")
        await m.edit(embed=embed)
        for option in options:
            await m.add_reaction(option.emote)

    @commands.Cog.listener("on_raw_reaction_add")
    async def vote_add_listener(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        option_id = self.get_option_id(payload)
        if not option_id:
            return

        with sqlite3.connect(self.db) as connection:
            connection.execute("INSERT INTO poll_option_vote (option_id, user_id) VALUES (?, ?)", (option_id, payload.user_id))

    @commands.Cog.listener("on_raw_reaction_remove")
    async def vote_remove_listener(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        option_id = self.get_option_id(payload)
        if not option_id:
            return

        with sqlite3.connect(self.db) as connection:
            connection.execute("DELETE FROM poll_option_vote WHERE option_id = ? AND user_id = ?", (option_id, payload.user_id))
