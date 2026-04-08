import asyncio
import os

import discord
from discord.ext import commands

from config.settings import BOT_NAME, BOT_VERSION, TOKEN


intents = discord.Intents.all()


async def load_extensions(client: commands.Bot):
    commands_dir = 'commands'
    print('Loading all commands (extensions)...')

    for filename in os.listdir(f'./{commands_dir}'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await client.load_extension(f'{commands_dir}.{filename[:-3]}')
                print(f' - Loaded {filename}')
            except Exception as e:
                print(f' - Failed to load {filename}: {e}')


class UIUBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.synced_once = False

    async def setup_hook(self):
        await load_extensions(self)
        if not self.synced_once:
            try:
                synced = await self.tree.sync()
                self.synced_once = True
                print(f'Synced {len(synced)} slash command(s)')
            except Exception as e:
                print(f'Failed to sync commands: {e}')


client = UIUBot()


@client.event
async def on_ready():
    print(f'\nSuccess! We have logged in as {client.user}')
    print('-----------------------------------------')


if __name__ == '__main__':
    print(f'{BOT_NAME} v{BOT_VERSION} is starting...')
    client.run(TOKEN)
