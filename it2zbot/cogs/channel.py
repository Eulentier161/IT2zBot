from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands

from it2zbot.translations import translate

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class ChannelCog(commands.GroupCog, name=locale_str("channel")):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name=locale_str("set_topic"), description=locale_str("set a new channel topic"))
    @app_commands.describe(
        topic=locale_str("the new topic"), channel=locale_str("Guild Channel to target. Defaults to current channel.")
    )
    @app_commands.rename(topic=locale_str("topic"), channel=locale_str("channel"))
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def set_topic(
        self, interaction: discord.Interaction, topic: str, channel: Optional[discord.TextChannel] = None
    ):
        channel = channel or interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(translate("failure", interaction), ephemeral=True)
        await channel.edit(topic=topic)
        await interaction.response.send_message("success", ephemeral=True)

    @app_commands.command(name=locale_str("get_topic"), description=locale_str("get a channel topic"))
    @app_commands.describe(channel=locale_str("Guild Channel to target. Defaults to current channel."))
    async def get_topic(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        channel = channel or interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(translate("failure", interaction), ephemeral=True)
        await interaction.response.send_message(channel.topic)
