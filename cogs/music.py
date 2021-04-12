"""
Music module of the bot.

Uses Discord's commands.Cog as a base class.
"""
import os
import math
import random
from gettext import translation
from asyncio import run_coroutine_threadsafe, CancelledError
import discord
from discord.utils import get
from discord.ext import commands
from youtube_dl import YoutubeDL
from youtube_search import YoutubeSearch

if os.getenv('LANG').casefold().startswith('ru'):
    _ = translation('Discord-Music-Bot', './locale', languages=['ru']).gettext
else:
    _ = translation('Discord-Music-Bot', './locale', languages=['en']).gettext


def boxed_string(text: str) -> str:
    """Returns passed text string wrapped in triple backticks."""
    return '```' + text + '```'


# pylint: disable=C0103
_songlist = []
_unknown_files = 0
_playlist = []
MUSIC_PATH = './music/'
MUSIC_EXT = '.opus'
# pylint: enable=C0103


def update_songlist():
    """Updates songlist variable in Music class. (will be deprecated)"""
    _songlist.clear()
    for filename in os.listdir(MUSIC_PATH):
        if filename.endswith(MUSIC_EXT):
            _songlist.append(filename)
        else:
            _unknown_files += 1


if os.path.exists(MUSIC_PATH):
    update_songlist()
else:
    os.mkdir(MUSIC_PATH)
random.seed()


class Music(commands.Cog):
    """Contains all invokable commands within music module."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.current_song = {}
        self.is_stopped = False
        self._stop_loop = False
        self._looped = False
        self.music_volume = 0.05
        self._urlslist = []

    @commands.command(name='list', brief=_('Shows songs list'))
    async def list_(self, ctx: commands.Context, page='all'):
        """Displays list of songs page by page."""
        max_page = math.ceil(len(_songlist)/10)
        if page == 'all':
            string = _('Full song list:\n')
            for i, name in enumerate(_songlist):
                temp_string = f'{(i + 1)!s}. {name[:-5]!s}\n'
                if len(string + temp_string) > 1994:
                    await ctx.send(boxed_string(string))
                    string = ''
                string += temp_string
        else:
            if _songlist and not 0 < int(page) <= max_page:
                await ctx.send(boxed_string(_('404 bro, use one of {} existing pages').format(max_page)))
                return
            elif not _songlist:
                await ctx.send(boxed_string(_('No songs! Use {}download to download songs').format(self.bot.command_prefix)))
                return
            string = f'Page {page!s} of {max_page!s}:\n'
            for i, name in enumerate(_songlist):
                if (int)(page) == (i)//10 + 1:
                    string += f'{(i + 1)!s}. {name[:-5]!s}\n'
        await ctx.send(boxed_string(string))
        if _unknown_files == 1:
            await ctx.send(boxed_string(_('Also there is a file with unknown extension. Use {}convert list to convert your music files to "opus" format.').format(self.bot.command_prefix)))
        elif _unknown_files > 1:
            await ctx.send(boxed_string(_('Also there are {} files with unknown extension. Use {}convert list to convert your music files to "opus" format.').format(_unknown_files, self.bot.command_prefix)))

    @commands.command(brief=_('Stops playing audio'))
    async def stop(self, ctx: commands.Context, loop=''):
        """Stops current playback or breaks the playback loop."""
        if loop == 'loop':
            self._stop_loop = True
            self._looped = False
            await ctx.send(boxed_string(_('Loop stopped!')))
        elif ctx.voice_client is not None and ctx.voice_client.is_connected():
            await ctx.voice_client.disconnect()
            await self.bot.change_presence(status=discord.Status.idle, afk=True)
            self.is_stopped = True
            self._looped = False
        else:
            await ctx.send(boxed_string(_('Nothing is playing')))

    @commands.command(name='play', brief=_('Plays song from list'))
    async def choose_song(self, ctx: commands.Context, *, arg: str = ''):
        """Lets the user play a song from songlist or start a playlist.

        Also used by other methods of Music class which substitute user input.
        """
        playlist = False
        if not arg:
            playlist = True
        if arg and arg.startswith('loop'):
            self._stop_loop = False
            self._looped = True
            await ctx.send(boxed_string(_('Loop activated!')))
            return
        elif arg and arg.startswith('random'):
            number = random.randint(0, len(_songlist) - 1)
        elif playlist or arg.startswith('playlist'):
            if _playlist:
                number = _songlist.index(_playlist[0]) + 1
                _playlist.pop(0)
            else:
                await ctx.send(boxed_string(_('Nothing to play!')))
                return
        elif arg and arg.split(maxsplit=1)[0].isnumeric():
            number = int(arg.split(maxsplit=1)[0])
        if 'number' in locals():
            self.current_song = {
                'name':   _songlist[int(number) - 1][:-5],
                'source': MUSIC_PATH + _songlist[int(number) - 1]
            }
            ffmpeg_opts = {}
        else:
            ydl_opts = {'format': 'bestaudio'}
            ffmpeg_opts = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            if arg.startswith('http'):
                url = arg
            else:
                searchrequest = arg
                url = 'https://www.youtube.com' + \
                    YoutubeSearch(searchrequest, max_results=1).to_dict()[
                        0]['url_suffix']  # type: ignore
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            self.current_song = {
                'name':   info['title'],
                'source': info['formats'][0]['url']
            }
        arg_split = arg.split()
        if len(arg_split) > 1 and arg_split[1] == 'loop' and str(arg_split[0]).isnumeric():
            self._looped = True
        self._stop_loop = False
        self.is_stopped = False

        await self.player(ctx, ffmpeg_opts)

    async def player(self, ctx: commands.Context, ffmpeg_opts):
        """Core player function."""
        status = get(self.bot.voice_clients, guild=ctx.guild)
        try:
            if not status:
                await ctx.author.voice.channel.connect()  # type: ignore
        except AttributeError:
            await ctx.send(boxed_string(_('Connect to a voice channel before playing')))
            return
        await self.changestatus(ctx, self.current_song['name'])

        def after_play(error):
            if self._looped and not self._stop_loop:
                if self.current_song['source'].startswith('http'):
                    param = self.current_song['source']
                else:
                    param = _songlist.index(
                        self.current_song['name'] + MUSIC_EXT) + 1
            elif _playlist and not self.is_stopped:
                param = 'playlist'

            if 'param' in locals():
                coroutine = self.choose_song(ctx, arg=str(param))
            elif not self.is_stopped:
                coroutine = self.stop(ctx)
            if 'coroutine' in locals():
                future = run_coroutine_threadsafe(coroutine, self.bot.loop)
                try:
                    future.result()
                except CancelledError:
                    print(_('Disconnect has failed. Run {}stop manually').format(
                        self.bot.command_prefix), error)
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
            self.current_song['source'], **ffmpeg_opts), self.music_volume), after=after_play)

    @commands.command(brief=_('Pauses playback'))
    async def pause(self, ctx: commands.Context):
        """Pauses current playback."""
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        else:
            await ctx.send(boxed_string(_('Nothing is playing')))

    @commands.command(brief=_('Resumes playback'))
    async def resume(self, ctx: commands.Context):
        """Resumes playback if it was paused."""
        if ctx.voice_client is not None and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
        else:
            await ctx.send(boxed_string(_('Nothing is paused')))

    @commands.command(brief=_('Changes music volume (0-100)'))
    async def volume(self, ctx: commands.Context, volume=None):
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
    async def download(self, ctx: commands.Context, url):
        """Parses YouTube link passed by user and downloads found audio."""
        ydl_opts = {
            'format': 'bestaudio/opus',
            'outtmpl': f'{MUSIC_PATH}%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
            }],
        }

        if not url.startswith('http'):
            url = f'https://www.youtube.com{self._urlslist[int(url) - 1]}'
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            update_songlist()
            name = info['title'].replace('"', "'")
            await ctx.send(boxed_string(_('Song downloaded:\n{}\nSong number: {}').format(name, _songlist.index(name + ".opus") + 1)))

    @commands.command(brief=_('Removes a song selected from the list'))
    async def remove(self, ctx: commands.Context, number=0):
        """Removes a song's data and file from songlist and music directory."""
        if 1 <= int(number) <= len(_songlist):
            song = _songlist.pop(int(number) - 1)
            try:
                os.remove(MUSIC_PATH + song)
                await ctx.send(boxed_string(_('Song {} has been deleted').format(song[:-5])))
            except PermissionError:
                await ctx.send(boxed_string(_('Unable to delete song file, probably because it is being played right now.')))
            except FileNotFoundError:
                await ctx.send(boxed_string(_('Unable to delete song file as it no longer exists.')))
        else:
            await ctx.send(boxed_string(_('Select an existing song from the list')))

    @commands.command(brief=_('Flushes the music directory'))
    async def flush(self, ctx: commands.Context):
        """Removes all files from music directory."""
        status = get(self.bot.voice_clients, guild=ctx.guild)
        if not status:
            for filename in os.scandir(MUSIC_PATH):
                os.remove(filename.path)
            await ctx.send(boxed_string(_('Music folder is now empty')))
        _songlist.clear()

    @commands.command(brief=_('Use to search videos in YT'))
    async def search(self, ctx: commands.Context, *key):
        """Searches YouTube videos by user-provided string."""
        i = 0
        self._urlslist.clear()
        searchrequest = ''
        string = _('Search results:\n')
        for word in key:
            searchrequest += f'{word!s} '
        searchlist = YoutubeSearch(searchrequest, max_results=5).to_dict()
        for video in searchlist:
            i += 1
            self._urlslist.append(video['url_suffix'])  # type: ignore
            string += f'{i!s}. {video["title"]}\n'  # type: ignore
        string += _('Use {}download <number> to download song from list.').format(
            self.bot.command_prefix)
        await ctx.send(boxed_string(string))

    @commands.command(brief=_('Use with <add/del/clear> + song number to edit the current playlist.'))
    async def playlist(self, ctx: commands.Context, action='show', song_number=None):
        """Performs actions with a playlist."""
        # TODO: write a bit more detailed description of what playlist() does.
        if action == 'show':
            string = ''
            i = 0
            if _playlist:
                for song in _playlist:
                    i += 1
                    string += f'{i}. {song[:-5]}\n'
            else:
                string = _('Playlist is empty')
            await ctx.send(boxed_string(string))

        elif action == 'add':
            if song_number == 'random':
                song_number = random.randint(0, len(_songlist) - 1)
            _playlist.append(_songlist[int(song_number) - 1])
            await ctx.send(boxed_string(_('«‎{}»‎ added to queue.').format(_songlist[int(song_number) - 1][:-5])))

        elif action == 'del':
            await ctx.send(boxed_string(_('Song «‎{}»‎ has been removed from queue').format(_playlist[int(song_number) - 1][:-5])))
            _playlist.pop(int(song_number) - 1)

        elif action == 'clear':
            _playlist.clear()
            await ctx.send(boxed_string(_('Playlist is cleared.')))

        elif action == 'random':
            for i in range(int(song_number)):
                number = random.randint(0, len(_songlist) - 1)
                _playlist.append(_songlist[int(number) - 1])
                await ctx.send(boxed_string(_('«‎{}»‎ added to queue.').format(_songlist[int(number) - 1][:-5])))
            if ctx.voice_client is not None and ctx.voice_client.is_playing():
                pass
            else:
                await self.choose_song(ctx, arg='playlist')

    @commands.command(brief=_('Use to skip current song in playlist.'))
    async def skip(self, ctx: commands.Context, quantity=1):
        """Skips a provided amount of songs in a playlist."""
        i = 0
        while i < quantity - 1:
            if _playlist:
                _playlist.pop(0)
            i += 1
        if ctx.voice_client is not None and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()

    @commands.command(hidden=True)
    async def changestatus(self, ctx: commands.Context, status):
        """Changes bot's status on Discord and displays current song playing."""
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status))
        await ctx.send(boxed_string(_('Playing: ') + status))

    @commands.command(brief=_('Plays song, which is displayed in your Spotify status'))
    async def spotify(self, ctx: commands.Context):
        """Checks user's status for Spotify integration and, if it exists, searches the currently playing song on YouTube.

        Invokes choose_song(artist + name) which plays the first match of the search query."""
        for activity in ctx.author.activities:  # type: ignore
            if isinstance(activity, discord.Spotify):
                await self.choose_song(ctx, arg=f'{activity.artist} - {activity.title}')
                return
        await ctx.send(boxed_string('Can\'t detect your Spotify status.'))


def setup(bot: commands.Bot):
    """Initializes Music as a cog of the Bot."""
    bot.add_cog(Music(bot))
