import discord, os, time, gettext
from discord.ext import commands

token = os.getenv('DISCORD_TOKEN')
client = commands.Bot(command_prefix = tuple(os.getenv('DISCORD_PREFIXES').split())) #Import prefixes as space-separated values

langRU = gettext.translation('Discord-Music-Bot', './locale', languages=['ru'])
langEN = gettext.translation('Discord-Music-Bot', './locale', languages=['en'])
if os.getenv('LANG').casefold().startswith('ru'):
    _ = langRU.gettext
else:
    _ = langEN.gettext

@client.event
async def on_ready():
    print('Connected.')

@client.command(hidden = True)
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    print(f'Module "{extension}" loaded')

@client.command(hidden = True)
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print(f'Module "{extension}" unloaded')

@client.command(hidden = True)
async def reload(ctx, extension = 'music'):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    print(f'Module {extension} reloaded')
    await ctx.send(f'```Module "{extension}" has been reloaded```')

@client.command()
async def about(ctx):
    await ctx.send(
        '```' +
        _('GitHub source code') + ': https://github.com/duha54rus/Discord-Music-Bot' + '\n' +
        _('Docker Hub repository') + ': https://hub.docker.com/r/drews54/discord-music-bot' +
        '```'
    )

@client.command(hidden = True)
async def about_system(ctx):
    if os.name == 'posix':
        uname_result = os.uname()
        await ctx.send(f"""
System name: {uname_result.sysname}
Machine name: {uname_result.nodename}
Release: {uname_result.release}
Version: {uname_result.version}
Hardware: {uname_result.machine}""")
    else:
        await ctx.send('This OS type is not yet supported.')

@client.command(hidden=True, aliases=['exit', 'die', 'logout'])
@commands.is_owner()
async def shutdown(ctx, sec: int = 60):
    await ctx.send(f'Shutdown has been planned in {sec} s')
    time.sleep(sec)
    await ctx.send('Shutting down. Goodbye.')
    await client.logout()

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(f'Module {filename[:-3]} loaded')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f'**{ctx.message.content}** command not found. Use {client.command_prefix[0]}help')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Missing command parameter.\nMissing parameter: **{error.param}**\nUse **{client.command_prefix[0]}help {ctx.command}**')
    else:
        await ctx.send(f'Something went wrong...\nCommand: {ctx.command}\nError log:\n{error}')
        print(f'Command: {ctx.command}\nError log:\n{error}')

print('Connecting to gateway...')
client.run(token)
""" Expanded run command. Interrupts are not handled for unknown reasons.
try:
    client.loop.run_until_complete(client.start(token))
except discord.errors.LoginFailure:
    print('Login failed')
except discord.errors.ConnectionClosed as err:
    print(f'Connection clesed: {err.reason}')
except KeyboardInterrupt or InterruptedError:
    client.loop.run_until_complete(client.logout())
finally:
    client.loop.close()
"""