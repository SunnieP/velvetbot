"""Custom commands cog for VelvetBot."""

import discord
from discord.ext import commands


class CustomCommands(commands.Cog):
    """Cog for custom user-defined commands."""

    def __init__(self, bot):
        """Initialize the CustomCommands cog."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        pass


async def setup(bot):
    """Load the CustomCommands cog."""
    await bot.add_cog(CustomCommands(bot))
