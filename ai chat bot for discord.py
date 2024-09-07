import os
import discord
from discord.ext import commands
import asyncio
import google.generativeai as genai
import logging
import json

# Configuration - Use environment variables for security
DISCORD_BOT_TOKEN = ('your-token-here')
GEMINI_API_KEY = ('your-key-here')

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Define intents
intents = discord.Intents.default()
intents.messages = True  # Enable message events
intents.message_content = True  # Enable access to message content

# Default response if Gemini API fails
DEFAULT_RESPONSE = "I'm sorry, I don't have a response for that."

# File to store chat history
HISTORY_FILE = 'chat_history.json'

# Load chat history from file
def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as file:
                if os.stat(HISTORY_FILE).st_size == 0:  # Check if file is empty
                    return {}
                return json.load(file)
        except json.JSONDecodeError:
            print("Error: JSON decode error. The file may be corrupted.")
            return {}
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return {}
    return {}

# Save chat history to file
def save_chat_history(chat_history):
    try:
        with open(HISTORY_FILE, 'w') as file:
            json.dump(chat_history, file, indent=4)
    except Exception as e:
        print(f"Error saving chat history: {e}")

# Initialize chat history
chat_history = load_chat_history()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Initialize user chat history if not already present
    if str(message.author.id) not in chat_history:
        chat_history[str(message.author.id)] = []

    # Store the new message in chat history
    chat_history[str(message.author.id)].append(message.content)

    # Save the updated chat history
    save_chat_history(chat_history)

    # Check if the bot is mentioned in the message
    if bot.user.mentioned_in(message):
        content = message.content

        # Append chat history to the prompt
        history_text = "\n".join(chat_history[str(message.author.id)])
        prompt = (
            f"You are a Turkish person. Speak and think like a Turkish person. "
            f"Remember all previous chats. Here is the chat history:\n{history_text}\n"
            f"Respond to the following message: {content}"
        )

        if content.strip():
            try:
                response = await ask_gemini(prompt)
                await message.channel.send(response)
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                await message.channel.send("An error occurred while processing your message. Please try again later.")
        else:
            return

async def ask_gemini(prompt):
    try:
        # Use the Gemini API to generate a response
        response = await asyncio.get_event_loop().run_in_executor(None, lambda: model.generate_content(prompt))
        # Extract response text
        if response and hasattr(response, 'text'):
            return response.text
        else:
            logging.info("API Response: %s", response)
            return DEFAULT_RESPONSE
    except Exception as e:
        logging.error("API Exception: %s", e)
        return DEFAULT_RESPONSE

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN or not GEMINI_API_KEY:
        print("Error: Environment variables for DISCORD_BOT_TOKEN or GEMINI_API_KEY are not set.")
    else:
        bot.run(DISCORD_BOT_TOKEN)