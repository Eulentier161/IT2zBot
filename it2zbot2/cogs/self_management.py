import discord
from discord import app_commands
from discord.ext import commands


class SelfManagement(commands.GroupCog, name="self_management"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="setcolor")
    async def setcolor_cmd(self, interaction: discord.Interaction, color_hex: str):
        """assign a custom color-role to yourself or change your color"""
        try:
            color = discord.Colour.from_rgb(*[int(color_hex[i : i + 2], 16) for i in (0, 2, 4)])
        except ValueError:
            return await interaction.response.send_message("invalid hex-color", ephemeral=True)
        uid = str(interaction.user.id)
        existing_roles = await interaction.guild.fetch_roles()
        if uid in [role.name for role in existing_roles]:
            for role in existing_roles:
                if role.name != uid:
                    continue
                role = await role.edit(colour=color, reason="color role")
                break
        else:
            new_role = await interaction.guild.create_role(name=uid, colour=color, reason="color role")
            await interaction.user.add_roles(new_role)
        await interaction.response.send_message(role.mention)
