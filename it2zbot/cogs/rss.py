import sqlite3
from datetime import datetime
from time import mktime
from typing import TYPE_CHECKING, Optional

import discord
import feedparser
from discord import app_commands
from discord.ext import commands, tasks
from markdownify import markdownify as md

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class RssCog(commands.GroupCog, name="rss"):
    def __init__(self, bot: "MyBot") -> None:
        self.db = "bot.db"
        self.bot = bot
        with sqlite3.connect(self.db) as connection:
            # connection.execute("DROP TABLE IF EXISTS rss_entry")
            # connection.execute("DROP TABLE IF EXISTS rss_feed_subscription")
            # connection.execute("DROP TABLE IF EXISTS rss_feed")
            # connection.execute("DROP TABLE IF EXISTS subscription")

            connection.execute("PRAGMA foreign_keys = ON;")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS subscription (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL
                );
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rss_feed (
                    id       INTEGER  PRIMARY KEY  AUTOINCREMENT,
                    url      TEXT     NOT NULL     UNIQUE
                );
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rss_feed_subscription (
                    subscription_id INTEGER NOT NULL,
                    rss_feed_id INTEGER NOT NULL,
                    FOREIGN KEY (subscription_id) REFERENCES subscription(id) ON DELETE CASCADE,
                    FOREIGN KEY (rss_feed_id) REFERENCES rss_feed(id) ON DELETE CASCADE
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
        self.rss_publisher.start()
        super().__init__()

    def cog_unload(self):
        self.rss_publisher.cancel()

    @app_commands.command(name="subscribe")
    async def subscribe_cmd(self, interaction: discord.Interaction, feed: str, channel: Optional[discord.TextChannel]):
        await interaction.response.defer()
        d = feedparser.parse(feed)

        # validate feed
        if d.bozo:
            return await interaction.followup.send("invalid feed")

        # use user dms if no channel
        # TODO: split this in its own command
        if not channel:
            channel = interaction.user.dm_channel or await interaction.user.create_dm()
        else:
            if not interaction.user.guild_permissions.manage_channels:
                return await interaction.followup.send(
                    "adding a feed to a guild channel requires the `manage_channels` permission.\n"
                    "you can still subscribe to feeds without specifying a channel to receive the feed in dms."
                )

        # validate feed+channel not already set
        with sqlite3.connect(self.db) as con:
            r = con.execute(
                f"""
                SELECT * FROM rss_feed_subscription rfs 
                JOIN rss_feed rf ON rfs.rss_feed_id = rf.id 
                JOIN subscription s ON rfs.subscription_id = s.id 
                WHERE rf.url = '{feed}' AND s.channel_id = '{channel.id}'
                """
            ).fetchall()
            if r:
                return await interaction.followup.send(f"already subbed")

        channel: discord.TextChannel | discord.DMChannel

        with sqlite3.connect(self.db) as con:
            cursor = con.cursor()
            r = cursor.execute(f"SELECT id FROM rss_feed WHERE url = '{feed}'").fetchone()
            if r:
                feed_id = r[0]
            else:
                cursor.execute(f"INSERT OR IGNORE INTO rss_feed (url) VALUES ('{feed}')")
                feed_id = cursor.lastrowid
                values = [f"('{entry.id}', '{feed_id}')" for entry in d.entries]
                cursor.execute(f"INSERT OR IGNORE INTO rss_entry VALUES {','.join(values)}")
            cursor.execute(f"INSERT INTO subscription (channel_id) VALUES ('{channel.id}');")
            subscription_id = cursor.lastrowid
            cursor.execute(f"INSERT INTO rss_feed_subscription VALUES ('{subscription_id}', '{feed_id}')")

        await channel.send(f"this channel is now tracking {feed}")
        await interaction.followup.send("✔")

    @tasks.loop(minutes=10)  # TODO: reduce this!!
    async def rss_publisher(self):
        with sqlite3.connect(self.db) as con:
            feeds = con.execute("SELECT * FROM rss_feed").fetchall()
            for feed_id, feed_url in feeds:
                d = feedparser.parse(feed_url)
                known = [r[0] for r in con.execute(f"SELECT id FROM rss_entry WHERE rss_feed = '{feed_id}'")]
                for entry in d.entries:
                    if entry.id in known:
                        continue
                    channel_ids = [
                        r[0]
                        for r in con.execute(
                            f"SELECT s.channel_id FROM rss_feed_subscription rfs JOIN subscription s ON rfs.subscription_id = s.id WHERE rfs.rss_feed_id = '{feed_id}'"
                        )
                    ]
                    for channel_id in channel_ids:
                        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)

                        # https://stackoverflow.com/a/1697907
                        timestamp = entry.get("updated_parsed", None)
                        if timestamp:
                            timestamp = datetime.fromtimestamp(mktime(timestamp))

                        embed = (
                            discord.Embed(
                                title=md(entry.get("title", "Untitled"), convert=[]),
                                description=md(entry.get("summary", "No description available")),
                                url=entry.get("link", None),
                                timestamp=timestamp,
                            )
                            .set_thumbnail(url=d.feed.get("image", {}).get("href", self.bot.user.display_avatar.url))
                            .set_footer(text=feed_url)
                        )
                        if author := entry.get("author_detail", None):
                            embed.set_author(name=author.get("name"), url=author.get("href", None))

                        await channel.send(embed=embed)
                    con.execute(f"INSERT INTO rss_entry VALUES ('{entry.id}', '{feed_id}')")

    @rss_publisher.before_loop
    async def before_rss_publisher(self):
        await self.bot.wait_until_ready()
