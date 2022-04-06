from pathlib import Path
from discord import Colour, DMChannel, User
import random


class Utils(object):
    """Generic utilities"""

    @staticmethod
    def get_project_root():
        return Path(__file__).parent.parent

    @staticmethod
    def random_color():
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return Colour.from_rgb(r, g, b)

    @staticmethod
    async def get_dm_channel(user: User) -> DMChannel:
        return user.dm_channel if user.dm_channel else await user.create_dm()

    @staticmethod
    def get_project_root() -> Path:
        return Path(__file__).parent.parent
