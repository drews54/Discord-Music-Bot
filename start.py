import discord
import os
from discord.ext import commands

client = commands.Bot(command_prefix = 'bro ')
token = ''
with open('BotToken.txt') as tokenFile:
    token = tokenFile.readline()

@client.event
async def on_ready():
    print('Connected.')

@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    print(extension + ' loaded')

@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print(extension + ' unloaded')

@client.command()
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print(extension + ' unloaded')
    client.load_extension(f'cogs.{extension}')
    print(extension + ' loaded')
    await ctx.message.channel.send('```' + extension + ' module has been reloaded```')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(filename[:-3] + ' loaded')

client.run(token)
