import random
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class ChoiceButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(label=label)

    async def callback(self, interaction: discord.Interaction):
        view: SimpleGameView = self.view
        content = ""

        if self.label == "Weiter laufen":
            content += "Das ist der Wald.\nDas Spiel endet Hier."
            if view.gold:
                content += "\n".join(
                    [
                        "```\n",
                        "                     ,",
                        "                    (_) ",
                        "                    |-|",
                        "                    | |",
                        "                    | |",
                        "                   .| |. ",
                        "                  |'---'|",
                        "                  |~  ~~|",
                        "              .-@'|  ~  |'@-.",
                        "             (@    '---'    @)",
                        "             |'-@..__@__..@-'|",
                        "          () |~  ~ ~ ~     ~ | ()",
                        "         .||'| ~() ~   ~ ()~ |'||.",
                        "        ( || @'-||.__~__.||-'@ || )",
                        "        |'-.._  ||   @   ||  _..-'|",
                        "        |~ ~  '''---------'''  ~  |",
                        "        |  ~  ~  Y  O  U   ~  ~  ~|",
                        "        | ~   F U C K I N G   ~ ~ |",
                        "         '-.._  !!! WON !!!  _..-'",
                        "              '''---------'''",
                        "```",
                    ]
                )
            for button in view.children:
                button.disabled = True
            view.stop()

        elif self.label == "Eingang Erkunden":
            view.gold += 1
            content += "Beim betreten des Einganges findest du eine Münze!\nEtwas weiter geradeaus befindet sich ein zwielichtiger Pfad nach links und ein beleuchteter Pfad nach rechts."
            view.firstChoiceButton.label = "Pfad links"
            view.secondChoiceButton.label = "Pfad rechts"

        elif self.label.startswith("Pfad "):
            if self.label.endswith("links"):
                content += "In der Höhle begegnet die Ein Goblin der dich angreift! Du schaffst es gerade noch zu fliehen\n"
                if random.randint(1, 20) <= 5:
                    content += "Du hast den Angriff abgewehrt und keine Lebenspunkte verloren\n\n"
                else:
                    dmg = random.randint(10, 50)
                    view.life -= dmg
                    if view.life <= 0:
                        view.life = 0
                    content += f"Du wurdest getroffen!\nDir wurden {dmg} Lebenspunkte abgezogen.\nDu hast noch: {view.life} Lebenspunkte.\n\n"
                    if view.life == 0:
                        content += "Du bist gestorben :(\n  ---GAME OVER---)"
                        for button in view.children:
                            button.disabled = True
                        view.stop()
                        return await interaction.response.edit_message(content=f"`gold: {view.gold}`\n`life: {view.life}`\n{content}", view=view)

            elif self.label.endswith("rechts"):
                content += "Der Pfad endet hier. du musst zurück um Anfang um den rest zu Erkunden!\n"

            view.firstChoiceButton.label, view.secondChoiceButton.label = "Weiter laufen", "Eingang Erkunden"
            content += "Du stehst in einem Wald mit einer Taschenlampe. Vor dir ist ein Mysteriöser Eingang."

        await interaction.response.edit_message(content=f"`gold: {view.gold}`\n`life: {view.life}`\n{content}", view=view)


class SimpleGameView(discord.ui.View):
    children: list[ChoiceButton]

    def __init__(self):
        super().__init__()
        self.gold = 0
        self.life = 100
        self.firstChoiceButton = ChoiceButton(label="Weiter laufen")
        self.secondChoiceButton = ChoiceButton(label="Eingang Erkunden")
        self.add_item(self.firstChoiceButton)
        self.add_item(self.secondChoiceButton)


class SimpleGameCog(commands.GroupCog, name="simple_game"):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="start")
    async def simple_game_cmd(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"`gold: 0`\n`life: 100`\nDu stehst in einem Wald mit einer Taschenlampe. Vor dir ist ein Mysteriöser Eingang.",
            view=SimpleGameView(),
        )
