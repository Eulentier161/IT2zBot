import sqlite3

import discord
from discord import app_commands
from discord.ext import commands
from utils import get_config


class CustomReactions(commands.GroupCog, name="custom_reactions"):
    def __init__(self, bot: commands.Bot) -> None:
        with sqlite3.connect("bot.db") as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS custom_reaction (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author VARCHAR(25),
                    trigger VARCHAR(100) UNIQUE,
                    response VARCHAR(2000)
                );
                """
            )
        self.bot = bot
        self.admins = get_config()["admins"]
        super().__init__()

    @commands.Cog.listener("on_message")
    async def trigger_custom_reaction(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        with sqlite3.connect("bot.db") as connection:
            if res := connection.execute(f"SELECT response FROM custom_reaction WHERE trigger = '{message.content}';").fetchone():
                await message.reply(res[0], mention_author=False)

    @app_commands.command(name="create")
    @app_commands.describe(trigger="text that triggers this custom reaction", response="response for this custom reaction")
    async def create_custom_reaction(
        self, interaction: discord.Interaction, trigger: app_commands.Range[str, 1, 100], response: app_commands.Range[str, 1, 2000]
    ):
        """create a new custom reaction"""
        try:
            with sqlite3.connect("bot.db") as connection:
                connection.execute(
                    f"""
                    INSERT INTO custom_reaction (
                        author,
                        trigger,
                        response
                    ) VALUES (
                        '{interaction.user.id}',
                        '{trigger}',
                        '{response}'
                    );
                    """
                )
            await interaction.response.send_message(f"I will respond to {trigger}!")
        except sqlite3.IntegrityError:
            await interaction.response.send_message("there is already a custom reaction with this trigger", ephemeral=True)

    @app_commands.command(name="list")
    async def list_custom_reactions(self, interaction: discord.Interaction):
        """list all custom reactions"""
        # TODO: this will break if the response body reaches discords message length limit
        with sqlite3.connect("bot.db") as connection:
            custom_reactions = [{"id": row[0], "trigger": row[1]} for row in connection.execute("SELECT id, trigger FROM custom_reaction;").fetchall()]
        embed = discord.Embed(
            title="Custom Reactions", description="\n".join([f"{reaction['id']}. **{reaction['trigger']}**" for reaction in custom_reactions])
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delete")
    async def delete_custom_reactions(self, interaction: discord.Interaction, trigger: str):
        """delete a custom reaction"""
        with sqlite3.connect("bot.db") as connection:
            if not (res := connection.execute(f"SELECT id, author FROM custom_reaction WHERE trigger = '{trigger}';").fetchone()):
                return await interaction.response.send_message(f"there is no custom reaction with `{trigger=}`", ephemeral=True)
            if not interaction.user.id == int(res[1]) and interaction.user.id not in self.admins:
                return await interaction.response.send_message(
                    "you cant delete this reaction. only a bot-admin or the user who created this reaction may delete it", ephemeral=True
                )
            connection.execute(f"DELETE FROM custom_reaction WHERE id = {res[0]};")
        await interaction.response.send_message(f"i wont respond to {trigger} anymore")
