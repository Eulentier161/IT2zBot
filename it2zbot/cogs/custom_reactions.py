import math
import sqlite3
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands

from it2zbot.translations import translate

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class CustomReactionsCog(commands.GroupCog, name=locale_str("custom_reactions")):
    def __init__(self, bot: "MyBot") -> None:
        with sqlite3.connect("bot.db") as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS custom_reaction (
                    id       INTEGER       PRIMARY KEY AUTOINCREMENT,
                    author   VARCHAR(25),
                    trigger  VARCHAR(100)  UNIQUE,
                    response VARCHAR(2000)
                );
                """
            )
        self.bot = bot
        self.admins = bot.config["admins"]
        super().__init__()

    @commands.Cog.listener("on_message")
    async def trigger_custom_reaction(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        with sqlite3.connect("bot.db") as connection:
            try:
                if res := connection.execute(
                    f"SELECT response FROM custom_reaction WHERE trigger = ?;", (message.content,)
                ).fetchone():
                    await message.reply(res[0], mention_author=False)
            except sqlite3.OperationalError:
                pass

    @app_commands.command(name=locale_str("create"), description=locale_str("create a new custom reaction"))
    @app_commands.describe(
        trigger=locale_str("text that triggers this custom reaction"),
        response=locale_str("response for this custom reaction"),
    )
    @app_commands.rename(trigger=locale_str("trigger"), response=locale_str("response"))
    async def create_custom_reaction(
        self,
        interaction: discord.Interaction,
        trigger: app_commands.Range[str, 1, 100],
        response: app_commands.Range[str, 1, 2000],
    ):
        try:
            with sqlite3.connect("bot.db") as connection:
                connection.execute(
                    f"""
                    INSERT INTO custom_reaction (author, trigger, response)
                    VALUES (?, ?, ?);
                    """,
                    (interaction.user.id, trigger, response),
                )
            await interaction.response.send_message(f"{translate('I will respond to', interaction)} `{trigger}`")
        except sqlite3.IntegrityError:
            await interaction.response.send_message(
                translate("there is already a custom reaction with this trigger", interaction), ephemeral=True
            )

    @app_commands.command(name=locale_str("list"), description=locale_str("list all custom reactions"))
    async def list_custom_reactions(self, interaction: discord.Interaction):
        def select(connection: sqlite3.Connection, page: int) -> list[dict]:
            return [
                {"id": row[0], "trigger": row[1]}
                for row in connection.execute(
                    f"SELECT id, trigger FROM custom_reaction ORDER BY id LIMIT ?, 10;", ((page - 1) * 10,)
                ).fetchall()
            ]

        class PreviousButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="⬅️", style=discord.ButtonStyle.gray, disabled=True)

            async def callback(self, interaction: discord.Interaction):
                view: ListView = self.view
                page = view.handle_prev_button()
                with sqlite3.connect("bot.db") as connection:
                    custom_reactions = select(connection, page=page)
                embed = discord.Embed(
                    title=translate("Custom Reactions", interaction),
                    description="\n".join(
                        [f"{reaction['id']}. **{reaction['trigger']}**" for reaction in custom_reactions]
                    ),
                )
                embed.set_footer(text=f"{translate('page', interaction)} {view.page}/{view.last_page}")
                await interaction.response.edit_message(embed=embed, view=view)

        class NextButton(discord.ui.Button):
            def __init__(self, disabled):
                super().__init__(label="➡️", style=discord.ButtonStyle.gray, disabled=disabled)

            async def callback(self, interaction: discord.Interaction):
                view: ListView = self.view
                page = view.handle_next_button()
                with sqlite3.connect("bot.db") as connection:
                    custom_reactions = select(connection, page=page)
                embed = discord.Embed(
                    title=translate("Custom Reactions", interaction),
                    description="\n".join(
                        [f"{reaction['id']}. **{reaction['trigger']}**" for reaction in custom_reactions]
                    ),
                )
                embed.set_footer(text=f"{translate('page', interaction)} {view.page}/{view.last_page}")
                await interaction.response.edit_message(embed=embed, view=view)

        class ListView(discord.ui.View):
            def __init__(self, last_page: int):
                super().__init__()
                self.page = 1
                self.last_page = last_page
                self.prev_button = PreviousButton()
                self.next_button = NextButton(disabled=last_page <= 1)
                self.add_item(self.prev_button)
                self.add_item(self.next_button)

            def handle_button_disabled(self):
                self.next_button.disabled = self.page >= self.last_page
                self.prev_button.disabled = self.page <= 1

            def handle_next_button(self):
                self.page += 1
                self.handle_button_disabled()
                return self.page

            def handle_prev_button(self):
                self.page -= 1
                self.handle_button_disabled()
                return self.page

        # TODO: this will break if the response body reaches discords message length limit. custom reactions would need to be limited.
        with sqlite3.connect("bot.db") as connection:
            last_page = max(
                1, math.ceil(connection.execute("SELECT COUNT(*) FROM custom_reaction;").fetchone()[0] / 10)
            )
            custom_reactions = select(connection, page=1)
        embed = discord.Embed(
            title=translate("Custom Reactions", interaction),
            description="\n".join([f"{reaction['id']}. **{reaction['trigger']}**" for reaction in custom_reactions]),
        )
        embed.set_footer(text=f"{translate('page', interaction)} 1/{last_page}")
        await interaction.response.send_message(embed=embed, view=ListView(last_page), ephemeral=True)

    @app_commands.command(name=locale_str("delete"), description=locale_str("delete a custom reaction"))
    async def delete_custom_reactions(self, interaction: discord.Interaction, trigger: str):
        with sqlite3.connect("bot.db") as connection:
            if not (
                res := connection.execute(
                    f"SELECT id, author FROM custom_reaction WHERE trigger = ?;", (trigger,)
                ).fetchone()
            ):
                return await interaction.response.send_message(
                    f"{translate('there is no custom reaction with', interaction)} `{trigger=}`", ephemeral=True
                )
            if not interaction.user.id == int(res[1]) and interaction.user.id not in self.admins:
                return await interaction.response.send_message(
                    translate(
                        "you can't delete this reaction. only a bot-admin or the user who created this reaction may delete it",
                        interaction,
                    ),
                    ephemeral=True,
                )
            connection.execute(f"DELETE FROM custom_reaction WHERE id = ?;", (res[0],))
        await interaction.response.send_message(f"{translate('i will stop responding to', interaction)} `{trigger}`")
