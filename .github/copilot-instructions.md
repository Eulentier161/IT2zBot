# Copilot instructions

## Project

- IT2zBot is a Python 3.14+ Discord bot built with `discord.py`.
- The package is `it2zbot/`; the executable entry point is `it2zbot.bot:main`.
- Bot features are implemented as Discord.py cogs in `it2zbot/cogs/`.

## Working in this repository

- This project uses the `uv` CLI for environment and dependency management and for running project commands; prefer `uv` over `pip` or direct invocation.
- Follow the existing cog patterns and keep bot startup and cog registration consistent with `it2zbot/bot.py` and `it2zbot/cogs/__init__.py`.
- When adding a cog, define it in `it2zbot/cogs/` and register its class in `COGS`.
- Keep configuration access consistent with the `Config` type and `get_config()` in `it2zbot/utils.py`. Never add credentials, tokens, private keys, or local configuration/database files to source control.
- Translations are gettext catalogs under `it2zbot/translations/<locale>/LC_MESSAGES/messages.po`. When changing catalogs, compile them with `uv run compile_translations` (requires `msgfmt`).
- Use Black formatting with a 120-character line length and isort's Black profile, as configured in `pyproject.toml`.
- Keep dependencies and project metadata in `pyproject.toml`; use `uv` to update `uv.lock` when dependencies change.
- Make focused changes and preserve existing behavior. Check for relevant tests before changing behavior; do not claim tests were run if no applicable test suite exists.
