import discord
import os
from discord.ext import commands

class Converter(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._fileslist = []
        self._fileslist_updater()

    async def boxed_print(self, ctx, text):
        await ctx.message.channel.send('```' + text + '```')

    @commands.command()
    async def convert(self, ctx, arg):
        if arg == 'list':
            self._fileslist_updater()
            if not self._fileslist:
                await self.boxed_print(ctx, 'No files to convert')
                return
            i = 0
            string = ''
            for name in self._fileslist:
                i += 1
                string += f'{i!s}. {name!s}\n'
            await self.boxed_print(ctx, string)
        else:
            file = self._fileslist[int(arg) - 1]
            await self.boxed_print(ctx, f'I`m going to convert {file} to ".opus" format')


    def _fileslist_updater(self):
        self._fileslist.clear()
        for filename in os.listdir('./music'):
            if not filename.endswith('.opus'):
                self._fileslist.append(filename)

def setup(client):
    client.add_cog(Converter(client))
