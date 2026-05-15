import sqlite3
from typing import TYPE_CHECKING
from functools import wraps

import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import locale_str
from it2zbot.translations import translate

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class EconomyCog(commands.GroupCog, name=locale_str("economy")):
    def __init__(self, bot: "MyBot") -> None:
        with sqlite3.connect("bot.db") as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS economy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user VARCHAR(25),
                    wealth INTEGER
                );""")
        self.bot = bot
        super().__init__()

    def create_user_if_not_exists(func):
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            with sqlite3.connect("bot.db") as connection:
                cursor = connection.execute("SELECT id FROM economy WHERE user = ?", (str(interaction.user.id),))
                if cursor.fetchone() is None:
                    connection.execute(
                        "INSERT INTO economy (user, wealth) VALUES (?, ?)", (str(interaction.user.id), 0)
                    )
            return await func(self, interaction, *args, **kwargs)

        return wrapper

    @app_commands.command(name=locale_str("hourly"))
    @app_commands.checks.cooldown(1, 3600)
    @create_user_if_not_exists
    async def economy_hourly_cmd(self, interaction: discord.Interaction):
        with sqlite3.connect("bot.db") as connection:
            cursor = connection.execute("SELECT wealth FROM economy WHERE user = ?", (str(interaction.user.id),))
            wealth = cursor.fetchone()[0]
            new_wealth = wealth + 100
            connection.execute("UPDATE economy SET wealth = ? WHERE user = ?", (new_wealth, str(interaction.user.id)))

        await interaction.response.send_message(
            translate("economy_hourly_success", interaction).format(amount=100, total=new_wealth),
            ephemeral=True,
        )

    @economy_hourly_cmd.error
    async def economy_hourly_cmd_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                translate("economy_hourly_on_cooldown", interaction).format(seconds=error.retry_after),
                ephemeral=True,
            )
