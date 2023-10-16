import math
import sqlite3
from typing import TYPE_CHECKING, Optional

import feedparser
import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class RssCog(commands.GroupCog, name="rss"):
    def __init__(self, bot: "MyBot") -> None:
        self.db = "bot.db"
        with sqlite3.connect(self.db) as connection:
            connection.execute("PRAGMA foreign_keys = ON;")
            # TODO: table for receivers of a feed. type of guild channel or user dm. read feed once and distribute in case of multiple channels subbing to the same feed
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rss_feed (
                    id       INTEGER  PRIMARY KEY  AUTOINCREMENT,
                    url      TEXT     NOT NULL     UNIQUE,
                );
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rss_entry (
                    id        TEXT     PRIMARY KEY,
                    rss_feed  INTEGER  NOT NULL,
                    FOREIGN KEY (rss_feed) REFERENCES rss_feed(id) ON DELETE CASCADE
                );
                """
            )
        self.bot = bot
        super().__init__()

    @app_commands.command(name="subscribe")
    async def subscribe_cmd(self, interaction: discord.Interaction, feed: str, channel: Optional[discord.TextChannel]):
        d = feedparser.parse(feed)
        if d.bozo:
            return await interaction.response.send_message("invalid feed")

        with sqlite3.connect("db.sqlite") as con:
            if con.execute(f"SELECT * FROM rss_feed f WHERE f.url = '{feed}'").fetchall():
                # TODO: if feed exists it may need to be distributed to another subscriber
                return
            con.execute(f"INSERT OR IGNORE INTO rss_feed (url) VALUES ('{feed}')")
            feed_id = con.execute(f"SELECT id FROM rss_feed WHERE url = '{feed}'").fetchone()[0]
            values = [f"('{entry.id}', '{feed_id}')" for entry in d.entries]
            con.execute(f"INSERT OR IGNORE INTO entry VALUES {','.join(values)}")
