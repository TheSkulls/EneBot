import asyncio
import discord
#from chatterbot import Chatbot
#from chatterbot.trainers import ListTrainer
import cleverbot
import music

#chatbot = Chatbot("Ene")
#chatbot.set_trainer(ListTrainer)
#chatbot.train("chatterbot.corpus.Portuguese")
chatbot = cleverbot.Cleverbot()
token   = "MjM5MTExNzQ0NzA5MDY2NzUz.CuwCqg.ObOSR09-SGbgbAZGLXzmqiVDyM0"
bot     = discord.Client()
music   = music.Music(bot)

function = [	['help','Ajuda'],\
            	['clear_chat','Apaga todas as mensagens do chat'],\
				['play','Tocar Musica / Sem link da play na musica pausada'],\
				['pause','Pausa a musica'],\
				['vol','Muda o volume'],\
				['playing','Mostra a musica que está tocando'],\
				['skip','Vota para passar a musica']\
			]

print("Discord Version: "+ discord.__version__)
print("Logging......\n")

if not discord.opus.is_loaded():
	# the 'opus' library here is opus.dll on windows
	# or libopus.so on linux in the current directory
	# you should replace this with the location the
	# opus library is located in and with the proper filename.
	# note that on windows this DLL is automatically provided for you
	discord.opus.load_opus('opus')

@bot.event
async def on_delete_message(msg):
	if msg.server.get_member(bot.user.id).permissions_in(msg.channel).manage_messages == True:
		await bot.delete_message(msg)
	else:
		return

@bot.event
async def on_user_menssage(msg):
	space = 0
	if msg.content.startswith(' '):
		msg.content = msg.content.split(' ')[1]
		space = 1

	if msg.content == '':
		await bot.send_message(msg.channel, '{0.author.mention} Você precisa de ajuda?!'.format(msg))

	elif msg.content == '?':
		await on_user_command(msg, '')

	else:
		if space == 1:
			#await bot.send_message(msg.channel, '{}'.format(chatbot.get_response(msg.content)))
			await bot.send_message(msg.channel, '{0}'.format(chatbot.ask(msg.content)))
		else:
			return

@bot.event
async def on_user_command(msg, msgContent):
	if msg.content == '':
		await on_user_menssage(msg)

	elif msg.content == 'help' or msg.content == '?':
		fmt = ', esses são os meus comandos:\n\n'
		for i in range(len(function)):
			fmt += '	`!'+function[i][0]+'` - '+function[i][1]+'\n'
		fmt += '\nMas lembre-se de usar e/ene antes dos comandos'
		await bot.send_message(msg.channel, '{0.author.mention}{1}'.format(msg,fmt))
		await on_delete_message(msg)

	elif msg.content.startswith('play'):
		msg.content = msg.content.split('play')[1]
		if msg.content.startswith(' '):
			num = msgContent.lower().find(msg.content.split(' ')[1])
			await music.play(msg, msgContent[num:])
		else:
			await music.resume(msg)

		await on_delete_message(msg)

	elif msg.content.startswith('pause'):
		await music.pause(msg)
		await on_delete_message(msg)

	elif msg.content.startswith('skip'):
		await music.skip(msg)
		await on_delete_message(msg)

	elif msg.content.startswith('vol'):
		msg.content = msg.content.split('vol')[1]
		if msg.content.startswith(' '):
			if msg.content.split(' ')[1] != '':
				await music.volume(msg, int(msg.content.split(' ')[1]))
		await on_delete_message(msg)

	elif msg.content.startswith('playing'):
		await music.playing(msg)
		await on_delete_message(msg)

	elif msg.content.startswith('clear_chat'):
		if msg.server.get_member(msg.author.id).permissions_in(msg.channel).manage_messages == True:
			if msg.server.get_member(bot.user.id).permissions_in(msg.channel).manage_messages == True:
				await bot.purge_from(msg.channel,limit=1000000000)
			else:
				await bot.send_message(msg.channel, '{0.author.mention} Desculpe, mas eu não tenho permissão de admin para apagar as mensagens!'.format(msg))
				return
		else:
			await bot.send_message(msg.channel, '{0.author.mention} Desculpe, mas você não pode apagar as mensagens!'.format(msg))
			return

	else:
		await bot.send_message(msg.channel, '{0.author.mention} Eu não entendi o que quer!'.format(msg))
		await on_delete_message(msg)


@bot.event
async def on_ready():
	print('Login Complete!\n')
	print('Logged in: '+bot.user.name)
	print('ID: '+bot.user.id)
	print('----------------------------\n')

@bot.event
async def on_message(msg):
	if msg.author.bot == True:
		return
	else:
		msgContent = msg.content
		msg.content = msg.content.lower()
		if msg.content.startswith(bot.user.name.lower()) or msg.content.startswith('e'):
			if msg.content.startswith(bot.user.name.lower()+'!'):
				if msg.content.split(bot.user.name.lower()+'!')[1].startswith(' '):
					#Conversa
					msg.content = msg.content.split(bot.user.name.lower()+'! ')[1]
					await on_user_menssage(msg)

				else:
					#Comandos
					msg.content = msg.content.split(bot.user.name.lower()+'!')[1]
					await on_user_command(msg, msgContent)

			elif msg.content.startswith('e!'):
				if msg.content.split('e!')[1].startswith(' '):
					#Conversa
					msg.content = msg.content.split('e! ')[1]
					await on_user_menssage(msg)

				else:
					#Comandos
					msg.content = msg.content.split('e!')[1]
					await on_user_command(msg, msgContent)

			else:
				if msg.content.startswith(bot.user.name.lower()):
					if msg.content.startswith(bot.user.name.lower()+'!'):
						msg.content = msg.content.split(bot.user.name.lower()+'!')[1]
					else:
						msg.content = msg.content.split(bot.user.name.lower())[1]
				elif msg.content.startswith('e'):
					if msg.content.startswith('e!'):
						msg.content = msg.content.split('e!')[1]
					elif msg.content.split('e')[1] == ' ?' or msg.content.split('e')[1] == '?':
						msg.content = msg.content.split('e')[1]
					else:
						return
				await on_user_menssage(msg)

		elif bot.user in msg.mentions:
			#Quando o bot é mencionado
			msg.content = msg.content.replace(bot.user.mention.lower(), '')
			if msg.content == '':
				await bot.send_message(msg.channel, '{0.author.mention} Você me chamou?!'.format(msg))
				await on_delete_message(msg)
			else:
				await on_user_menssage(msg)

		#elif msg.content.find('leili') != -1:
			#Quando alguém fala leili

bot.run(token)
