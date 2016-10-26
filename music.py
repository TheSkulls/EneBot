import asyncio
import discord

class VoiceEntry:
	def __init__(self, message, player):
		self.requester = message.author
		self.channel = message.channel
		self.player = player

	def __str__(self):
		fmt = '`{0.title}` upado por `{0.uploader}` e requisitado por `{1.display_name}`'
		duration = self.player.duration
		if duration:
			fmt = fmt + ' **[duração: {0[0]}m {0[1]}s]**'.format(divmod(duration, 60))
		return fmt.format(self.player, self.requester)

class VoiceState:
	def __init__(self, bot):
		self.current = None
		self.voice = None
		self.bot = bot
		self.play_next_song = asyncio.Event()
		self.songs = asyncio.Queue()
		self.skip_votes = set() # a set of user_ids that voted
		self.audio_player = self.bot.loop.create_task(self.audio_player_task())

	def is_playing(self):
		if self.voice is None or self.current is None:
			return False

		player = self.current.player
		return not player.is_done()

	@property
	def player(self):
		return self.current.player

	def skip(self):
		self.skip_votes.clear()
		if self.is_playing():
			self.player.stop()

	def toggle_next(self):
		self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

	async def audio_player_task(self):
		while True:
			self.play_next_song.clear()
			self.current = await self.songs.get()
			await self.bot.send_message(self.current.channel, '**[Musica]** Tocando ' + str(self.current))
			self.current.player.start()
			await self.play_next_song.wait()

class Music:
	"""Voice related commands.
	Works in multiple servers at once.
	"""
	def __init__(self, bot):
		self.bot = bot
		self.voice_states = {}

	def get_voice_state(self, server):
		state = self.voice_states.get(server.id)
		if state is None:
			state = VoiceState(self.bot)
			self.voice_states[server.id] = state

		return state

	async def create_voice_client(self, channel):
		voice = await self.bot.join_voice_channel(channel)
		state = self.get_voice_state(channel.server)
		state.voice = voice

	def __unload(self):
		for state in self.voice_states.values():
			try:
				state.audio_player.cancel()
				if state.voice:
					self.bot.loop.create_task(state.voice.disconnect())
			except:
				pass

	async def join(self, channel : discord.Channel):
		"""Joins a voice channel."""
		try:
			await self.create_voice_client(channel)
		except discord.ClientException:
			await self.bot.send_message(msg.channel, 'Already in a voice channel...')
		except discord.InvalidArgument:
			await self.bot.send_message(msg.channel, 'This is not a voice channel...')
		else:
			await self.bot.send_message(msg.channel, 'Ready to play audio in ' + channel.name)

	async def summon(self, msg):
		"""Summons the bot to join your voice channel."""
		summoned_channel = msg.author.voice_channel
		if summoned_channel is None:
			await self.bot.send_message(msg.channel, 'Você não está em um canal de voz.')
			return False

		state = self.get_voice_state(msg.server)
		if state.voice is None:
			state.voice = await self.bot.join_voice_channel(summoned_channel)
		else:
			await state.voice.move_to(summoned_channel)

		return True

	async def play(self, msg, song : str):
		"""Plays a song.
		If there is a song currently in the queue, then it is
		queued until the next song is done playing.
		This command automatically searches as well from YouTube.
		The list of supported sites can be found here:
		https://rg3.github.io/youtube-dl/supportedsites.html
		"""
		state = self.get_voice_state(msg.server)
		opts = {
			'default_search': 'auto',
			'format': 'm4a[abr>0]/bestaudio/worstvideo[height<=360]',
			'quiet': True,
		}

		if state.voice is None:
			success = await self.summon(msg)
			if not success:
				return

		try:
			player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
		except Exception as e:
			fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
			await self.bot.send_message(msg.channel, fmt.format(type(e).__name__, e))
		else:
			#player.volume = 0.6
			if state.is_playing():
				player.volume = state.player.volume
			else:
				player.volume = 0.6
			entry = VoiceEntry(msg, player)
			await self.bot.send_message(msg.channel, '**[Musica]** Adicionado ' + str(entry))
			await state.songs.put(entry)

	async def volume(self, msg, value : int):
		"""Sets the volume of the currently playing song."""

		state = self.get_voice_state(msg.server)
		if state.is_playing():
			player = state.player
			player.volume = value / 100
			await self.bot.send_message(msg.channel, 'Mudando volume para {:.0%}'.format(player.volume))

	async def pause(self, msg):
		"""Pauses the currently played song."""
		state = self.get_voice_state(msg.server)
		if state.is_playing():
			player = state.player
			player.pause()

	async def resume(self, msg):
		"""Resumes the currently played song."""
		state = self.get_voice_state(msg.server)
		if state.is_playing():
			player = state.player
			player.resume()

	async def stop(self, msg):
		"""Stops playing audio and leaves the voice channel.
		This also clears the queue.
		"""
		server = msg.server
		state = self.get_voice_state(server)

		if state.is_playing():
			player = state.player
			player.stop()

		try:
			state.audio_player.cancel()
			del self.voice_states[server.id]
			await state.voice.disconnect()
		except:
			pass

	async def skip(self, msg):
		"""Vote to skip a song. The song requester can automatically skip.
		3 skip votes are needed for the song to be skipped.
		"""

		state = self.get_voice_state(msg.server)
		if not state.is_playing():
			await self.bot.send_message(msg.channel, 'Não estou tocando nenhuma musica.')
			return

		voter = msg.author
		if voter == state.current.requester:
			await self.bot.send_message(msg.channel, 'Requester requested skipping song...')
			state.skip()
		elif voter.id not in state.skip_votes:
			state.skip_votes.add(voter.id)
			total_votes = len(state.skip_votes)
			if total_votes >= 3:
				await self.bot.send_message(msg.channel, 'Já que vários querem, estou trocando de musica...')
				state.skip()
			else:
				await self.bot.send_message(msg.channel, 'Seu voto foi adicionado a contagem, agora temos [{}/3]'.format(total_votes))
		else:
			await self.bot.send_message(msg.channel, 'Você já votou.')

	async def playing(self, msg):
		"""Shows info about the currently played song."""

		state = self.get_voice_state(msg.server)
		if state.current is None:
			await self.bot.send_message(msg.channel, 'Não estou tocando nada.')
		else:
			skip_count = len(state.skip_votes)
			await self.bot.send_message(msg.channel, 'Estou tocando {} [skips: {}/3]'.format(state.current, skip_count))

	async def queue(self, msg):
		state = self.get_voice_state(msg.server)
		if state.current is None:
			await self.bot.send_message(msg.channel, 'Não estou tocando nada.')
		else:
			print(list(state.songs))
