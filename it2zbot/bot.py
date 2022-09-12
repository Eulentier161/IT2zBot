#!./.venv/bin/python
import discord
import yaml
from discord.ext import commands
from cogs import custom_reactions, self_management, misc

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
    MY_GUILD = discord.Object(cfg["guild"])
    TOKEN = cfg["token"]
    ADMINS = cfg["admins"]


class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.admins = ADMINS

    async def setup_hook(self):
        await self.add_cog(custom_reactions.CustomReactions(self))
        await self.add_cog(self_management.SelfManagement(self))
        await self.add_cog(misc.MiscCog(self))
        # self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(
            # guild=MY_GUILD
        )


bot = MyBot(command_prefix=".", intents=discord.Intents.all())

if __name__ == "__main__":
    bot.run(TOKEN)
