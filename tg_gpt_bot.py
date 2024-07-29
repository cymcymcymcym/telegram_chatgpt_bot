import os
from openai import OpenAI
import sys
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiocron import crontab
from datetime import datetime
import random

sys.path.append('../..')
from dotenv import load_dotenv, find_dotenv

_=load_dotenv(find_dotenv())
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

bot = Bot(token=os.environ['BOT_TOKEN'])
dp = Dispatcher(bot)

weaker_model="gpt-4o-mini"
stronger_model="gpt-4o"

setted_model=weaker_model

system_prompt="""
Your name is Git. You need to either chat in chinese or english, based on the user's language. Never emphasize you are a language model or artificial intelligence. Act as a friend with casual language.
You are a member of a group chat for casual daily conversation. 
Remember in a group chat not every message is targeted towards you (if there is an unidentifiable pronoun 你 or you or he or she in the conversation, you should judge based on the context whether it is refering to you), so if you receive a message irrelevant to you (such as mentioning another member's name or dicussion of personal details and personal experience or queries such as what happened and you have no idea on the context), print 'none' only and no other tokens."
If a message is targeted towards you such as asking for academic/technical details, you should make a full-length response. Otherwise, your languaged should be limited to something casual and concise (such as 'hmm' 'aww' 'yes' 'no' ), ideally less than 20 tokens.
Your response must never start with personal id. Start straight-away with texts. 
"""

voices=["alloy","echo","fable","onyx","nova","shimmer"]
voice_index=3

def audio_to_text(file_path):
    transcript_data = client.audio.transcriptions.create(
        model="whisper-1", 
        file=open(file_path, "rb")
    )
    return transcript_data['text']

def text_to_audio(text,speech_file_path):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voices[voice_index],
        input=text
    )
    response.stream_to_file(speech_file_path)
    return

def private_text_generation(conversation_history,model=setted_model):
    completion = client.chat.completions.create(
        model=model,
        messages=conversation_history
    )
    response_text = completion.choices[0].message.content
    return response_text

# Dictionary to keep track of conversation history for each user
conversations = {}
groupchat_conversations={}

@dp.message_handler(commands=['start','restart'])
async def welcome(message:types.Message):
    chat_type = message.chat.type
    chat_id = message.chat.id
    user_id = message.from_user.id
    global voice_index
    voice_index=3
    
    if chat_type=='private':
        conversations[user_id] = []
    elif chat_type=='group':
        groupchat_conversations[chat_id] = []
    
    await message.reply("Welcome! I am a GPT bot")

@dp.message_handler(commands=['newvoice'])
async def new_voice(message:types.Message):
    global voice_index
    voice_index+=1
    voice_index%=len(voices)
    
    text="Hi. This is my new voice."

    text_to_audio(text, "gpt_voice.mp3")
    # Send the audio file using telethon
    with open('gpt_voice.mp3', 'rb') as audio:
        await message.answer_voice(audio,caption=text)

@dp.message_handler(commands=['chatid'])
async def welcome(message:types.Message):
    chat_id = message.chat.id
    await message.reply("chat id: "+str(chat_id))

@dp.message_handler(commands=['stronger'])
async def stronger(message:types.Message):
    chat_type = message.chat.type
    if chat_type=='private':
        global setted_model
        setted_model=stronger_model
        await message.reply("Model changed to: "+stronger_model)
    else:
        await message.reply(f"I cannot be {stronger_model} in group chats. cym is too poor for that.")

@dp.message_handler(commands=['weaker'])
async def weaker(message:types.Message):
    chat_type = message.chat.type
    if chat_type=='private':
        global setted_model
        setted_model=weaker_model
        await message.reply("Model changed to: "+weaker_model)
    else:
        await message.reply(f"I am always {weaker_model} in group chats.")


@dp.message_handler(content_types=types.ContentType.ANY)
async def handle_any_message(message: types.Message):
    message_type=message.content_type
    chat_type = message.chat.type  # 'private', 'group', 'supergroup', or 'channel'
    chat_id = message.chat.id
    user_id = message.from_user.id
    text_content=""
    if message_type == 'text':
        text_content = message.text
    elif message_type == 'voice':
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        telegram_path = file.file_path
        download_path="voice"+str(user_id)+".ogg"
        await bot.download_file(telegram_path, download_path)

        text_content=audio_to_text(download_path)
        os.remove(download_path)
    elif message_type in ['document', 'photo']:
        if message.caption:
            pass
        pass
    elif message_type in ['animation','sticker']:
        pass
    else:
        pass

    if chat_type == 'private':
        #print("normal message")
        user_message = {"role": "user", "content": text_content}
        
        conversation_history = conversations.get(user_id, [{"role": "system", "content": "You are a helpful assistant."}])
        conversation_history.append(user_message)
        conversations[user_id] = conversation_history
        
        response_text = private_text_generation(conversation_history)
        conversations[user_id].append({"role": "assistant", "content": response_text})

        await message.reply(response_text)
    elif chat_type == 'group' or chat_type == 'supergroup':
    #print("group message")
        user_message = {"role": "user", "content": str(user_id) + ": " + text_content}
        
        conversation_history = groupchat_conversations.get(chat_id, [{"role": "system", "content": system_prompt}])
        conversation_history.append(user_message)
        groupchat_conversations[chat_id] = conversation_history
        
        response_text = private_text_generation(conversation_history,weaker_model)

        # Generate a random number between 0 and 1
        probability = random.random()

        if response_text != "none":
            if probability <= 0.8:
                # 20% probability to send a voice message
                print("audio")
                text_to_audio(response_text, "gpt_voice.mp3")
                # Send the audio file using telethon
                with open('gpt_voice.mp3', 'rb') as audio:
                    await message.answer_voice(audio,caption=response_text)
            else:
                # 80% probability to send a text message
                groupchat_conversations[chat_id].append({"role": "assistant", "content": response_text})
                await message.reply(response_text)
        else:
            print(user_message)

#schedule daily greeting message
'''
chat_id = 123456
@crontab('25 23 * * *')
async def send_scheduled_message(chat_id):
    print(f"Attempting to send scheduled message at {datetime.now()}")
    try:
        message_text = "Hey there, how's your day going? What's on your mind?"
        # Append the bot's message to the conversation history
        chat_id = chat_id
        greeting={"role": "assistant", "content": message_text}
        conversation_history = conversations.get(chat_id, [{"role": "system", "content": "You are a helpful assistant."}])
        conversation_history.append(greeting)
        groupchat_conversations[chat_id]=conversation_history
        await bot.send_message(chat_id=chat_id, text=message_text)
        print("Scheduled message sent.")
    except Exception as e:
        print(f"An error occurred: {e}")
'''

#schedule New Year message
#chat_id2=12345678
'''
@crontab('59 23 31 12 *')  # Schedule for 23:59 on December 31st
async def send_new_year_message(chat_id=chat_id2):
    print(f"Attempting to send scheduled Happy New Year message at {datetime.now()}")
    try:
        message_text = "Wishing you a fantastic year filled with joy and success."
        chat_id = chat_id

        greeting = {"role": "assistant", "content": message_text}
        conversation_history = conversations.get(chat_id, [{"role": "system", "content": "You are a helpful assistant."}])
        
        # Append the New Year greeting to the conversation history
        conversation_history.append(greeting)
        groupchat_conversations[chat_id] = conversation_history
        await bot.send_message(chat_id=chat_id, text=message_text)
        print("Happy New Year message sent.")
    except Exception as e:
        print(f"An error occurred: {e}")
'''

if __name__ == '__main__':
    print(f"Code started at {datetime.now()}")
    executor.start_polling(dp, skip_updates=True)


