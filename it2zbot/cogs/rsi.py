from dataclasses import dataclass

import bs4
import discord
import httpx
from discord import app_commands
from discord.ext import commands


@dataclass
class System:
    title: str
    status: str


@dataclass
class ServerStatus:
    status: str
    systems: list[System]
    title: str
    thumbnail: str
    description: str
    color: int


class RSICog(commands.GroupCog, name="rsi"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.url = "https://status.robertsspaceindustries.com/"
        self.colors = {
            "under-maintenance": 0x6A737D,
            "degraded-performance": 0x6F42C1,
            "partial-outage": 0xF66A0A,
            "major-outage": 0xD73A49,
            "operational": 0x28A745,
        }
        super().__init__()

    async def crawl_rsi_status(self):
        async with httpx.AsyncClient() as client:
            res = await client.get(self.url)

        soup = bs4.BeautifulSoup(res.text, "html.parser")
        container = soup.select_one('div[class~="systems-container"]')
        _systems = container.select('div[class~="system"]')
        status = soup.select_one('div[class~="global-status"]>span:first-child').text.strip()
        thumb = soup.select_one('meta[name="og:image"]').attrs["content"]
        title = soup.select_one("title").text.strip()
        desc = soup.select_one('meta[name="description"]').attrs["content"]
        systems = []
        clr = (  # lol
            self.colors[(c := next(iter(set(soup.select_one('div[class~="global-status"]').attrs.get("class")) & set(self.colors.keys())), None))] if c else 0x0
        )  # lmao

        for system in _systems:
            s_title = system.select_one('div[class~="system-title"]').text.strip()
            s_status = system.select_one('div[class~="system-status"]>span').text.strip()
            systems.append(System(s_title, s_status))

        return ServerStatus(status, systems, title, thumb, desc, clr)

    @app_commands.command(name="server_status")
    async def set_custom_color_command(self, interaction: discord.Interaction):
        """query the RSI server status"""
        server_status = await self.crawl_rsi_status()

        embed = discord.Embed(title=server_status.title, url=self.url, description=server_status.description, color=server_status.color)
        embed.set_thumbnail(url=server_status.thumbnail)
        embed.add_field(name="Global", value=server_status.status, inline=False)
        for system in server_status.systems:
            embed.add_field(name=system.title, value=system.status, inline=False)

        await interaction.response.send_message(embed=embed)
