import gettext
import subprocess
from pathlib import Path

import discord
from discord import app_commands

localedir = Path(__file__, "../").resolve()
gettext.bindtextdomain("messages", "translations")
gettext.textdomain("messages")

languages = {
    locale: gettext.translation("messages", localedir=localedir, languages=[lang])
    for lang, locale in [("en", "en"), ("de", discord.Locale.german), ("ja", discord.Locale.japanese)]
}


class MyTranslator(app_commands.Translator):
    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> str | None:
        message = str(string)
        return languages.get(locale, languages["en"]).gettext(message)


def translate(message: str, interaction: discord.Interaction) -> str:
    return languages.get(interaction.locale, languages["en"]).gettext(message)


def compile_mo_files():
    for root, dirs, files in localedir.walk():
        for file in files:
            if file.endswith(".po"):
                po_file = Path(root, file)
                mo_file = Path(root, f"{po_file.stem}.mo")
                subprocess.run(["msgfmt", "-o", str(mo_file.absolute()), str(po_file.absolute())])
                print(f"Compiled {po_file.relative_to(localedir)} to {mo_file.relative_to(localedir)}")
