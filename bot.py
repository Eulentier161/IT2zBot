try:
    import uvloop

    uvloop.install()
except ImportError:
    print("Couldn't install uvloop, falling back to the slower asyncio event loop")

import os
import discord
from discord.ext.commands import Bot
from cogs import admin, selfmanagement, info
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents().all()
client = Bot(command_prefix="?", intents=intents)


@client.event
async def on_ready():
    print(f"logged in as {client.user}")
    print(f"connected to {len(client.guilds)} guilds")
    await client.change_presence(activity=discord.Game(name="Nekopara Vol. 4"))


if __name__ == "__main__":
    client.add_cog(admin.AdminCog(client))
    client.add_cog(selfmanagement.SelfmanagementCog(client))
    client.add_cog(info.InfoCog(client))
    client.run(os.getenv("TOKEN"))
