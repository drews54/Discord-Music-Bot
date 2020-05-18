import discord
import youtube_dl
import os, math, subprocess
from discord.utils import get
from discord.ext import commands
from asyncio import run_coroutine_threadsafe
from youtube_search import YoutubeSearch

class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._songlist = []
        self._unknown_files = 0
        self._music_path = './music/'
        self.prefix = self.client.command_prefix[0]
        if os.path.exists(self._music_path):
            self._songlist, self._unknown_files = update_songlist()
        else:
            os.mkdir(self._music_path)

    async def boxed_print(self, ctx, text):
        await ctx.message.channel.send('```' + text + '```')

    @commands.command(name = 'list', brief = 'Shows songs list')
    async def list_(self, ctx, page = 1):
        max_page = math.ceil(len(self._songlist)/10)
        if self._songlist and not 0 < page <= max_page:
            await self.boxed_print(ctx, f'404 bro, use one of {max_page!s} existing pages')
            return
        elif not self._songlist:
            await self.boxed_print(ctx, f'No songs! Use {self.prefix}download to download songs')
            return
        i = 0
        string = f'Page {page!s} of {max_page!s}:\n'
        for name in self._songlist:
            i += 1
            if page == (i - 1)//10 + 1:
                string += f'{i!s}. {name[:-5]!s}\n'
        await self.boxed_print(ctx, string)
        if self._unknown_files == 1:
            await self.boxed_print(ctx, f'Also there is a file with unknown extension. Use {self.prefix}convert list to convert your music files to "opus" format.')
        elif self._unknown_files > 1:
            await self.boxed_print(ctx, f'Also there are {self._unknown_files!s} files with unknown extension. Use {self.prefix}convert list to convert your music files to "opus" format.')

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
            if not status:
                await ctx.message.author.voice.channel.connect()
        except AttributeError:
            await self.boxed_print(ctx, 'Connect to a voice channel before playing')
            return
        name = self._songlist[int(number) - 1]
        song = self._music_path + self._songlist[int(number) - 1]
        await self.boxed_print(ctx, 'Playing: ' + name[:-5])
        self._stop_loop = False
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
                    print(f'Disconnect has failed. Run {self.prefix}stop manually', error)
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

        if not url.startswith('http'):
            url = f'https://www.youtu.be{self._urlslist[int(url) - 1]}'
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            await self.boxed_print(ctx, 'Song downloaded: \n' + info['title'])
        self._songlist, self._unknown_files = update_songlist()
        await self.list_(ctx)

    @commands.command(brief = 'Removes a song selected from the list')
    async def remove(self, ctx, number = 0):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            if (1 <= int(number) <= len(self._songlist)):
                song = self._songlist.pop(int(number) - 1)
                os.remove(self._music_path + song)
                await self.boxed_print(ctx, f'Song {song[:-5]} has been deleted')
                await self.list_(ctx)
            else:
                await self.boxed_print(ctx, 'Select an existing song from the list')

    @commands.command(brief = 'Flushes the music directory')
    async def flush(self, ctx):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            for filename in os.scandir(self._music_path):
                os.remove(filename.path)
            await self.boxed_print(ctx, 'Music folder is now empty')
        self._songlist.clear()

    @commands.command(brief = 'Converts music file to opus format')
    async def convert(self, ctx, arg, ext = 'mp3'):
        if arg == 'list':
            self._filelist = update_songlist(ext)[0]
            if not self._filelist:
                await self.boxed_print(ctx, 'No files to convert')
                return
            i = 0
            string = ''
            for name in self._filelist:
                i += 1
                string += f'{i!s}. {name!s}\n'
            string = string + f'Use {self.prefix}convert [number] to convert files from list to "opus" format.'
            await self.boxed_print(ctx, string)
        elif (1 <= int(arg) <= len(self._filelist)):
            file = self._filelist[int(arg) - 1]
            await self.boxed_print(ctx, f'Performing convertation {file} to ".opus" format...')
            cmd = f'ffmpeg -i "music/{file}" "music/{file[:-len(ext)]}opus"'
            subprocess.call(cmd, shell=True)
            os.remove('./music/' + file)
            self._songlist.append(f'{file[:-len(ext)]}opus')
            self._songlist.sort()
            self._unknown_files -= 1
            await self.boxed_print(ctx, 'Converted!')
            await self.list_(ctx)
        else:
            await self.boxed_print(ctx, f'Select an existing file from the list or use {self.prefix}convert list.')

    @commands.command(brief = 'Use to search videos in YT')
    async def search(self, ctx, *key):
        i = 0
        self._urlslist = []
        searchrequest = ''
        string = 'Search results:\n'
        for word in key:
            searchrequest += f'{word!s} '
        searchlist = YoutubeSearch(searchrequest, max_results = 5).to_dict()
        for video in searchlist:
            i += 1
            self._urlslist.append(video['link'])
            string += f'{i!s}. {video["title"]}\n'
        string += f'Use {self.prefix}download <number> to download song from list.'
        await self.boxed_print(ctx, string)


def update_songlist(ext = 'opus', music_path = './music/'):
    songlist = []
    unknown_files = 0
    for filename in os.listdir(music_path):
        if filename.endswith(ext):
            songlist.append(filename)
        else:
            unknown_files += 1
    return songlist, unknown_files

def setup(client):
    client.add_cog(Music(client))
