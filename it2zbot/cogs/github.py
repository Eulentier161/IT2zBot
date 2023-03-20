import discord
import httpx
from discord import app_commands
from discord.ext import commands

from it2zbot import utils


class Issue(discord.ui.Modal, title="Issue"):
    issue_title = discord.ui.TextInput(label="Title", placeholder="help, owls are too cute and awesome", max_length=256)
    issue_body = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.long,
        placeholder="owls are too cute, pls fix!?",
        required=False,
        max_length=4000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        res = httpx.post(
            "https://api.github.com/repos/eulentier161/it2zbot/issues",
            headers={"Authorization": f"Bearer {utils.get_access_token()}"},
            json={"title": self.issue_title.value, "body": self.issue_body.value + "\n\n" + interaction.user.name + f" ({interaction.user.id})"},
        ).json()
        await interaction.response.send_message(f"Thanks for your feedback! {res['html_url']}", ephemeral=False)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Oops! Something went wrong.", ephemeral=True)


class Github(commands.GroupCog, name="github"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="repo")
    async def repo(self, interaction: discord.Interaction):
        """code where?!"""
        await interaction.response.send_message("https://eule.wtf/it2zbot")

    @app_commands.command(name="issue")
    async def issue(self, interaction: discord.Interaction):
        """create an issue for this project on github"""
        await interaction.response.send_modal(Issue())
