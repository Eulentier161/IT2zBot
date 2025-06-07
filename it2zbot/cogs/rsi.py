import asyncio
from typing import TYPE_CHECKING

import discord
import feedparser
import httpx
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands
from markdownify import markdownify as md

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class RsiCog(commands.GroupCog, name="rsi"):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="status", description="Get the status from status.robertsspaceindustries.com")
    async def rsi_status(self, interaction: discord.Interaction) -> None:
        """Get the status from status.robertsspaceindustries.com"""
        async with httpx.AsyncClient() as client:
            responses = await asyncio.gather(
                *[
                    client.get(url)
                    for url in [
                        "https://status.robertsspaceindustries.com/index.xml",
                        "https://status.robertsspaceindustries.com",
                    ]
                ]
            )
        feed = feedparser.parse(responses[0].text)
        soup = BeautifulSoup(responses[1].text, "html.parser")

        component_statuses = {
            "operational": "#51ae7a",
            "maintenance": "#aab5bb",
            "partial": "#e8944a",
            "major": "#ff6666",
            "degraded": "#969AE8",
        }

        components = [
            {
                "name": element.find(string=True, recursive=False).strip(),
                "value": element.select_one(".component-status").text.strip(),
                "data-status": element.select_one(".component-status")["data-status"],
            }
            for element in soup.select(".components>.component")
        ]

        embeds: list[discord.Embed] = []

        try:
            latest_entry = [entry for entry in feed.entries if not entry.title.startswith("[Resolved]")][0]
        except IndexError:
            latest_entry = None

        for component in components:
            embeds.append(
                discord.Embed(
                    title=component["name"],
                    description=component["value"],
                    color=discord.Colour.from_str(component_statuses[component["data-status"]]),
                )
            )

        await interaction.response.send_message(
            content=None if not latest_entry else md(latest_entry.description), embeds=embeds
        )
