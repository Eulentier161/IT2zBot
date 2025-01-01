#!./.venv/bin/python
import discord
from discord.ext import commands

from it2zbot.cogs import COGS, RolePickerView
from it2zbot.utils import Config, get_config
from it2zbot.translations import MyTranslator

try:
    import uvloop

    uvloop.install()
except:
    print("failed to import uvloop, falling back to the built-in asyncio event loop")


class MyBot(commands.Bot):
    def __init__(self, config: Config, intents):
        self.config = config
        super().__init__(command_prefix=config["command_prefix"], intents=intents)

    async def setup_hook(self):
        for cog in COGS:
            await self.add_cog(cog(self))

        self.add_view(RolePickerView())
        await self.tree.set_translator(MyTranslator())

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
