import random
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import locale_str

from it2zbot.translations import translate

if TYPE_CHECKING:
    from it2zbot.bot import MyBot


class ChoiceButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(label=label)

    async def callback(self, interaction: discord.Interaction):
        view: SimpleGameView = self.view
        content = ""

        if self.label == translate("Weiter laufen", interaction):
            content += translate("Das ist der Wald.\nDas Spiel endet Hier.", interaction)
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

        elif self.label == translate("Eingang Erkunden", interaction):
            view.gold += 1
            content += translate(
                "Beim betreten des Einganges findest du eine Münze!\nEtwas weiter geradeaus befindet sich ein zwielichtiger Pfad nach links und ein beleuchteter Pfad nach rechts.",
                interaction,
            )
            view.firstChoiceButton.label = translate("Pfad", interaction) + " " + translate("links", interaction)
            view.secondChoiceButton.label = translate("Pfad", interaction) + " " + translate("rechts", interaction)

        elif self.label.startswith(translate("Pfad", interaction)):
            if self.label.endswith(translate("links", interaction)):
                content += (
                    translate(
                        "In der Höhle begegnet die Ein Goblin der dich angreift! Du schaffst es gerade noch zu fliehen",
                        interaction,
                    )
                    + "\n"
                )
                if random.randint(1, 20) <= 5:
                    content += (
                        translate("Du hast den Angriff abgewehrt und keine Lebenspunkte verloren", interaction) + "\n\n"
                    )
                else:
                    dmg = random.randint(10, 50)
                    view.life -= dmg
                    if view.life <= 0:
                        view.life = 0
                    content += (
                        translate(
                            "Du wurdest getroffen!\nDir wurden {dmg} Lebenspunkte abgezogen.\nDu hast noch: {life} Lebenspunkte.",
                            interaction,
                        ).format(dmg=dmg, life=view.life)
                        + "\n\n"
                    )
                    if view.life == 0:
                        content += translate("Du bist gestorben :(\n  ---GAME OVER---)", interaction)
                        for button in view.children:
                            button.disabled = True
                        view.stop()
                        return await interaction.response.edit_message(
                            content=translate("`gold: {gold}`\n`life: {life}`", interaction).format(
                                gold=view.gold, life=view.life, content=content
                            )
                            + "\n{content}",
                            view=view,
                        )

            elif self.label.endswith(translate("rechts", interaction)):
                content += (
                    translate("Der Pfad endet hier. du musst zurück um Anfang um den rest zu Erkunden!", interaction)
                    + "\n"
                )

            view.firstChoiceButton.label, view.secondChoiceButton.label = translate(
                "Weiter laufen", interaction
            ), translate("Eingang Erkunden", interaction)
            content += translate(
                "Du stehst in einem Wald mit einer Taschenlampe. Vor dir ist ein Mysteriöser Eingang.", interaction
            )

        await interaction.response.edit_message(
            content=translate("`gold: {gold}`\n`life: {life}`", interaction).format(gold=view.gold, life=view.life)
            + "\n"
            + content,
            view=view,
        )


class SimpleGameView(discord.ui.View):
    children: list[ChoiceButton]

    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.gold = 0
        self.life = 100
        self.firstChoiceButton = ChoiceButton(label=translate("Weiter laufen", interaction))
        self.secondChoiceButton = ChoiceButton(label=translate("Eingang Erkunden", interaction))
        self.add_item(self.firstChoiceButton)
        self.add_item(self.secondChoiceButton)


class SimpleGameCog(commands.GroupCog, name=locale_str("simple_game")):
    def __init__(self, bot: "MyBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name=locale_str("start"))
    async def simple_game_cmd(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            translate("`gold: {gold}`\n`life: {life}`", interaction).format(gold=0, life=100)
            + "\n"
            + translate(
                "Du stehst in einem Wald mit einer Taschenlampe. Vor dir ist ein Mysteriöser Eingang.", interaction
            ),
            view=SimpleGameView(interaction),
        )
