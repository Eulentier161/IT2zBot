from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import locale_str

from it2zbot.translations import translate

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class RolePickerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        cls=discord.ui.Select,
        options=[
            discord.SelectOption(value=value, label=f"projekt-{label}", emoji=emoji)
            for value, label, emoji in (
                (1152317540010303508, 1, "1\uFE0F\u20E3"),
                (1119674718686023781, 2, "2\uFE0F\u20E3"),
                (1152317648026214462, 3, "3\uFE0F\u20E3"),
                (1152317755740127294, 4, "4\uFE0F\u20E3"),
                (1152317804658315354, 5, "5\uFE0F\u20E3"),
                (1152317842130214972, 6, "6\uFE0F\u20E3"),
                (1152317938150428833, 7, "7\uFE0F\u20E3"),
                (1152318005586448525, 8, "8\uFE0F\u20E3"),
                (1152318057239293973, 9, "9\uFE0F\u20E3"),
                (1119012136614629456, 10, "\U0001f51f"),
            )
        ],
        min_values=0,
        max_values=10,
        placeholder="Select your groups...",
        custom_id="persistent_view:role_select",
    )
    async def select_roles(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(thinking=True, ephemeral=True)
        selected_roles = [interaction.guild.get_role(int(role_id)) for role_id in select.values]
        current_roles = [role for role in interaction.user.roles if role.name.startswith("projekt-")]
        to_be_removed = [role for role in current_roles if role not in selected_roles]
        to_be_added = [role for role in selected_roles if role not in current_roles]
        await interaction.user.remove_roles(*to_be_removed, reason="projekt-role-selector")
        await interaction.user.add_roles(*to_be_added, reason="projekt-role-selector")
        return await interaction.followup.send(
            f"updated your roles\nadded: {', '.join(role.mention for role in to_be_added)}\nremoved: {', '.join(role.mention for role in to_be_removed)}",
            ephemeral=True,
        )


@app_commands.guild_only()
class SelfManagementCog(commands.GroupCog, name=locale_str("self_management")):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=locale_str("set_custom_color"),
        description=locale_str("assign a custom color-role to yourself or change your color"),
    )
    @app_commands.describe(color=locale_str("the color you want to set"))
    @app_commands.rename(color=locale_str("color"))
    async def set_custom_color_command(self, interaction: discord.Interaction, color: str):
        try:
            color = discord.Colour.from_str(color)
        except ValueError:
            return await interaction.response.send_message(
                f"{translate('color must be in one of the following format', interaction)}\n"
                "- `0x<hex>`\n"
                "- `#<hex>`\n"
                "- `0x#<hex>`\n"
                "- `rgb(<number>, <number>, <number>)`\n"
                f"{translate('Like CSS, `<number>` can be either 0-255 or 0-100% and `<hex>` can be either a 6 digit hex number or a 3 digit hex shortcut (e.g. #fff).',interaction)}",
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
        await interaction.response.send_message(role.mention, ephemeral=True)

    @app_commands.command(
        name=locale_str("delete_custom_color"), description=locale_str("delete your custom color role from the guild")
    )
    async def delete_custom_color_command(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        existing_roles = await interaction.guild.fetch_roles()
        if not uid in [role.name for role in existing_roles]:
            return await interaction.response.send_message(
                translate("You dont have a custom color", interaction), ephemeral=True
            )
        for role in existing_roles:
            if role.name == uid:
                await role.delete()
                return await interaction.response.send_message(
                    translate("Your custom color has been deleted", interaction), ephemeral=True
                )
        await interaction.response.send_message(translate("something went wrong", interaction), ephemeral=True)

    @commands.command(name="init_role_picker")
    @commands.is_owner()
    async def init_role_picker(self, ctx: commands.Context, message: str):
        channel = await self.bot.fetch_channel(1152327496184889364)
        await channel.send(message, view=RolePickerView())
