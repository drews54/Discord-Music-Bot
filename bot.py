"""
Main body of the bot.

It only contains a few top-level commands and initialization procedures.
"""
import os
import textwrap
import time
from discord import Intents
from gettext import translation
from discord.ext import commands

token = os.getenv('DISCORD_TOKEN')
client = commands.Bot(command_prefix=os.getenv('DISCORD_PREFIXES'), intents=Intents.all())

if os.getenv('LANG').casefold().startswith('ru'):
    _ = translation('Discord-Music-Bot', './locale', languages=['ru']).gettext
else:
    _ = translation('Discord-Music-Bot', './locale', languages=['en']).gettext


def boxed_string(text) -> str:
    """Returns passed text string wrapped in triple backticks."""
    return '```' + text + '```'


@client.event
async def on_ready():
    """Prints to console when bot is ready."""
    print('Connected.')


@client.command(hidden=True)
async def load(ctx, extension: str):
    """Loads a module from ./cogs/ folder."""
    client.load_extension(f'cogs.{extension}')
    print(f'Module "{extension}" loaded')


@client.command(hidden=True)
async def unload(ctx, extension: str):
    """Unloads a module from ./cogs/ folder."""
    client.unload_extension(f'cogs.{extension}')
    print(f'Module "{extension}" unloaded')


@client.command(hidden=True)
async def reload(ctx, extension: str = 'music'):
    """Reloads a module from ./cogs/ folder."""
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    print(f'Module {extension} reloaded')


@client.command()
async def about(ctx):
    """Prints information about the bot to the active channel."""
    await ctx.send(boxed_string(
        _('GitHub source code') + ': https://github.com/duha54rus/Discord-Music-Bot' + '\n' +
        _('Docker Hub repository') + ': https://hub.docker.com/r/drews54/discord-music-bot')
    )


@client.command(hidden=True)
async def about_system(ctx):
    """Prints information about the OS running the bot to the active channel.

    Only works on certain flavors of Linux.
    """
    if os.name == 'posix':
        uname_result = os.uname()
        await ctx.send(textwrap.dedent(f"""\
            System name: {uname_result.sysname}
            Machine name: {uname_result.nodename}
            Release: {uname_result.release}
            Version: {uname_result.version}
            Hardware: {uname_result.machine}"""))
    else:
        await ctx.send('This OS type is not ***yet*** supported.')


@client.command(hidden=True, aliases=('exit', 'die', 'logout'))
@commands.is_owner()
async def shutdown(ctx, sec: int = 3):
    """Logs out and closes the bot after a certain time in seconds.

    Use rights are currently limited to the bot owner.
    """
    await ctx.send(f'Shutdown has been planned in {sec} s')
    time.sleep(sec)
    await ctx.send('Shutting down. Goodbye.')
    await client.close()


@client.event
async def on_command_error(ctx, error):
    """Prints error contents to current channel when encountered."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(textwrap.dedent("""\
            **{}** command not found.
            Use {}help
            """).format(ctx.message.content,
                        client.command_prefix))
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(textwrap.dedent("""\
            Missing command parameter.
            Missing parameter: **{}**
            Use **{}help {}** to get help.
            """).format(error.param,
                        client.command_prefix, ctx.command))
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
        client.load_extension(f'cogs.{filename[:-3]}')
        print(f'Module {filename[:-3]} loaded')

print('Connecting to gateway...')
client.run(token)
