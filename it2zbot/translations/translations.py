from discord import app_commands
import discord
import gettext

gettext.bindtextdomain("messages", "translations")
gettext.textdomain("messages")

languages = {
    lang: gettext.translation("messages", localedir="translations", languages=[lang]) for lang in ["en", "de", "ja"]
}


class MyTranslator(app_commands.Translator):
    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> str | None:
        message = str(string)
        
        if locale is discord.Locale.japanese:
            return languages["ja"].gettext(message)
        elif locale is discord.Locale.german:
            return languages["de"].gettext(message)
        else:
            return languages["en"].gettext(message)

