from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands

@app_commands.guild_only()
class SelfManagement(commands.GroupCog, name="self_management"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="set_custom_color")
    async def set_custom_color_command(self, interaction: discord.Interaction, color: str):
        """assign a custom color-role to yourself or change your color"""
        try:
            color = discord.Colour.from_str(color)
        except ValueError:
            return await interaction.response.send_message(
                "\n".join(
                    [
                        "color must be in one of the following format",
                        "- `0x<hex>`",
                        "- `#<hex>`",
                        "- `0x#<hex>`",
                        "- `rgb(<number>, <number>, <number>)`",
                        "Like CSS, `<number>` can be either 0-255 or 0-100% and `<hex>` can be either a 6 digit hex number or a 3 digit hex shortcut (e.g. #fff).",
                    ]
                ),
                ephemeral=True,
            )
        uid = str(interaction.user.id)
        existing_roles = await interaction.guild.fetch_roles()
        if uid in [role.name for role in existing_roles]:
            for role in existing_roles:
                if role.name != uid:
                    continue
                role = await role.edit(colour=color, reason="color role")
                break
        else:
            role = await interaction.guild.create_role(name=uid, colour=color, reason="color role")
            await interaction.user.add_roles(role)
        await interaction.response.send_message(role.mention)

    @app_commands.command(name="delete_custom_color")
    async def delete_custom_color_command(self, interaction: discord.Interaction):
        """delete your custom color role from the guild"""
        uid = str(interaction.user.id)
        existing_roles = await interaction.guild.fetch_roles()
        if not uid in [role.name for role in existing_roles]:
            return await interaction.response.send_message("You dont have a custom color", ephemeral=True)
        for role in existing_roles:
            if role.name == uid:
                await role.delete()
                return await interaction.response.send_message("Your custom color has been deleted")
        await interaction.response.send_message("something went wrong")
