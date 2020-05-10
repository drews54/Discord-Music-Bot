import discord
from discord.ext import commands

class Connection(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def join(self, ctx):
        await ctx.message.channel.send('Connecting')
        await ctx.message.author.voice.channel.connect()
        await ctx.message.channel.send('Connected')

    @commands.command()
    async def leave(self, ctx):
        await ctx.message.guild.voice_client.disconnect()

def setup(client):
    client.add_cog(Connection(client))
