from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord
import httpx
import re
from urllib.parse import urlparse
from pydantic import BaseModel
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


class GithubCog(commands.GroupCog, name=locale_str("github")):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name=locale_str("source"), description=locale_str("code where?!"))
    async def repo(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://git.eule.wtf/Eulentier161/IT2zBot")

    @app_commands.command(
        name=locale_str("issue"), description=locale_str("create an issue for this project on github")
    )
    async def issue(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Issue(interaction=interaction))

    @commands.Cog.listener("on_message")
    async def respond_to_gist_link(self, message: discord.Message):
        if message.author.bot or message.author == self.bot.user:
            return

        gist_ids = re.findall(r"https://gist\.github\.com/\w+/(\w+)", message.content, re.MULTILINE)
        if len(gist_ids) == 0:
            return

        class GistOwner(BaseModel):
            login: str

        class GistFile(BaseModel):
            filename: str
            content: str
            size: int

        class GistData(BaseModel):
            files: dict[str, GistFile]
            owner: GistOwner
            html_url: str
            description: str

        def build_gist_embeds(gist_data: GistData) -> list[discord.Embed]:
            MAX_CHARS_EMBEDS = 6000
            MAX_CHARS_EMBED_DESCRIPTION = 4096

            embeds: list[discord.Embed] = []
            for filename in list(gist_data.files.keys())[:10]:
                file = gist_data.files[filename]
                MAX_EMBED_CHARS_BY_CNT_EMBEDS = MAX_CHARS_EMBEDS // min(10, len(gist_data.files))
                cnt_lost_chars_from_wrapper = len(f"```{filename.split('.')[-1]}\n\n```")
                max_description_length = min(
                    MAX_CHARS_EMBED_DESCRIPTION - cnt_lost_chars_from_wrapper, MAX_EMBED_CHARS_BY_CNT_EMBEDS
                )
                embed = discord.Embed(
                    title=file.filename,
                    description=f"```{filename.split('.')[-1]}\n{file.content[:max_description_length]}\n```",
                )
                embeds.append(embed)
            return embeds

        async with httpx.AsyncClient() as client:
            for gist_id in gist_ids:
                res = await client.get(f"https://api.github.com/gists/{gist_id}")
                if res.status_code != 200:
                    continue
                gist_data = GistData.model_validate(res.json())
                embeds = build_gist_embeds(gist_data)
                await message.reply(
                    f"# [Gist by {gist_data.owner.login}](<{gist_data.html_url}>)\n-# {gist_data.description}",
                    embeds=embeds,
                )
