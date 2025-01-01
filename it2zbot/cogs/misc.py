import asyncio
import random
import re
import sqlite3
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Literal

import discord
import httpx
from discord import CustomActivity, Streaming, app_commands
from discord.ext import commands, tasks

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


ACTIVITIES = [
    *[
        CustomActivity(text)
        for text in [
            "testhuhn",
            "is das jetzt quasi open source for a fee?",
            "get (user_id course_id)",
            "open source funktioniert einfach nicht",
            "absoluter pflad",
            "Könnt ihr mein Steam Profil bewerten?",
            "#freeport22",
            "HAAAAALLLLOOOOOOOOO!!!",
            "Stuhlkreis!",
            "der Boden ist aus Boden gemacht.",
            "Wenn jeder an sich denkt ist an jeden gedacht.",
            "objectively mein bester status",
            "Hey Leute, checkt mal meinen Podcast!",
        ]
    ],
    Streaming(
        name="dramaonair",
        url="https://twitch.tv/dramaonair",
        platform="Twitch",
    ),
]


@dataclass
class PlayingCard:
    suit: Literal["hearts", "clubs", "spades", "diamonds"]
    symbol: Literal[2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"]

    def __repr__(self):
        suits_map = {
            "hearts": "\u2665\uFE0F",
            "clubs": "\u2663\uFE0F",
            "spades": "\u2660\uFE0F",
            "diamonds": "\u2666\uFE0F",
        }
        return f"{suits_map[self.suit]}{self.symbol}"


class Hand:
    def __init__(self):
        self.cards: list[PlayingCard] = []
        self.value = 0

    def _calculate_hand_value(self):
        self.value = 0
        aces: list[PlayingCard] = []

        for card in self.cards:
            if isinstance(card.symbol, int):
                self.value += card.symbol
            elif card.symbol == "A":
                aces.append(card)
                self.value += 11
            else:
                self.value += 10

        # count as many aces as needed as 1 instead of 11 to get below or equal to 21
        i = 0
        while self.value > 21 and i < len(aces):
            self.value -= 10
            i += 1

        return self.value

    def take(self, card: PlayingCard):
        self.cards.append(card)
        self._calculate_hand_value()

    def __repr__(self) -> str:
        return f"({self.value}) {', '.join([str(card) for card in self.cards])}"


class MiscCog(commands.Cog):
    def __init__(self, bot: "MyBot") -> None:
        with sqlite3.connect("bot.db") as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS quotes (
                    author  VARCHAR(25),
                    message VARCHAR(25),
                    channel VARCHAR(25),
                    guild   VARCHAR(25),
                    content VARCHAR(2000),
                    PRIMARY KEY (author, message, channel, guild)
                );
                """
            )
        self.bot = bot
        self.set_status.start()
        self.quote_ctx_menu = app_commands.ContextMenu(name="quote", callback=self.quote)
        self.bot.tree.add_command(self.quote_ctx_menu)
        self.randomize_role_color.start()

    def cog_unload(self):
        self.set_status.cancel()

    @app_commands.command(name="joke")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.describe(category="joke category")
    async def joke_command(
        self,
        interaction: discord.Interaction,
        category: Literal["Any", "Misc", "Programming", "Dark", "Pun", "Spooky", "Christmas"],
    ):
        """get a random joke"""
        async with httpx.AsyncClient() as httpx_client:
            res: dict = (
                await httpx_client.get(f"https://v2.jokeapi.dev/joke/{category}?blacklistFlags=racist,sexist,political")
            ).json()

        if (type := res.get("type", None)) == "single":
            await interaction.response.send_message(f"{res['joke']}")
        elif type == "twopart":
            await interaction.response.send_message(f"{res['setup']}\n\n||{res['delivery']}||")
        else:
            await interaction.response.send_message(f"something went wrong ¯\\_(ツ)_/¯", ephemeral=True)

    @app_commands.command(name="button")
    async def button_command(self, interaction: discord.Interaction):
        """get a button to click :)"""

        class ClickableButton(discord.ui.View):
            @discord.ui.button(label=":(", style=discord.ButtonStyle.red)
            async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
                button.disabled = True
                button.style = discord.ButtonStyle.green
                button.label = ":)"
                await interaction.response.edit_message(content="You did press the Button!! Yay!!", view=self)

        await interaction.response.send_message(content="Press the Button!!", view=ClickableButton(), ephemeral=True)

    @app_commands.command(name="shorten")
    @app_commands.describe(url="the big url to shorten", slug="the slug in 'https://eule.wtf/slug'")
    async def shorten_cmd(self, interaction: discord.Interaction, url: str, slug: str):
        """shorten a url with the worlds famous eule.wtf TM service"""
        async with httpx.AsyncClient() as client:
            res = await client.post("https://eule.wtf/api", json={"slug": slug, "destination": url})
        if res.status_code != 200:
            return await interaction.response.send_message(res.json()["message"], ephemeral=True)
        return await interaction.response.send_message(res.json()["url"], ephemeral=True)

    @commands.Cog.listener("on_message")
    async def preview_linked_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if (
            not message.content.count("/") == 6
            or not message.content.startswith("https://discord.com/channels/")
            or not all([id.isdigit() for id in message.content.split("/")[-3:]])
        ):
            return  # doesnt look like a discord message link

        channel_id, message_id = [id for id in message.content.split("/")[-2:]]
        linked_message = await (await self.bot.fetch_channel(channel_id)).fetch_message(message_id)
        files = [await attachment.to_file() for attachment in linked_message.attachments]

        await message.reply(linked_message.content, embeds=linked_message.embeds, files=files)

    @app_commands.command(name="avatar")
    async def avatar_cmd(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message(file=(await user.display_avatar.to_file()), ephemeral=True)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.quote_ctx_menu.name, type=self.quote_ctx_menu.type)

    async def quote(self, interaction: discord.Interaction, message: discord.Message):
        if not message.content.strip():
            return await interaction.response.send_message(
                "the message does not contain plain text and is discarded", ephemeral=True
            )
        try:
            with sqlite3.connect("bot.db") as connection:
                connection.execute(
                    f"""
                    INSERT INTO quotes (
                        author,
                        message,
                        channel,
                        guild,
                        content
                    ) VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        str(message.author.id),
                        str(message.id),
                        str(message.channel.id),
                        str(message.guild.id),
                        message.content,
                    ),
                )
        except sqlite3.IntegrityError:
            return await interaction.response.send_message(f"this message has already been saved as quote")
        await interaction.response.send_message(
            f"added quote from {message.author.name} for [this message]({message.jump_url})"
        )

    @app_commands.command(name="quote")
    async def get_quote(self, interaction: discord.Interaction):
        """get a random quote"""
        with sqlite3.connect("bot.db") as connection:
            user_id, message_id, channel_id, _, content = connection.execute(
                "SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1;"
            ).fetchone()
        jump_url = (await (await self.bot.fetch_channel(int(channel_id))).fetch_message(int(message_id))).jump_url
        user_name = (await self.bot.fetch_user(int(user_id))).name
        embed = discord.Embed(url=jump_url, description=content, title=user_name, color=0x7A00FF)
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener("on_message")
    async def trigger_animal_reaction(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        emojis = ["🐸", "🦝"]
        random.shuffle(emojis)

        reactions = [emoji for emoji in emojis if random.random() < 0.01]
        for reaction in reactions:
            await message.add_reaction(reaction)

    def cog_unload(self):
        self.randomize_role_color.cancel()

    @tasks.loop(minutes=5.0)
    async def randomize_role_color(self):
        try:
            guild = self.bot.get_guild(958611525541720064)
            role = guild.get_role(1027636884731596911)
            await role.edit(color=discord.colour.Colour.from_rgb(*[random.randint(0, 255) for _ in range(3)]))
        except:
            pass

    @randomize_role_color.before_loop
    async def before_randomize_role_color(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="say")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def say_command(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        await channel.send(message)
        await interaction.response.send_message("✅", ephemeral=True)

    @app_commands.command(name="moodle_status")
    async def is_moodle_up_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            r = f"reached in {round(httpx.get('https://moodle.itech-bs14.de/').elapsed.total_seconds() * 1000)}ms"
        except httpx.RequestError:
            r = "unreachable"
        finally:
            await interaction.followup.send(r)

    @app_commands.command(name="blackjack")
    async def blackjack(self, interaction: discord.Interaction):
        class HitButton(discord.ui.Button):
            def __init__(self, disabled):
                super().__init__(label="hit", style=discord.ButtonStyle.green, disabled=disabled)

            async def callback(self, interaction: discord.Interaction):
                view: GameView = self.view
                await view.handle_hit_button(interaction)

        class StopButton(discord.ui.Button):
            def __init__(self, disabled):
                super().__init__(label="stop", style=discord.ButtonStyle.red, disabled=disabled)

            async def callback(self, interaction: discord.Interaction):
                view: GameView = self.view
                await view.handle_stop_button(interaction)

        class GameView(discord.ui.View):
            def __init__(self, player_hand: Hand, dealer_hand: Hand, deck: list[PlayingCard], embed: discord.Embed):
                super().__init__()
                self.hit_button = HitButton(disabled=player_hand.value == 21)
                self.stop_button = StopButton(disabled=player_hand.value == 21)
                self.add_item(self.hit_button)
                self.add_item(self.stop_button)
                self.player_hand = player_hand
                self.dealer_hand = dealer_hand
                self.deck = deck
                self.embed = embed

            async def handle_hit_button(self, interaction: discord.Interaction):
                self.player_hand.take(self.deck.pop())
                self.embed.add_field(
                    name="hit", value=f"dealer: {self.dealer_hand}\nplayer: {self.player_hand}", inline=False
                )
                if self.player_hand.value == 21:
                    return await self.dealer_turns(interaction)
                elif self.player_hand.value > 21:
                    self.hit_button.disabled = True
                    self.stop_button.disabled = True
                    self.embed.add_field(name="result", value="bust")
                await interaction.response.edit_message(embed=self.embed, view=self)

            async def handle_stop_button(self, interaction: discord.Interaction):
                await self.dealer_turns(interaction)

            async def dealer_turns(self, interaction: discord.Interaction):
                self.hit_button.disabled = True
                self.stop_button.disabled = True
                while self.dealer_hand.value < 17:
                    self.dealer_hand.take(self.deck.pop())
                self.embed.add_field(
                    name="dealers turn", value=f"dealer: {self.dealer_hand}\nplayer: {self.player_hand}", inline=False
                )
                if self.dealer_hand.value > 21:
                    self.embed.add_field(name="result", value="dealer bust")
                elif self.player_hand.value == self.dealer_hand.value:
                    self.embed.add_field(name="result", value="tie")
                elif self.player_hand.value > self.dealer_hand.value:
                    self.embed.add_field(name="result", value="win")
                elif self.player_hand.value < self.dealer_hand.value:
                    self.embed.add_field(name="result", value="lose")
                await interaction.response.edit_message(embed=self.embed, view=self)

        player_hand, dealer_hand = Hand(), Hand()
        deck = [
            PlayingCard(suit, value)
            for value in [*range(2, 11), *"JQKA"]
            for suit in ["hearts", "clubs", "spades", "diamonds"]
        ]
        random.shuffle(deck)
        dealer_hand.take(deck.pop())
        player_hand.take(deck.pop())
        player_hand.take(deck.pop())

        embed = discord.Embed(title="Black Jack", url="https://en.wikipedia.org/wiki/Blackjack")
        embed.add_field(name="starting hands", value=f"dealer: {dealer_hand}\nplayer: {player_hand}", inline=False)
        if player_hand.value == 21:
            embed.add_field(name="result", value="Black Jack!")

        await interaction.response.send_message(
            embed=embed,
            view=GameView(player_hand, dealer_hand, deck, embed),
            ephemeral=True,
        )

    @tasks.loop(minutes=1)
    async def set_status(self):
        await self.bot.change_presence(activity=random.choice(ACTIVITIES))

    @set_status.before_loop
    async def before_set_status(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener("on_message")
    async def jesus_tanz(self, message: discord.Message):
        if message.author.id != 414138605133627396:
            return
        jesus_ids = [
            "LSyT7s8XC3g",
            "wqrh2FWvUBI",
            "-0I_By13FOA",
            "XpLpbetC6MA",
            "rKIMXXaUu7U",
            "A34KSjPWNsY",
            "7mI5yKC34E4",
        ]
        links = re.findall(r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-&?=%.]+", message.content)
        if not links:
            return
        jesus_wurde_betanzt = False

        async with httpx.AsyncClient() as client:
            for link in links:
                try:
                    request = await client.get(link, follow_redirects=True)
                except:
                    continue
                query = request.url.query.decode("utf-8")
                if jesus_wurde_betanzt := any([jesus_id in query for jesus_id in jesus_ids]):
                    break

        if not jesus_wurde_betanzt:
            return

        try:
            await message.author.timeout(timedelta(minutes=1))
        except discord.errors.Forbidden:
            pass

        await asyncio.gather(
            message.delete(),
            message.channel.send(
                f"{message.author.mention} es hat sich ausgejesustanzt! <:pepeevil:1079434494165135360>"
            ),
        )
