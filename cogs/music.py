import discord
import os
import youtube_dl
from discord.utils import get
from discord.ext import commands
from asyncio import run_coroutine_threadsafe

class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._songlist = []
        if os.path.exists('./music'):
            self._update_songlist()
        else:
            os.mkdir('./music')
        self._stop_loop = False

    def _update_songlist(self):
        self._songlist.clear()
        for filename in os.listdir('./music'):
            if filename.endswith('.opus'):
                self._songlist.append(filename)

    async def boxed_print(self, ctx, text):
        await ctx.message.channel.send('```' + text + '```')

    @commands.command(name = 'list', brief = 'Shows songs list')
    async def list_(self, ctx):
        if not self._songlist:
            await self.boxed_print(ctx, 'No songs! Use "bro download" to download songs')
            return
        i = 0
        string = ''
        for name in self._songlist:
            i += 1
            string += str(i) + '. ' + str(name[:-5]) + '\n'
        await self.boxed_print(ctx, string)

    @commands.command(brief = 'Stops playing audio')
    async def stop(self, ctx, loop = ''):
        if loop == 'loop':
            self._stop_loop = True
        elif ctx.voice_client.is_connected():
            await ctx.message.guild.voice_client.disconnect()

    @commands.command(brief = 'Plays song from list')
    async def play(self, ctx, number, loop = ''):
        status = get(self.client.voice_clients, guild=ctx.guild)
        try:
            if not status and ctx.message.author.voice != None:
                await ctx.message.author.voice.channel.connect()
        except:
            await self.boxed_print(ctx, 'Connect to a voice channel before playing')
        name = self._songlist[int(number) - 1]
        song = './music/' + self._songlist[int(number) - 1]
        await self.boxed_print(ctx, 'Playing: ' + name[:-5])
        def after_play(error):
            if loop == 'loop' and not self._stop_loop:
                try:
                    ctx.message.guild.voice_client.play(discord.FFmpegOpusAudio(song), after = after_play)
                except:
                    pass
            else:
                coroutine = ctx.voice_client.disconnect()
                future = run_coroutine_threadsafe(coroutine, self.client.loop)
                try:
                    future.result()
                except:
                    print('Disconnect has failed. Run "stop" manually', error)
        ctx.message.guild.voice_client.play(discord.FFmpegOpusAudio(song), after = after_play)

    @commands.command(brief = 'Downloads audio from YouTube')
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
            self._songlist.append(info['title'])
        self._songlist.sort()
        await self.list_(ctx)

    @commands.command(brief = 'Deletes all your cool songs((')
    async def flush(self, ctx):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            for filename in os.scandir('./music'):
                os.remove(filename.path)
        await self.boxed_print(ctx, 'Music folder is now empty')
        self._songlist.clear()

def setup(client):
    client.add_cog(Music(client))
