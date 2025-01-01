import gettext
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
