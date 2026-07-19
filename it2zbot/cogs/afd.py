import sqlite3
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from it2zbot.translations import translate

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


def get_embed(
    id: str, title: str | None, text: str | None, transcription: str | None, platform: str, url: str, name: str
) -> discord.Embed:
    embed = discord.Embed(
        colour=discord.Colour.from_rgb(150, 75, 0),
        title=title or "<Kein Titel>",
        description=text + "\n-\n" + transcription if text and transcription else text or transcription,
        url=f"https://fragdenstaat.de/aktionen/afd-datenbank/beleg/{id}/",
    )
    embed.set_author(name=name)
    embed.add_field(name="Original Beitrag", value=f"[{platform}]({url})")
    return embed


class AfdCog(commands.GroupCog, name="afd"):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="random", description="get a random verfassungswidrigen post of germans party for mentally gapped people"
    )
    async def afd_cmd(self, interaction: discord.Interaction):
        with sqlite3.connect("afd-datenbank.db") as connection:
            post = connection.execute("""
                SELECT 
                    posts.evidence_slug AS id,
                    posts.title,
                    posts.text,
                    posts.transcription,
                    posts.platform,
                    posts.url,
                    actors.name
                FROM posts
                JOIN actors ON posts.actors = actors.actor_id
                WHERE coalesce(length(text), 0) + coalesce(length(transcription), 0) < 4096 - 3
                ORDER BY random()
                LIMIT 1
            """)
            embed = get_embed(*post.fetchone())

        await interaction.response.send_message(
            embed=embed,
            ephemeral=False,
        )
