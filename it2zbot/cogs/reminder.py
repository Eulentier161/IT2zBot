import sqlite3
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands, tasks

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class ReminderCog(commands.Cog):
    def __init__(self, bot: "MyBot") -> None:
        with sqlite3.connect("bot.db") as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reminder (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user VARCHAR(25),
                    channel VARCHAR(25),
                    time DATETIME,
                    message VARCHAR(1000),
                    og_message_url VARCHAR(100)
                );"""
            )
        self.bot = bot
        self.remind_exceeded.start()

    @app_commands.command(name="remind")
    @app_commands.describe(
        who="who should be mentioned?",
        amount="how long from now?",
        unit="how long from now?",
        message="a message to be reminded of",
    )
    async def remind_me_command(
        self,
        interaction: discord.Interaction,
        who: discord.User,
        amount: app_commands.Range[int, 1, 365],
        unit: Literal["Minutes", "Hours", "Days"],
        message: app_commands.Range[str, 1, 1000],
    ):
        """create a reminder"""
        channel_id, user_id = str(interaction.channel_id), str(who.id)
        if unit == "Minutes":
            delta = timedelta(minutes=amount)
        elif unit == "Hours":
            delta = timedelta(hours=amount)
        elif unit == "Days":
            delta = timedelta(days=amount)

        date = datetime.now() + delta
        date = date.strftime("%Y-%m-%d %H:%M:%S")
        name = "you" if interaction.user == who else who.display_name
        await interaction.response.send_message(f"I'll remind {name} here in {amount} {unit}")
        jump_url = (await interaction.original_response()).jump_url
        with sqlite3.connect("bot.db") as connection:
            connection.execute(
                f"""
                INSERT INTO reminder (
                    user, channel, time, message, og_message_url
                ) VALUES (
                    '{user_id}', '{channel_id}', '{date}', '{message}', '{jump_url}'
                )"""
            )

    @tasks.loop(minutes=1)
    async def remind_exceeded(self):
        with sqlite3.connect("bot.db") as connection:
            for id, time in connection.execute("SELECT id, time FROM reminder;").fetchall():
                if datetime.strptime(time, "%Y-%m-%d %H:%M:%S") > datetime.now():
                    continue  # stored date is in the future
                user_id, channel_id, message, og_message_url = connection.execute(
                    f"SELECT user, channel, message, og_message_url FROM reminder WHERE id = {id};"
                ).fetchone()
                user = await self.bot.fetch_user(int(user_id))
                channel = await self.bot.fetch_channel(int(channel_id))
                embed = discord.Embed(title="Reminder!", description=message, url=og_message_url)
                await channel.send(content=user.mention, embed=embed)
                connection.execute(f"DELETE FROM reminder WHERE id = {id};")

    @remind_exceeded.before_loop
    async def before_remind_exceeded(self):
        await self.bot.wait_until_ready()
