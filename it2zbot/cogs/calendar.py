from datetime import datetime
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from httpx import TimeoutException

from it2zbot.icsparser import CalendarParser

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class CalendarCog(commands.GroupCog, name="calendar"):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        self.userid = self.bot.config["userid"]
        self.authtoken = self.bot.config["authtoken"]
        super().__init__()

    @app_commands.command(name="view")
    async def view(self, interaction: discord.Interaction):
        """calendar view"""
        try:
            await interaction.response.defer()
            try:
                events = CalendarParser(self.userid, self.authtoken).get_events()
            except TimeoutException:
                return await interaction.followup.send("moodle timeout")

            embeds = [
                discord.Embed(
                    title=event["summary"],
                    description=f'{event["description"]}\n<t:{event["dtstart"]}:R> - <t:{event["dtend"]}:R>',
                    timestamp=datetime.fromtimestamp(event["dtstart"]),
                )
                for event in events
            ]

            class PreviousButton(discord.ui.Button):
                def __init__(self):
                    super().__init__(label="⬅️", style=discord.ButtonStyle.gray, disabled=True)

                async def callback(self, interaction: discord.Interaction):
                    view: ListView = self.view
                    page = view.handle_prev_button()
                    await interaction.response.edit_message(embed=embeds[page - 1], view=view)

            class NextButton(discord.ui.Button):
                def __init__(self, disabled):
                    super().__init__(label="➡️", style=discord.ButtonStyle.gray, disabled=disabled)

                async def callback(self, interaction: discord.Interaction):
                    view: ListView = self.view
                    page = view.handle_next_button()
                    await interaction.response.edit_message(embed=embeds[page - 1], view=view)

            class ListView(discord.ui.View):
                def __init__(self, last_page):
                    super().__init__()
                    self.page = 1
                    self.last_page = last_page
                    self.prev_button = PreviousButton()
                    self.next_button = NextButton(disabled=last_page <= 1)
                    self.add_item(self.prev_button)
                    self.add_item(self.next_button)

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

            await interaction.followup.send(embed=embeds[0], view=ListView(len(embeds))) if len(embeds) else await interaction.followup.send("None")
        except Exception:
            await interaction.followup.send("something went wrong", ephemeral=True)
