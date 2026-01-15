from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
import discord
from discord import app_commands
from discord.ext import commands
from pydantic import BaseModel
from markdownify import markdownify as md

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class WikipediaSearchResultsPageThumbnail(BaseModel):
    mimetype: str
    width: int | None
    height: int | None
    duration: float | int | None
    url: str


class WikipediaSearchResultsPage(BaseModel):
    id: int
    key: str
    title: str
    excerpt: str | None
    matched_title: str | None
    description: str | None
    thumbnail: WikipediaSearchResultsPageThumbnail | None


class WikipediaSearchResults(BaseModel):
    pages: list[WikipediaSearchResultsPage]


def embed_from_wikipedia_search_results_page(page: WikipediaSearchResultsPage) -> discord.Embed:
    embed = discord.Embed(
        title=page.title,
        url=f"https://de.wikipedia.org/wiki/{page.key}",
        description=(
            md(page.excerpt).strip() + f"... [weiter lesen](https://de.wikipedia.org/wiki/{page.key})"
            if page.excerpt
            else "Keine Vorschau verfügbar."
        ),
    )
    if page.thumbnail:
        embed.set_thumbnail(url=urlparse(page.thumbnail.url)._replace(scheme="https").geturl())
    embed.set_footer(
        text=page.description or "Keine Beschreibung verfügbar.",
        icon_url="https://de.wikipedia.org/static/images/icons/wikipedia.png",
    )
    return embed


class WikipediaCog(commands.GroupCog, name="wikipedia"):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="search", description="search a wikipedia article")
    async def search(self, interaction: discord.Interaction, query: str):
        class PreviousButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="⬅️", style=discord.ButtonStyle.gray, disabled=True)

            async def callback(self, interaction: discord.Interaction):
                view: ListView = self.view
                page = view.handle_prev_button()
                await interaction.response.edit_message(embed=view.embeds[page - 1], view=view)

        class NextButton(discord.ui.Button):
            def __init__(self, disabled):
                super().__init__(label="➡️", style=discord.ButtonStyle.gray, disabled=disabled)

            async def callback(self, interaction: discord.Interaction):
                view: ListView = self.view
                page = view.handle_next_button()
                await interaction.response.edit_message(embed=view.embeds[page - 1], view=view)

        class ListView(discord.ui.View):
            def __init__(self, embeds: list[discord.Embed]):
                super().__init__()
                self.page = 1
                self.embeds = embeds
                self.last_page = len(embeds)
                self.prev_button = PreviousButton()
                self.next_button = NextButton(disabled=self.last_page <= 1)
                self.add_item(self.prev_button)
                self.add_item(self.next_button)
                self.message: discord.Message | None = None

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

            async def on_timeout(self):
                if self.message:
                    await self.message.edit(view=None)

        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://de.wikipedia.org/w/rest.php/v1/search/page",
                params={"q": query},
                headers={
                    "Accept": "application/json",
                    "User-Agent": "it2zbot/0.1.0 (https://github.com/eulentier161/it2zbot;it2zbot@eule.wtf)",
                },
            )
        search_results = WikipediaSearchResults.model_validate(res.json())
        embeds = list(map(embed_from_wikipedia_search_results_page, search_results.pages))

        if embeds:
            view = ListView(embeds)
            await interaction.response.send_message(embed=embeds[0], view=view)
            view.message = await interaction.original_response()
        else:
            await interaction.response.send_message("Keine Ergebnisse gefunden.")
