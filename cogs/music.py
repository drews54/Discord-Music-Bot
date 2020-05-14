import discord
import os
import youtube_dl
from discord.utils import get
from discord.ext import commands
from asyncio import run_coroutine_threadsafe

class Music(commands.Cog):

    def __init__(self, client):
        self.client = client
        if not os.path.exists('./music'): os.mkdir('./music')

    @commands.command()
    async def list(self, ctx):
        songs = [ ]
        i = 0
        string = ''
        for filename in os.listdir('./music'):
            if filename.endswith('.opus'):
                songs.append(filename[:-5])
        for name in songs:
            i += 1
            string += str(i) + '. ' + str(name) + '\n'
        await ctx.message.channel.send('```' + string + '```')
    
    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client.is_connected():
            await ctx.message.guild.voice_client.disconnect()
    
    @commands.command()
    async def play(self, ctx, number):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            await ctx.message.author.voice.channel.connect()
        songs = [ ]
        for filename in os.listdir('./music'):
            if filename.endswith('.opus'):
                songs.append(filename[:-5])
        name = songs[int(number) - 1]
        song = './music/' + name + '.opus'
        await ctx.message.channel.send('```Playing: ' + name + '```')
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
            await ctx.message.channel.send('```Song downloaded: \n' + info['title'] + '```')
        await self.list(ctx)
    
    @commands.command()
    async def flush(self, ctx):
        if not ctx.voice_client.is_connected():
            for filename in os.scandir('./music'):
                os.remove(filename.path)
        await ctx.message.channel.send('```Music folder is now empty```')

def setup(client):
    client.add_cog(Music(client))
