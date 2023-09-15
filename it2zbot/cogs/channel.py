from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class ChannelCog(commands.GroupCog, name="channel"):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="set_topic")
    @app_commands.describe(topic="the new topic", channel="Guild Channel to target. Defaults to current channel.")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def set_topic(self, interaction: discord.Interaction, topic: str, channel: Optional[discord.TextChannel] = None):
        """set a new channel topic"""
        channel = channel or interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("failure", ephemeral=True)
        await channel.edit(topic=topic)
        await interaction.response.send_message("success", ephemeral=True)

    @app_commands.command(name="get_topic")
    @app_commands.describe(channel="Guild Channel to target. Defaults to current channel.")
    async def get_topic(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """get a channel topic"""
        channel = channel or interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("failure", ephemeral=True)
        await interaction.response.send_message(channel.topic)
