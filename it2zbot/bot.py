#!./.venv/bin/python
import discord
import uvloop
from discord.ext import commands

from it2zbot.cogs import (
    AdminCog,
    CalendarCog,
    CustomReactionsCog,
    GithubCog,
    MiscCog,
    ReminderCog,
    RSICog,
    SelfManagementCog,
)
from it2zbot.utils import get_config

uvloop.install()


class MyBot(commands.Bot):
    def __init__(self, config, intents):
        self.config = config
        super().__init__(command_prefix=config["command_prefix"], intents=intents)

    async def setup_hook(self):
        await self.add_cog(CustomReactionsCog(self))
        await self.add_cog(SelfManagementCog(self))
        await self.add_cog(MiscCog(self))
        await self.add_cog(GithubCog(self))
        await self.add_cog(ReminderCog(self))
        await self.add_cog(CalendarCog(self))
        await self.add_cog(AdminCog(self))
        await self.add_cog(RSICog(self))

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
