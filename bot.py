"""
Main body of the bot.

It only contains a few top-level commands and initialization procedures.
"""
import os
import textwrap
import time
from re import fullmatch
from getpass import getpass
from gettext import translation
from discord import Intents
from discord.ext import commands

TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('DISCORD_PREFIX')
LANG = os.getenv('LANG')

if LANG is None or LANG.strip() == '':
    LANG = input('Select language | Выберите язык [EN/ru]: ').strip() or 'en'
if LANG.casefold().startswith('en'):
    _ = translation('Discord-Music-Bot', './locale', languages=['en']).gettext
elif LANG.casefold().startswith('ru'):
    _ = translation('Discord-Music-Bot', './locale', languages=['ru']).gettext
else:
    raise NameError(f"Couldn't find locale | Не найдена локаль: {LANG}")

if PREFIX is None or PREFIX.lstrip() == '':
    PREFIX = input(_('Enter prefix: ')).lstrip() or '$'

bot = commands.Bot(
    command_prefix=PREFIX, strip_after_prefix=True, intents=Intents(
        guilds=True, guild_messages=True, voice_states=True, presences=True, members=True))

if TOKEN is None or TOKEN == '':
    TOKEN = getpass(_('Enter token (not displayed): '))
assert fullmatch(r'[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}', TOKEN)


def boxed_string(text: str) -> str:
    """Returns passed text string wrapped in triple backticks."""
    return '```' + text + '```'


@bot.event
async def on_ready():
    """Prints to console when bot is ready."""
    print('Connected.')


@bot.command(hidden=True)
async def load(ctx: commands.Context, extension: str):  # pylint: disable=unused-argument
    """Loads a module from ./cogs/ folder."""
    bot.load_extension(f'cogs.{extension}')
    print(f'Module "{extension}" loaded')


@bot.command(hidden=True)
async def unload(ctx: commands.Context, extension: str):  # pylint: disable=unused-argument
    """Unloads a module from ./cogs/ folder."""
    bot.unload_extension(f'cogs.{extension}')
    print(f'Module "{extension}" unloaded')


@bot.command(hidden=True)
async def reload(ctx: commands.Context, extension: str = 'music'):  # pylint: disable=unused-argument
    """Reloads a module from ./cogs/ folder."""
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    print(f'Module {extension} reloaded')


@bot.command()
async def about(ctx: commands.Context):
    """Prints information about the bot to the active channel."""
    await ctx.send(boxed_string(
        _('GitHub source code') + ': https://github.com/duha54rus/Discord-Music-Bot' + '\n' +
        _('Docker Hub repository') + ': https://hub.docker.com/r/drews54/discord-music-bot')
    )


@bot.command(hidden=True)
async def about_system(ctx: commands.Context):
    """Prints information about the OS running the bot to the active channel.

    Only works on certain flavors of Linux.
    """
    if os.name == 'posix':
        uname_result = os.uname()  # pylint: disable=no-member
        await ctx.send(textwrap.dedent(f"""\
            System name: {uname_result.sysname}
            Machine name: {uname_result.nodename}
            Release: {uname_result.release}
            Version: {uname_result.version}
            Hardware: {uname_result.machine}"""))
    else:
        await ctx.send('This OS type is not ***yet*** supported.')


@bot.command(hidden=True, aliases=('exit', 'die', 'logout'))
@commands.is_owner()
async def shutdown(ctx: commands.Context, sec: int = 3):
    """Logs out and closes the bot after a certain time in seconds.

    Use rights are currently limited to the bot owner.
    """
    await ctx.send(f'Shutdown has been planned in {sec} s')
    time.sleep(sec)
    await ctx.send('Shutting down. Goodbye.')
    await ctx.voice_client.disconnect()
    await bot.close()


@bot.event
async def on_command_error(ctx: commands.Context, error):
    """Prints error contents to current channel when encountered."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(textwrap.dedent("""\
            **{}** command not found.
            Use {}help
            """).format(ctx.message.content,
                        bot.command_prefix))
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(textwrap.dedent("""\
            Missing command parameter.
            Missing parameter: **{}**
            Use **{}help {}** to get help.
            """).format(error.param,
                        bot.command_prefix, ctx.command))
    elif isinstance(error, commands.NotOwner):
        await ctx.send(f"Error: {error}")
    else:
        await ctx.send(
            'Something went wrong...'
        )
        print(textwrap.dedent("""\
            Command: {}
            Error log:
            {}""").format(ctx.command, error))


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
        print(f'Module {filename[:-3]} loaded')

print('Connecting to gateway...')
bot.run(TOKEN)
