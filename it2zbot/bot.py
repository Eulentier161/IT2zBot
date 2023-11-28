#!./.venv/bin/python
import discord
import uvloop
from discord.ext import commands

from it2zbot.cogs import (
    AdminCog,
    CalendarCog,
    ChannelCog,
    CustomReactionsCog,
    GithubCog,
    MiscCog,
    PollCog,
    ReminderCog,
    RolePickerView,
    RssCog,
    SelfManagementCog,
    SimpleGameCog,
)
from it2zbot.utils import Config, get_config

uvloop.install()


class MyBot(commands.Bot):
    def __init__(self, config: Config, intents):
        self.config = config
        super().__init__(command_prefix=config["command_prefix"], intents=intents)

    async def setup_hook(self):
        for cog in [AdminCog, CalendarCog, CustomReactionsCog, GithubCog, MiscCog, PollCog, ReminderCog, SelfManagementCog, ChannelCog, RssCog, SimpleGameCog]:
            await self.add_cog(cog(self))

        self.add_view(RolePickerView())

        if self.config["prod"]:
            await self.tree.sync()
        else:
            my_guild = discord.Object(self.config["guild"])
            self.tree.copy_global_to(guild=my_guild)
            await self.tree.sync(guild=my_guild)


def main():
    config = get_config()
    bot = MyBot(config, discord.Intents.all())
    bot.run(config["token"])


if __name__ == "__main__":
    main()
