"""Analytics cog for VelvetBot."""

import discord
from discord.ext import commands


class Analytics(commands.Cog):
    """Cog for analytics and statistics tracking."""

    def __init__(self, bot):
        """Initialize the Analytics cog."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        pass


async def setup(bot):
    """Load the Analytics cog."""
    await bot.add_cog(Analytics(bot))
