import discord, os, json
from discord.ext import commands

if not os.path.exists('./data.json'):
        
        user_token = input('Enter your bot token:\n')
        user_input = input('Enter your prefixes separated by commas(do not use spaces between prefixes)\n')
        user_prefixes = user_input.split(',')

        data_file = {
            'token' : user_token,
            'prefix' : user_prefixes
        }
        with open('data.json', 'x', encoding = 'utf-8') as file:
            json.dump(data_file, file, sort_keys = True, indent = 2)
        print('Data file has been created.')

with open('data.json', encoding = 'utf-8') as dataFile:
    global client
    global token

    data = json.load(dataFile)

    token = data['token']
    client = commands.Bot(command_prefix = tuple(data['prefix']))

@client.event
async def on_ready():
    print('Connected.')

@client.command(hidden = True)
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    print(f'Module {extension} loaded')

@client.command(hidden = True)
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print(f'Module {extension} unloaded')

@client.command(hidden = True)
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    print(f'Module {extension} reloaded')
    await ctx.send(f'```Module {extension} module has been reloaded```')

@client.command()
async def about(ctx):
    await ctx.send('```Github source code link: https://github.com/duha54rus/Discord-Music-Bot```')

@client.command(hidden=True, aliases=['exit', 'die', 'logout'])
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send('Shutting down.\nGoodbye.')
    await client.logout()

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(f'Module {filename[:-3]} loaded')

print('\nConnecting to server...')
client.run(token)
