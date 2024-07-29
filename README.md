## GPT Bot on Telegram
This program deploys a gpt bot on telegram. The extra functions include
1. Simultaneous multi-user support.
2. Chat history support, use '/start' to clear chat history and start a new chat.
3. Audio transcription support with openai whisper.
4. Voice message support with openai tts, use '/newvoice' to switch a new tts voice.
5. Use '/stronger' to switch to a more advanced model and '/weaker' to switch to a cheaper model. The default stronger model is gpt-4o and weaker model is gpt-4o-mini.
6. Scheduled messages support. Two examples are provided at the end (commented), one is sending a greeting message every day at a fixed time, the other is sending a new year greeting.
7. Special support for group chat. Not every message is target toward the bot in a group chat, so the bot will selectively reply to messages, with a certain probabiliy (default 20%) to respond in voice chat.

## Deployment
1. Create .env file as follows:
```env
OPENAI_API_KEY=
BOT_TOKEN=
```
2. Run the following commands:
```sh
pip install -r requirements.txt
python tg_gpt_bot.py
```