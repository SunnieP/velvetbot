"""VelvetBot - Main Bot File
All-in-One Discord Bot for Content Creators & Business
"""

import os
import asyncio
import logging
from datetime import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

from .config import Config
from .database import Database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('velvetbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VelvetBot')


class VelvetBot(commands.Bot):
    """Main bot class with enhanced functionality for creators and business."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.config = Config
        self.db = None
        self.start_time = datetime.utcnow()
        self.version = "1.0.0"
    
    async def setup_hook(self):
        """Initialize database and load cogs."""
        # Initialize database
        self.db = Database()
        await self.db.init()
        logger.info("Database initialized")
        
        # Load all cogs
        cogs = [
            'velvetbot.cogs.moderation',
            'velvetbot.cogs.engagement',
            'velvetbot.cogs.streaming',
            'velvetbot.cogs.clients',
            'velvetbot.cogs.analytics',
            'velvetbot.cogs.custom_commands'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f'{self.user.name} is online!')
        logger.info(f'Bot ID: {self.user.id}')
        logger.info(f'Connected to {len(self.guilds)} guild(s)')
        
        # Set custom status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | {Config.PREFIX}help"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Global error handler."""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=self._error_embed(
                "Missing Permissions",
                "You don't have permission to use this command."
            ))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=self._error_embed(
                "Missing Argument",
                f"Missing required argument: `{error.param.name}`"
            ))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=self._error_embed(
                "Cooldown",
                f"Try again in {error.retry_after:.1f} seconds."
            ))
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(embed=self._error_embed(
                "Error",
                "An unexpected error occurred."
            ))
    
    def _error_embed(self, title: str, description: str) -> discord.Embed:
        """Create a standardized error embed."""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=Config.COLORS['error']
        )
        embed.set_footer(text="VelvetBot")
        return embed


def main():
    """Entry point for the bot."""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        return
    
    bot = VelvetBot()
    
    try:
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        logger.error("Invalid Discord token!")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")


if __name__ == '__main__':
    main()
