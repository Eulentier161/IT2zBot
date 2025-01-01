from typing import TYPE_CHECKING

import discord
import httpx
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands

from it2zbot import utils
from it2zbot.translations import translate

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class Issue(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(title=translate("Issue", interaction))
        self.issue_title = discord.ui.TextInput(
            label=translate("Title", interaction),
            placeholder=translate("help, owls are too cute and awesome", interaction),
            max_length=256,
        )
        self.issue_body = discord.ui.TextInput(
            label=translate("Description", interaction),
            style=discord.TextStyle.long,
            placeholder=translate("owls are too cute, pls fix!?", interaction),
            required=False,
            max_length=4000,
        )
        self.add_item(self.issue_title)
        self.add_item(self.issue_body)

    async def on_submit(self, interaction: discord.Interaction):
        res = httpx.post(
            "https://api.github.com/repos/eulentier161/it2zbot/issues",
            headers={"Authorization": f"Bearer {utils.get_access_token()}"},
            json={
                "title": self.issue_title.value,
                "body": self.issue_body.value + "\n\n" + interaction.user.name + f" ({interaction.user.id})",
            },
        ).json()
        await interaction.response.send_message(
            f"{translate('Thanks for your feedback!', interaction)} {res['html_url']}", ephemeral=False
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(translate("Oops! Something went wrong.", interaction), ephemeral=True)


class GithubCog(commands.GroupCog, name="github"):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="repo", description=locale_str("code where?!"))
    async def repo(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://git.eule.wtf/Eulentier161/IT2zBot")

    @app_commands.command(
        name=locale_str("issue"), description=locale_str("create an issue for this project on github")
    )
    async def issue(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Issue(interaction=interaction))
