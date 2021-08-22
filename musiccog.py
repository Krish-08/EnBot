
import discord

from discord.ext import commands

from functools import partial

from async_timeout import timeout

import youtube_dl
import asyncio



youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' 
}

ffmpeg_options = {
  'before_options': '-nostdin',
  'options': '-vn'
}


ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5,requester):
        super().__init__(source)
        self.requester=requester
        #self.data = data
        self.title = data.get('title')
        self.url =data.get("url")

    def __getitem__(self, item: str):
      return self.__getattribute__(item)

    @classmethod
    async def from_url(cls, ctx,url,search:str, *, loop=None, download=False):
        loop = loop or asyncio.get_event_loop()
        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None,to_run)
        
        if 'entries' in data:
          data = data['entries'][0]
        embed = discord.Embed(title="", description=f"Queued [{data['title']}]({data['url']}) [{ctx.author.mention}]", color=discord.Color.green())
        await ctx.send(embed=embed)
        
        if download:
          source= ytdl.prepare_filename(data)
        else:
          return {'url': data['url'], 'requester': ctx.author, 'title': data['title']}
        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    
    @classmethod
    async def streamFunction(cls,data,*,loop):
      loop = loop or asyncio.get_event_loop()
      requester = data['requester']

      to_run = partial(ytdl.extract_info, url=data['url'], download=False)
      data = await loop.run_in_executor(None, to_run)
      return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


class MusicPlayer:
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
              
                try:
                    source = await YTDLSource.streamFunction(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            embed = discord.Embed(title="Now playing", description=f"[{source.title}]({source.url}) [{source.requester.mention}]", color=discord.Color.green())
            self.np = await self._channel.send(embed=embed)
            await self.next.wait()

           
            source.cleanup()
            self.current = None

    def destroy(self, guild):
        return self.bot.loop.create_task(self._cog.cleanup(guild))

class MusicCommands(commands.cog):
  __slots__ = ('bot', 'players')

  def __init__(self, bot):
    self.bot = bot
    self.players = {}

  async def cleanup(self, guild):
    try:
      await guild.voice_client.disconnect()
    except AttributeError:
      pass

    try:
      del self.players[guild.id]
    except KeyError:
      pass
  

  def get_player(self, ctx):
    try:
      player = self.players[ctx.guild.id]
    except KeyError:
      player = MusicPlayer(ctx)
      self.players[ctx.guild.id] = player
      return player
  

  @commands.command(name="join")
  async def join(self,ctx):
    if not ctx.message.author.voice:
      await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
      return
    else:
      channel = ctx.message.author.voice.channel
  
    await channel.connect()
  

  @commands.command(name="play")
  async def play(self,ctx,*,search:str):
    vc = ctx.voice_client
    await ctx.trigger_searching()

    if not vc:
      await ctx.invoke(self.join)

    player = self.get_player(ctx)
    source = await YTDLSource.from_url(ctx, search, loop=self.bot.loop, download=False)

    await player.queue.put(source)
  

  @commands.command(name="pause")
  async def pause(self,ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
      voice_client.pause()
      await ctx.send('**Music paused**')
    else:
      await ctx.send("The bot is not playing anything at the moment.")

  
  @commands.command(name="resume")
  async def resume(self,ctx):
   voice_client = ctx.message.guild.voice_client
   if voice_client.is_paused():
      voice_client.resume()
      await ctx.send('**Music Resumed**')
   else:
      await ctx.send("The bot was not playing anything before this. Use play command")
  

  @commands.command(name="leave")
  async def leave(self,ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
      await self.cleanup(ctx.guild)
      await ctx.send("**Music Stopped**")
    else:
      await ctx.send("The bot is not connected to a voice channel.")

def setup(bot):
    bot.add_cog(MusicCommands(bot))









  




