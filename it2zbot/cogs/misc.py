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
    async def joke_command(
        self,
        interaction: discord.Interaction,
        category: Literal["Any", "Misc", "Programming", "Dark", "Pun", "Spooky", "Christmas"],
    ):
        """get a random joke"""
        async with httpx.AsyncClient() as httpx_client:
            res: dict = (await httpx_client.get(f"https://v2.jokeapi.dev/joke/{category}?blacklistFlags=racist,sexist,political")).json()

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

    @app_commands.command(name="shorten")
    @app_commands.describe(url="the big url to shorten", slug="the slug in 'https://eule.wtf/slug'")
    async def shorten_cmd(self, interaction: discord.Interaction, url: str, slug: str):
        """shorten a url with the worlds famous eule.wtf TM service"""
        async with httpx.AsyncClient() as client:
            res = await client.post("https://eule.wtf/api", json={"slug": slug, "destination": url})
        if res.status_code != 200:
            return await interaction.response.send_message(res.json()["message"])
        return await interaction.response.send_message(res.json()["url"])

    @commands.Cog.listener("on_message")
    async def preview_linked_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if (
            not message.content.count("/") == 6
            or not message.content.startswith("https://discord.com/channels/")
            or not all([id.isdigit() for id in message.content.split("/")[-3:]])
        ):
            return  # doesnt look like a discord message link

        channel_id, message_id = [id for id in message.content.split("/")[-2:]]
        linked_message = await (await self.bot.fetch_channel(channel_id)).fetch_message(message_id)
        files = [await attachment.to_file() for attachment in linked_message.attachments]

        await message.reply(linked_message.content, embeds=linked_message.embeds, files=files)

    @app_commands.command(name="avatar")
    async def avatar_cmd(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message(file=(await user.display_avatar.to_file()))
