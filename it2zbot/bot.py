#!./.venv/bin/python
import discord
import uvloop
from discord.ext import commands

from cogs import custom_reactions, github, misc, self_management
from utils import get_config

uvloop.install()


class MyBot(commands.Bot):
    def __init__(self, config, intents):
        self.config = config
        super().__init__(command_prefix=config["command_prefix"], intents=intents)

    async def setup_hook(self):
        await self.add_cog(custom_reactions.CustomReactions(self))
        await self.add_cog(self_management.SelfManagement(self))
        await self.add_cog(misc.MiscCog(self))
        await self.add_cog(github.Github(self))

        if self.config["prod"]:
            await self.tree.sync()
        else:
            my_guild = discord.Object(self.config["guild"])
            self.tree.copy_global_to(guild=my_guild)
            await self.tree.sync(guild=my_guild)


if __name__ == "__main__":
    config = get_config()
    bot = MyBot(config, discord.Intents.all())
    bot.run(config["token"])
