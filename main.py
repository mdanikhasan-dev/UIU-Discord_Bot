import discord
from discord.ext import commands
import os
import asyncio
from config.settings import TOKEN  
from config.settings import BOT_NAME, BOT_VERSION  

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

async def load_extensions():
    commands_dir = 'commands'
    print("Loading all commands (extensions)...")
    
    for filename in os.listdir(f'./{commands_dir}'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await client.load_extension(f'{commands_dir}.{filename[:-3]}')
                print(f" - Loaded {filename}")
            except Exception as e:
                print(f" - Failed to load {filename}: {e}")

@client.event
async def on_ready():
    if not client.extensions:
        await load_extensions()

    print(f'\nSuccess! We have logged in as {client.user}')
    print('-----------------------------------------')
    
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

if __name__ == '__main__':
    print(f"{BOT_NAME} v{BOT_VERSION} is starting...")
    client.run(TOKEN)
