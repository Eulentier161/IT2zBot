import discord
from discord import app_commands
from discord.ext import commands
import httpx
import bs4


class RSICog(commands.GroupCog, name="rsi"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.url = "https://status.robertsspaceindustries.com/"
        super().__init__()

    async def rsi_server_status(self):
        async with httpx.AsyncClient() as client:
            res = await client.get(self.url)

        soup = bs4.BeautifulSoup(res.text, "html.parser")
        container = soup.select_one('div[class~="systems-container"]')
        systems = container.select('div[class~="system"]')

        thumb = soup.select_one('meta[name="og:image"]').attrs["content"]
        title = soup.select_one("title").text
        desc = soup.select_one('meta[name="description"]').attrs["content"]
        r = []
        for system in systems:
            s_title = system.select_one('div[class~="system-title"]')
            s_status = system.select_one('div[class~="system-status"]>span')
            r.append({"title": s_title.text.strip(), "status": s_status.text.strip()})

        return {"status": r, "title": title, "description": desc, "thumbnail": thumb}

    @app_commands.command(name="server_status")
    async def set_custom_color_command(self, interaction: discord.Interaction):
        """query the RSI server status"""
        res = await self.rsi_server_status()

        embed = discord.Embed(
            title=res["title"],
            url=self.url,
            description=res["description"],
        )
        embed.set_thumbnail(url=res["thumbnail"])

        # TODO
        # rsi is using a set of colors for the status.
        # .global-status & .system-status
        # 
        # .under-maintenance: #6a737d;
        # .degraded-performance: #6f42c1;
        # .partial-outage: #f66a0a;
        # .major-outage: #d73a49;
        # .operational: #28a745;
        #
        # the global status color would be a nice fit for the embed color

        for system in res["status"]:
            embed.add_field(name=system["title"], value=system["status"], inline=False)

        await interaction.response.send_message(embed=embed)
