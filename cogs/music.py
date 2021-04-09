"""
Music module of the bot.

Uses Discord's commands.Cog as a base class.
"""
import os
import math
import subprocess
import random
from gettext import translation
from asyncio import run_coroutine_threadsafe
import discord
from discord.utils import get
from discord.ext import commands
from youtube_dl import YoutubeDL
from youtube_search import YoutubeSearch

if os.getenv('LANG').casefold().startswith('ru'):
    _ = translation('Discord-Music-Bot', './locale', languages=['ru']).gettext
else:
    _ = translation('Discord-Music-Bot', './locale', languages=['en']).gettext


def boxed_string(text) -> str:
    """Returns passed text string wrapped in triple backticks."""
    return '```' + text + '```'


class Music(commands.Cog):
    """Contains all invokable commands within music module."""

    def __init__(self, client):
        self.client = client
        self._songlist = []
        self._unknown_files = 0
        self._playlist = []
        self.music_path = './music/'
        self.music_ext = '.opus'
        self.prefix = self.client.command_prefix[0]
        self._looped = False
        self.music_volume = 0.05
        if os.path.exists(self.music_path):
            self._songlist, self._unknown_files = update_songlist(
                self.music_path)
        else:
            os.mkdir(self.music_path)
        random.seed()

    @commands.command(name='list', brief=_('Shows songs list'))
    async def list_(self, ctx, page='all'):
        """Displays list of songs page by page."""
        max_page = math.ceil(len(self._songlist)/10)
        if page == 'all':
            string = _('Full song list:\n')
            for i, name in enumerate(self._songlist):
                temp_string = f'{(i + 1)!s}. {name[:-5]!s}\n'
                if len(string + temp_string) > 1994:
                    await ctx.send(boxed_string(string))
                    string = ''
                string += temp_string
        else:
            if self._songlist and not 0 < int(page) <= max_page:
                await ctx.send(boxed_string(_('404 bro, use one of {} existing pages').format(max_page)))
                return
            elif not self._songlist:
                await ctx.send(boxed_string(_('No songs! Use {}download to download songs').format(self.prefix)))
                return
            string = f'Page {page!s} of {max_page!s}:\n'
            for i, name in enumerate(self._songlist):
                if (int)(page) == (i)//10 + 1:
                    string += f'{(i + 1)!s}. {name[:-5]!s}\n'
        await ctx.send(boxed_string(string))
        if self._unknown_files == 1:
            await ctx.send(boxed_string(_('Also there is a file with unknown extension. Use {}convert list to convert your music files to "opus" format.').format(self.prefix)))
        elif self._unknown_files > 1:
            await ctx.send(boxed_string(_('Also there are {} files with unknown extension. Use {}convert list to convert your music files to "opus" format.').format(self._unknown_files, self.prefix)))

    @commands.command(brief=_('Stops playing audio'))
    async def stop(self, ctx, loop=''):
        """Stops current playback or breaks the playback loop."""
        if loop == 'loop':
            self._stop_loop = True
            self._looped = False
            await ctx.send(boxed_string(_('Loop stopped!')))
        elif ctx.voice_client is not None and ctx.voice_client.is_connected():
            await ctx.voice_client.disconnect()
            await self.client.change_presence(status=discord.Status.idle, afk=True)
            self.is_stopped = True
            self._looped = False
        else:
            await ctx.send(boxed_string(_('Nothing is playing')))

    @commands.command(name='play', brief=_('Plays song from list'))
    async def choose_song(self, ctx, *arg):
        """Lets the user play a song from songlist or start a playlist.

        Also used by other methods of Music class which substitute user input.
        """
        playlist = False
        if not arg:
            playlist = True
        if arg and arg[0] == 'loop':
            self._stop_loop = False
            self._looped = True
            await ctx.send(boxed_string(_('Loop activated!')))
            return
        elif arg and arg[0] == 'random':
            number = random.randint(0, len(self._songlist) - 1)
        elif playlist or arg[0] == 'playlist':
            if self._playlist:
                number = self._songlist.index(self._playlist[0]) + 1
                self._playlist.pop(0)
            else:
                await ctx.send(boxed_string(_('Nothing to play!')))
                return
        elif arg and str(arg[0]).isnumeric():
            number = int(arg[0])
        if 'number' in locals():
            self.current_song = {
                'name':   self._songlist[int(number) - 1][:-5],
                'source': self.music_path + self._songlist[int(number) - 1]
            }
            ffmpeg_opts = {}
        else:
            ydl_opts = {'format': 'bestaudio'}
            ffmpeg_opts = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            if arg[0].startswith('http'):
                url = arg[0]
            else:
                searchrequest = ''
                for word in arg:
                    searchrequest += f'{word!s} '
                url = 'https://www.youtube.com' + \
                    YoutubeSearch(searchrequest, max_results=1).to_dict()[
                        0]['url_suffix']
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            self.current_song = {
                'name':   info['title'],
                'source': info['formats'][0]['url']
            }

        if len(arg) > 1 and arg[1] == 'loop' and str(arg[0]).isnumeric():
            self._looped = True
        self._stop_loop = False
        self.is_stopped = False

        await self.player(ctx, ffmpeg_opts)

    async def player(self, ctx, ffmpeg_opts):
        """Core player function."""
        status = get(self.client.voice_clients, guild=ctx.guild)
        try:
            if not status:
                await ctx.voice.channel.connect()
        except AttributeError:
            await ctx.send(boxed_string(_('Connect to a voice channel before playing')))
            return
        await self.changestatus(ctx, self.current_song['name'])

        def after_play(error):
            if self._looped and not self._stop_loop:
                if self.current_song['source'].startswith('http'):
                    param = self.current_song['source']
                else:
                    param = self._songlist.index(
                        self.current_song['name'] + self.music_ext) + 1
            elif self._playlist and not self.is_stopped:
                param = 'playlist'

            if 'param' in locals():
                coroutine = self.choose_song(ctx, param)
            elif not self.is_stopped:
                coroutine = self.stop(ctx)
            if 'coroutine' in locals():
                future = run_coroutine_threadsafe(coroutine, self.client.loop)
                try:
                    future.result()
                except:
                    print(_('Disconnect has failed. Run {}stop manually').format(
                        self.prefix), error)
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
            self.current_song['source'], **ffmpeg_opts), self.music_volume), after=after_play)

    @commands.command(brief=_('Pauses playback'))
    async def pause(self, ctx):
        """Pauses current playback."""
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        else:
            await ctx.send(boxed_string(_('Nothing is playing')))

    @commands.command(brief=_('Resumes playback'))
    async def resume(self, ctx):
        """Resumes playback if it was paused."""
        if ctx.voice_client is not None and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
        else:
            await ctx.send(boxed_string(_('Nothing is paused')))

    @commands.command(brief=_('Changes music volume (0-100)'))
    async def volume(self, ctx, volume=None):
        """Changes playback volume.
        
        For user convenience, the default linear scale is substituted with an exponent.
        """
        if volume is None:
            await ctx.send(boxed_string(_('Volume = {}%').format((math.pow(self.music_volume, math.exp(-1))*100).__trunc__())))
        elif volume.isnumeric() and 0 <= int(volume) <= 100:
            self.music_volume = math.pow(int(volume) / 100, math.exp(1))
            if ctx.voice_client is not None and ctx.voice_client.is_playing():
                ctx.voice_client.source.volume = self.music_volume
            await ctx.send(boxed_string(_('Volume set to {}%').format((math.pow(self.music_volume, math.exp(-1))*100).__trunc__())))
        else:
            await ctx.send(boxed_string(_('Incorrect arguments were given. Only whole values from 0 to 100 are supported.')))

    @commands.command(brief=_('Downloads audio from YouTube'))
    async def download(self, ctx, url):
        """Parses YouTube link passed by user and downloads found audio."""
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
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            self._songlist, self._unknown_files = update_songlist(
                self.music_path)
            name = info['title'].replace('"', "'")
            await ctx.send(boxed_string(_('Song downloaded:\n{}\nSong number: {}').format(name, self._songlist.index(name + ".opus") + 1)))

    @commands.command(brief=_('Removes a song selected from the list'))
    async def remove(self, ctx, number=0):
        """Removes a song's data and file from songlist and music directory."""
        if 1 <= int(number) <= len(self._songlist):
            song = self._songlist.pop(int(number) - 1)
            try:
                os.remove(self.music_path + song)
                await ctx.send(boxed_string(_('Song {} has been deleted').format(song[:-5])))
            except PermissionError:
                await ctx.send(boxed_string(_('Unable to delete song file, probably because it is being played right now.')))
            except FileNotFoundError:
                await ctx.send(boxed_string(_('Unable to delete song file as it no longer exists.')))
        else:
            await ctx.send(boxed_string(_('Select an existing song from the list')))

    @commands.command(brief=_('Flushes the music directory'))
    async def flush(self, ctx):
        """Removes all files from music directory."""
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            for filename in os.scandir(self.music_path):
                os.remove(filename.path)
            await ctx.send(boxed_string(_('Music folder is now empty')))
        self._songlist.clear()

    @commands.command(brief=_('Converts music files to opus format'))
    async def convert(self, ctx, arg, ext='mp3'):
        if arg == 'list':
            self._filelist = update_songlist(self.music_path, ext)[0]
            if not self._filelist:
                await ctx.send(boxed_string(_('No files to convert')))
                return
            i = 0
            string = ''
            for name in self._filelist:
                i += 1
                string += f'{i!s}. {name!s}\n'
            string = string + \
                _('Use {}convert [number] to convert files from the list to ".opus" format.').format(
                    self.prefix)
            await ctx.send(boxed_string(string))
        elif (1 <= int(arg) <= len(self._filelist)):
            file = self._filelist[int(arg) - 1]
            await ctx.send(boxed_string(_('Performing conversion {} to ".opus" format...').format(file)))
            cmd = f'ffmpeg -i "music/{file}" "music/{file[:-len(ext)]}opus"'
            subprocess.call(cmd, shell=True)
            os.remove('./music/' + file)
            self._songlist.append(f'{file[:-len(ext)]}opus')
            self._songlist.sort()
            self._unknown_files -= 1
            await ctx.send(boxed_string(_('Conversion successful!')))
            await self.list_(ctx)
        else:
            await ctx.send(boxed_string(_('Select an existing file from the list or use {}convert list.').format(self.prefix)))

    @commands.command(brief=_('Use to search videos in YT'))
    async def search(self, ctx, *key):
        """Searches YouTube videos by user-provided string."""
        i = 0
        self._urlslist = []
        searchrequest = ''
        string = _('Search results:\n')
        for word in key:
            searchrequest += f'{word!s} '
        searchlist = YoutubeSearch(searchrequest, max_results=5).to_dict()
        for video in searchlist:
            i += 1
            self._urlslist.append(video['url_suffix'])
            string += f'{i!s}. {video["title"]}\n'
        string += _('Use {}download <number> to download song from list.').format(self.prefix)
        await ctx.send(boxed_string(string))

    @commands.command(brief=_('Use with <add/del/clear> + song number to edit the current playlist.'))
    async def playlist(self, ctx, action='show', song_number=None):
        """Performs actions with a playlist."""
        # TODO: write a bit more detailed description of what playlist() does.
        if action == 'show':
            string = ''
            i = 0
            if self._playlist:
                for song in self._playlist:
                    i += 1
                    string += f'{i}. {song[:-5]}\n'
            else:
                string = _('Playlist is empty')
            await ctx.send(boxed_string(string))

        elif action == 'add':
            if song_number == 'random':
                song_number = random.randint(0, len(self._songlist) - 1)
            self._playlist.append(self._songlist[int(song_number) - 1])
            await ctx.send(boxed_string(_('«‎{}»‎ added to queue.').format(self._songlist[int(song_number) - 1][:-5])))

        elif action == 'del':
            await ctx.send(boxed_string(_('Song «‎{}»‎ has been removed from queue').format(self._playlist[int(song_number) - 1][:-5])))
            self._playlist.pop(int(song_number) - 1)

        elif action == 'clear':
            self._playlist.clear()
            await ctx.send(boxed_string(_('Playlist is cleared.')))

        elif action == 'random':
            for i in range(int(song_number)):
                number = random.randint(0, len(self._songlist) - 1)
                self._playlist.append(self._songlist[int(number) - 1])
                await ctx.send(boxed_string(_('«‎{}»‎ added to queue.').format(self._songlist[int(number) - 1][:-5])))
            if ctx.voice_client is not None and ctx.voice_client.is_playing():
                pass
            else:
                await self.choose_song(ctx, 'playlist')

    @commands.command(brief=_('Use to skip current song in playlist.'))
    async def skip(self, ctx, quantity=1):
        """Skips a provided amount of songs in a playlist."""
        i = 0
        while i < quantity - 1:
            if self._playlist:
                self._playlist.pop(0)
            i += 1
        if ctx.voice_client is not None and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()

    @commands.command(hidden=True)
    async def changestatus(self, ctx, status):
        """Changes bot's status on Discord and displays current song playing."""
        await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status))
        await ctx.send(boxed_string(_('Playing: ') + status))


def update_songlist(music_path, ext='opus'):
    """Updates songlist variable in Music class. (will be deprecated)"""
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
