import discord
import os
import json
from discord.ext import commands

with open('Data.json', encoding = 'utf-8') as dataFile:
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
    print(extension + ' loaded')

@client.command(hidden = True)
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print(extension + ' unloaded')

@client.command(hidden = True)
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print(extension + ' unloaded')
    client.load_extension(f'cogs.{extension}')
    print(extension + ' loaded')
    await ctx.message.channel.send('```' + extension + ' module has been reloaded```')

@client.command()
async def about(ctx):
    await ctx.message.channel.send('```Github source code link: https://github.com/duha54rus/Discord-Music-Bot```')

#for filename in os.listdir('./cogs'):
#    if filename.endswith('.py'):
#        client.load_extension(f'cogs.{filename[:-3]}')
#        print(filename[:-3] + ' loaded')
client.load_extension('cogs.music')

@client.command()
async def convert(ctx):
    client.load_extension(f'cogs.convert')
    await ctx.message.channel.send('```Converter loaded```')

client.run(token)
