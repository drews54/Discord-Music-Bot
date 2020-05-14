import discord
import os
import youtube_dl
from shutil import move
from discord.utils import get
from discord.ext import commands
from asyncio import sleep
# import json

class Music(commands.Cog):
    # _length = {}
    
    def __init__(self, client):
        self.client = client
        if not os.path.exists('./music'): os.mkdir('./music')
    
    @commands.command()
    async def list(self, ctx):
        songs = [ ]
        i = 0
        string = ''
        for filename in os.listdir('./music'):
            if filename.endswith('.mp3'):
                songs.append(filename[:-4])
        for name in songs:
            i += 1
            string += str(i) + ' - ' + str(name) + '\n'
        await ctx.message.channel.send('```' + string + '```')
    
    @commands.command()
    async def stop(self, ctx):
        await ctx.message.guild.voice_client.disconnect()
    
    @commands.command()
    async def play(self, ctx, number):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            await ctx.message.author.voice.channel.connect()
        songs = [ ]
        for filename in os.listdir('./music'):
            if filename.endswith('.mp3'):
                songs.append(filename[:-4])
        name = songs[int(number) - 1]
        song = './music/' + name + '.mp3'
        await ctx.message.channel.send('```Playing: ' + name + '```')
        ctx.message.guild.voice_client.play(discord.FFmpegPCMAudio(song))
        # length = 0
        # with open('./music/lengths', 'r') as lengthsfile:
        #     length = json.load(lengthsfile)[name]
        # await asyncio.sleep(length)
        if ctx.voice_client.is_connected():
            while ctx.voice_client.is_playing():
                await sleep(1)
            await ctx.message.guild.voice_client.disconnect()
    
    @commands.command()
    async def download(self, ctx, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
                }],
        }
    
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            #region length file creation (remove ydl.download(url) before uncommenting)
            # file = ydl.extract_info(url)
            # try:
            #     if file['_type'] == 'playlist':
            #         for data in file['entries']:
            #             self._length[
            #                 str(data['title']).replace(':', ' -') +
            #                 '-' + data['id']] = data['duration']
            # except:
            #     self._length[
            #          str(file['title']).replace(':', ' -') +
            #          '-' + file['id']] = file['duration']
            # with open('./music/lengths', 'w') as lengthsfile:
            #     json.dump(self._length, lengthsfile)
            #endregion
            #region DEBUG
            # with open('./music/lengths', 'r') as testfile:
            #    print(self._length)
            #    print(json.load(testfile))
            #endregion
        for filename in os.listdir('./'):
            if filename.endswith('.mp3'):
                move(filename, './music')
                await ctx.message.channel.send('```Song downloaded:\n' + filename + '```')
        await self.list(ctx)

def setup(client):
    client.add_cog(Music(client))
