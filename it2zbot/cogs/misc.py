from typing import Literal
import discord
import httpx
from discord import app_commands
from discord.ext import commands


class MiscCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="joke")
    @app_commands.describe(category="joke category")
    async def joke_command(self, interaction: discord.Interaction, category: Literal["Any", "Misc", "Programming", "Dark", "Pun", "Spooky", "Christmas"]):
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
