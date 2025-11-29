"""VelvetBot - Main Bot File
All-in-One Discord Bot for Content Creators & Business
"""

import os
import asyncio
import logging
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv


# Load environment variables FIRST - before importing Config
load_dotenv()
from .config import Config
from .database import Database

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
            title=f"\u274c {title}",
            description=description,
            color=Config.COLORS['error']
        )
        embed.set_footer(text="VelvetBot")
        return embed

    def _success_embed(self, title: str, description: str) -> discord.Embed:
        """Create a standardized success embed."""
        embed = discord.Embed(
            title=f"\u2705 {title}",
            description=description,
            color=Config.COLORS['success']
        )
        embed.set_footer(text="VelvetBot")
        return embed


# Owner-only sync commands
@commands.command(name='sync')
@commands.is_owner()
async def sync_commands(ctx):
    """Sync slash commands to the current guild."""
    try:
        synced = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"\u2705 Synced {len(synced)} commands to this guild.")
    except Exception as e:
        await ctx.send(f"\u274c Failed to sync: {e}")


@commands.command(name='syncglobal')
@commands.is_owner()
async def sync_global(ctx):
    """Sync slash commands globally."""
    try:
        synced = await ctx.bot.tree.sync()
        await ctx.send(f"\u2705 Synced {len(synced)} commands globally.")
    except Exception as e:
        await ctx.send(f"\u274c Failed to sync: {e}")


@commands.command(name='freshsync')
@commands.is_owner()
async def fresh_sync(ctx):
    """Clear all commands and re-sync fresh (fixes duplicate/stale commands)."""
    bot = ctx.bot
    
    await ctx.send("\u23f3 Starting fresh sync... This may take a moment.")
    
    try:
        # Clear guild-specific commands
        bot.tree.clear_commands(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        
        # Clear global commands
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        
        # Reload all cogs to re-register commands
        cogs = [
            "velvetbot.cogs.moderation",
            "velvetbot.cogs.engagement",
            "velvetbot.cogs.streaming",
            "velvetbot.cogs.clients",
            "velvetbot.cogs.analytics",
            "velvetbot.cogs.custom_commands"
        ]
        for cog in cogs:
            try:
                await bot.reload_extension(cog)
            except Exception as e:
                logger.error(f"Failed to reload {cog}: {e}")
        # Sync globally
        synced = await bot.tree.sync()
        
        await ctx.send(f"\u2705 Fresh sync complete! Synced {len(synced)} commands.")
        logger.info(f"Fresh sync completed by {ctx.author}: {len(synced)} commands")
        
    except Exception as e:
        await ctx.send(f"\u274c Fresh sync failed: {e}")
        logger.error(f"Fresh sync error: {e}")


@commands.command(name='reloadcog')
@commands.is_owner()
async def reload_cog(ctx, cog_name: str):
    """Reload a specific cog."""
    full_name = f"velvetbot.cogs.{cog_name}"
    try:
        await ctx.bot.reload_extension(full_name)
        await ctx.send(f"\u2705 Reloaded `{cog_name}` cog.")
        logger.info(f"Reloaded cog {cog_name} by {ctx.author}")
    except Exception as e:
        await ctx.send(f"\u274c Failed to reload: {e}")


@commands.command(name='reloadall')
@commands.is_owner()
async def reload_all(ctx):
    """Reload all cogs."""
    cogs = [
        'velvetbot.cogs.moderation',
        'velvetbot.cogs.engagement',
        'velvetbot.cogs.streaming',
        'velvetbot.cogs.clients',
        'velvetbot.cogs.analytics',
        'velvetbot.cogs.custom_commands'
    ]
    
    success = []
    failed = []
    
    for cog in cogs:
        try:
            await ctx.bot.reload_extension(cog)
            success.append(cog.split('.')[-1])
        except Exception as e:
            failed.append(f"{cog.split('.')[-1]}: {e}")
    
    msg = f"\u2705 Reloaded: {', '.join(success)}" if success else ""
    if failed:
        msg += f"\n\u274c Failed: {', '.join(failed)}"
    
    await ctx.send(msg)


def main():
    """Entry point for the bot."""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        return

    bot = VelvetBot()
    
    # Add owner commands
    bot.add_command(sync_commands)
    bot.add_command(sync_global)
    bot.add_command(fresh_sync)
    bot.add_command(reload_cog)
    bot.add_command(reload_all)

    try:
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        logger.error("Invalid Discord token!")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")


if __name__ == '__main__':
    main()
