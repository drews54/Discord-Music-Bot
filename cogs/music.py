import discord
import youtube_dl
import os, math, subprocess, random, gettext
from discord.utils import get
from discord.ext import commands
from asyncio import run_coroutine_threadsafe
from youtube_search import YoutubeSearch

class Music(commands.Cog):
    langRU = gettext.translation('Discord-Music-Bot', './locale', languages=['ru'])
    _ = langRU.gettext
    
    def __init__(self, client):
        self.client = client
        self._songlist = []
        self._unknown_files = 0
        self._playlist = []
        self.music_path = './music/'
        self.prefix = self.client.command_prefix[0]
        self._looped = False
        self.music_volume = 0.05
        if os.path.exists(self.music_path):
            self._songlist, self._unknown_files = update_songlist(self.music_path)
        else:
            os.mkdir(self.music_path)
        random.seed()

    async def boxed_print(self, ctx, text):
        await ctx.send('```' + text + '```')

    @commands.command(name = 'list', brief = _('Shows songs list'))
    async def list_(self, ctx, page = 'all'):
        max_page = math.ceil(len(self._songlist)/10)
        if page == 'all':
            string = self._('Full song list:\n')
            for i, name in enumerate(self._songlist):
                temp_string = f'{(i + 1)!s}. {name[:-5]!s}\n'
                if len(string + temp_string) > 2000:
                    await self.boxed_print(ctx, string)
                    string = ''
                string += temp_string
        else:
            if self._songlist and not 0 < page <= max_page:
                await self.boxed_print(ctx, self._('404 bro, use one of {} existing pages').format(max_page))
                return
            elif not self._songlist:
                await self.boxed_print(ctx, self._('No songs! Use {}download to download songs').format(self.prefix))
                return
            string = f'Page {page!s} of {max_page!s}:\n'
            for i, name in self._songlist:
                if page == (i)//10 + 1:
                    string += f'{(i + 1)!s}. {name[:-5]!s}\n'
        await self.boxed_print(ctx, string)
        if self._unknown_files == 1:
            await self.boxed_print(ctx, self._('Also there is a file with unknown extension. Use {}convert list to convert your music files to "opus" format.').format(self.prefix))
        elif self._unknown_files > 1:
            await self.boxed_print(ctx, self._('Also there are {} files with unknown extension. Use {}convert list to convert your music files to "opus" format.').format(self._unknown_files, self.prefix))

    @commands.command(brief = _('Stops playing audio'))
    async def stop(self, ctx, loop = ''):
        if loop == 'loop':
            self._stop_loop = True
            self._looped = False
            await self.boxed_print(ctx, self._('Loop stopped!'))
        elif ctx.voice_client is not None and ctx.voice_client.is_connected():
            await ctx.voice_client.disconnect()
            await self.client.change_presence(status = discord.Status.idle, afk = True)
            self.is_stopped = True
            self._looped = False          
        else:
            await self.boxed_print(ctx, self._('Nothing is playing'))

    @commands.command(brief = _('Plays song from list'))
    async def play(self, ctx, number='playlist', loop = ''):
        if number == 'loop':
            self._stop_loop = False
            self._looped = True
            await self.boxed_print(ctx, self._('Loop activated!'))
            return
        elif number == 'random':
            number = random.randint(0, len(self._songlist) - 1)
        elif number == 'playlist':
            if self._playlist:
                number = self._songlist.index(self._playlist[0]) + 1
                self._playlist.pop(0)
            else:
                await self.boxed_print(ctx, self._('Nothing to play!'))
                return
        elif number.startswith('http'):
            ydl_opts = {'format':'bestaudio'}
            ffmpeg_opts = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
                'options': '-vn'
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(number, download=False)
            song = info['formats'][0]['url']
            name = info['title']
            await self.changestatus(ctx, name)
        if (str)(number).isnumeric():
            name = self._songlist[int(number) - 1]
            song = self.music_path + self._songlist[int(number) - 1]
            ffmpeg_opts = {}
            await self.changestatus(ctx, name[:-5])

        if loop == 'loop':
            self._looped = True

        status = get(self.client.voice_clients, guild=ctx.guild)
        try:
            if not status:
                await ctx.message.author.voice.channel.connect()
        except AttributeError:
            await self.boxed_print(ctx, self._('Connect to a voice channel before playing'))
            return

        self._stop_loop = False
        self.is_stopped = False
        def after_play(error):
            if self._looped and not self._stop_loop:
                try:
                    ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song, **ffmpeg_opts), self.music_volume), after = after_play)
                except:
                    pass
            elif self._playlist:
                try:
                    next_song = self.music_path + self._playlist[0]
                    coroutine = self.changestatus(ctx, self._playlist[0][:-5])

                    run_coroutine_threadsafe(coroutine, self.client.loop).result()
                    self._playlist.pop(0)
                    ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(next_song, **ffmpeg_opts), self.music_volume), after = after_play)
                except:
                    print('Error in playlist')
            elif not self.is_stopped:
                coroutine = self.stop(ctx)
                future = run_coroutine_threadsafe(coroutine, self.client.loop)
                try:
                    future.result()
                except:
                    print(self._('Disconnect has failed. Run {}stop manually').format(self.prefix), error)

        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song, **ffmpeg_opts), self.music_volume), after = after_play)

    @commands.command(brief = _('Pauses playback'))
    async def pause(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        else:
            await self.boxed_print(ctx, self._('Nothing is playing'))
                
    @commands.command(brief = _('Resumes playback'))
    async def resume(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
        else:
            await self.boxed_print(ctx, self._('Nothing is paused'))

    @commands.command(brief = _('Changes music volume (0-100)'))
    async def volume(self, ctx, volume=None):
        if volume == None:
            await self.boxed_print(ctx, self._('Volume = {}%').format((math.pow(self.music_volume, math.exp(-1)) * 100).__trunc__()))
        elif volume.isnumeric() and 0 <= int(volume) <= 100:
            self.music_volume = math.pow(int(volume) / 100, math.exp(1))
            if ctx.voice_client is not None and ctx.voice_client.is_playing():
                ctx.voice_client.source.volume = self.music_volume
            await self.boxed_print(ctx, self._('Volume set to {}%').format((math.pow(self.music_volume, math.exp(-1))*100).__trunc__()))
        else:
            await self.boxed_print(ctx, self._('Incorrect arguments were given. Only whole values from 0 to 100 are supported.'))

    @commands.command(brief = _('Downloads audio from YouTube'))
    async def download(self, ctx, url):
        ydl_opts = {
            'format': 'bestaudio/opus',
            'outtmpl': f'{self.music_path}%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                }],
        }

        if not url.startswith('http'):
            url = f'https://www.youtube.com{self._urlslist[int(url) - 1]}'
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            self._songlist, self._unknown_files = update_songlist(self.music_path)
            name = info['title'].replace('"', "'")
            await self.boxed_print(ctx, self._('Song downloaded:\n{}\nSong number: {}').format(name, self._songlist.index(name + ".opus") + 1))


    @commands.command(brief = _('Removes a song selected from the list'))
    async def remove(self, ctx, number = 0):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            if (1 <= int(number) <= len(self._songlist)):
                song = self._songlist.pop(int(number) - 1)
                os.remove(self.music_path + song)
                await self.boxed_print(ctx, self._('Song {} has been deleted').format(song[:-5]))
            else:
                await self.boxed_print(ctx, self._('Select an existing song from the list'))

    @commands.command(brief = _('Flushes the music directory'))
    async def flush(self, ctx):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            for filename in os.scandir(self.music_path):
                os.remove(filename.path)
            await self.boxed_print(ctx, self._('Music folder is now empty'))
        self._songlist.clear()

    @commands.command(brief = _('Converts music files to opus format'))
    async def convert(self, ctx, arg, ext = 'mp3'):
        if arg == 'list':
            self._filelist = update_songlist(self.music_path, ext)[0]
            if not self._filelist:
                await self.boxed_print(ctx, self._('No files to convert'))
                return
            i = 0
            string = ''
            for name in self._filelist:
                i += 1
                string += f'{i!s}. {name!s}\n'
            string = string + self._('Use {}convert [number] to convert files from the list to ".opus" format.').format(self.prefix)
            await self.boxed_print(ctx, string)
        elif (1 <= int(arg) <= len(self._filelist)):
            file = self._filelist[int(arg) - 1]
            await self.boxed_print(ctx, self._('Performing conversion {} to ".opus" format...').format(file))
            cmd = f'ffmpeg -i "music/{file}" "music/{file[:-len(ext)]}opus"'
            subprocess.call(cmd, shell=True)
            os.remove('./music/' + file)
            self._songlist.append(f'{file[:-len(ext)]}opus')
            self._songlist.sort()
            self._unknown_files -= 1
            await self.boxed_print(ctx, self._('Conversion successful!'))
            await self.list_(ctx)
        else:
            await self.boxed_print(ctx, self._('Select an existing file from the list or use {}convert list.').format(self.prefix))

    @commands.command(brief = _('Use to search videos in YT'))
    async def search(self, ctx, *key):
        i = 0
        self._urlslist = []
        searchrequest = ''
        string = self._('Search results:\n')
        for word in key:
            searchrequest += f'{word!s} '
        searchlist = YoutubeSearch(searchrequest, max_results = 5).to_dict()
        for video in searchlist:
            i += 1
            self._urlslist.append(video['url_suffix'])
            string += f'{i!s}. {video["title"]}\n'
        string += self._('Use {}download <number> to download song from list.').format(self.prefix)
        await self.boxed_print(ctx, string)

    @commands.command(brief = _('Use with <add/del/clear> + song number to edit the current playlist.'))
    async def playlist(self, ctx, action = 'show', song_number = None):
        if action == 'show':
            string = ''
            i = 0
            if self._playlist:
                for song in self._playlist:
                    i += 1
                    string += f'{i}. {song[:-5]}\n'
            else:
                string = self._('Playlist is empty')
            await self.boxed_print(ctx, string)
    
        elif action == 'add':
            if song_number == 'random':
                song_number = random.randint(0, len(self._songlist) - 1)
            self._playlist.append(self._songlist[int(song_number) - 1])
            await self.boxed_print(ctx, self._('«‎{}»‎ added to queue.').format(self._songlist[int(song_number) - 1][:-5]))

        elif action == 'del':
            await self.boxed_print(ctx, self._('Song «‎{}»‎ has been removed from queue').format(self._playlist[int(song_number) - 1][:-5]))
            self._playlist.pop(int(song_number) - 1)

        elif action == 'clear':
            self._playlist.clear()
            await self.boxed_print(ctx, self._('Playlist is cleared.'))

        elif action == 'random':
            for i in range(int(song_number)):
                number = random.randint(0, len(self._songlist) - 1)
                self._playlist.append(self._songlist[int(number) - 1])
                await self.boxed_print(ctx, self._('«‎{}»‎ added to queue.').format(self._songlist[int(number) - 1][:-5]))
            if ctx.voice_client is not None and ctx.voice_client.is_playing():
                pass
            else:
                await self.play(ctx)

    @commands.command(hidden = True)
    async def changestatus(self, ctx, status):
        await self.client.change_presence(activity = discord.Activity(type=discord.ActivityType.listening, name=status))
        await self.boxed_print(ctx, self._('Playing: ') + status)

def update_songlist(music_path, ext = 'opus'):
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
