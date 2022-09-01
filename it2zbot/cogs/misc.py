import sqlite3
from datetime import datetime, timedelta
from typing import Literal

import discord
import httpx
from discord import app_commands
from discord.ext import commands, tasks


class MiscCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
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
                );
                """
            )
        self.bot = bot
        self.remind_exceeded.start()

    @app_commands.command(name="joke")
    @app_commands.describe(category="joke category")
    async def joke_command(
        self,
        interaction: discord.Interaction,
        category: Literal["Any", "Misc", "Programming", "Dark", "Pun", "Spooky", "Christmas"],
    ):
        """get a random joke"""
        async with httpx.AsyncClient() as httpx_client:
            res: dict = (await httpx_client.get(f"https://v2.jokeapi.dev/joke/{category}")).json()

        if (type := res.get("type", None)) == "single":
            await interaction.response.send_message(f"{res['joke']}")
        elif type == "twopart":
            await interaction.response.send_message(f"{res['setup']}\n\n||{res['delivery']}||")
        else:
            await interaction.response.send_message(f"something went wrong ¯\\_(ツ)_/¯")

    @app_commands.command(name="button")
    async def button_command(self, interaction: discord.Interaction):
        """get a button to click :)"""

        class ClickableButton(discord.ui.View):
            @discord.ui.button(label=":(", style=discord.ButtonStyle.red)
            async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
                button.disabled = True
                button.style = discord.ButtonStyle.green
                button.label = ":)"
                await interaction.response.edit_message(content="You did press the Button!! Yay!!", view=self)

        await interaction.response.send_message(content="Press the Button!!", view=ClickableButton(), ephemeral=True)

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
        who: discord.Member,
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
                f"INSERT INTO reminder (user, channel, time, message, og_message_url) VALUES ('{user_id}', '{channel_id}', '{date}', '{message}', '{jump_url}')"
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

    @app_commands.command(name="shorten")
    @app_commands.describe(url="the big url to shorten", slug="the slug in 'https://eule.wtf/slug'")
    async def shorten_cmd(self, interaction: discord.Interaction, url: str, slug: str):
        """shorten a url with the worlds famous eule.wtf TM service"""
        async with httpx.AsyncClient() as client:
            res = await client.post("http://localhost:3002/api", json={"slug": slug, "destination": url})
        if res.status_code != 200:
            return await interaction.response.send_message(res.json()["message"])
        return await interaction.response.send_message(f"https://eule.wtf/{slug}")
