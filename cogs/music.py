import discord
import os
import youtube_dl
from discord.utils import get
from discord.ext import commands
from asyncio import run_coroutine_threadsafe

class Music(commands.Cog):

    _songs = []

    def __init__(self, client):
        self.client = client
        if not os.path.exists('./music'): os.mkdir('./music')
        self._tracklist()

    async def boxed_print(self, ctx, text):
        await ctx.message.channel.send('```' + text + '```')

    def _tracklist(self):
        for filename in os.listdir('./music'):
            if filename.endswith('.opus'):
                self._songs.append(filename)

    @commands.command()
    async def list(self, ctx):
        if not self._songs:
            await self.boxed_print(ctx, 'No songs! Use "bro download" to download songs')
            return
        i = 0
        string = ''
        for name in self._songs:
            i += 1
            string += str(i) + '. ' + str(name[:-5]) + '\n'
        await self.boxed_print(ctx, string)

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client.is_connected():
            await ctx.message.guild.voice_client.disconnect()

    @commands.command()
    async def play(self, ctx, number):
        status = get(self.client.voice_clients, guild=ctx.guild)
        try:
            if not status and ctx.message.author.voice != None:
                await ctx.message.author.voice.channel.connect()
        except:
            await self.boxed_print(ctx, 'Connect to a voice channel before playing')
        name = self._songs[int(number) - 1]
        song = './music/' + self._songs[int(number) - 1]
        #await ctx.message.channel.send('```Playing: ' + name[:-5] + '```')
        await self.boxed_print(ctx, 'Playing: ' + name[:-5])
        def after_play(error):
            coroutine = ctx.voice_client.disconnect()
            future = run_coroutine_threadsafe(coroutine, self.client.loop)
            try:
                future.result()
            except:
                print('Disconnect has failed. Run "stop" manually', error)
        ctx.message.guild.voice_client.play(discord.FFmpegOpusAudio(song), after = after_play)

    @commands.command()
    async def download(self, ctx, url):
        ydl_opts = {
            'format': 'bestaudio/opus',
            'outtmpl': '/music/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                }],
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            await self.boxed_print(ctx, 'Song downloaded: \n' + info['title'])
        self._tracklist()
        await self.list(ctx)

    @commands.command()
    async def flush(self, ctx):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            for filename in os.scandir('./music'):
                os.remove(filename.path)
        await self.boxed_print(ctx, 'Music folder is now empty')
        self._tracklist()

def setup(client):
    client.add_cog(Music(client))
