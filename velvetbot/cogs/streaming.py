"""Streaming cog for VelvetBot."""

import discord
from discord.ext import commands


class Streaming(commands.Cog):
    """Cog for stream monitoring and notifications."""

    def __init__(self, bot):
        """Initialize the Streaming cog."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        pass


async def setup(bot):
    """Load the Streaming cog."""
    await bot.add_cog(Streaming(bot))
