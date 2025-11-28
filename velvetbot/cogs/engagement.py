"""Engagement cog for VelvetBot."""

import discord
from discord.ext import commands


class Engagement(commands.Cog):
    """Cog for user engagement features."""

    def __init__(self, bot):
        """Initialize the Engagement cog."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        pass


async def setup(bot):
    """Load the Engagement cog."""
    await bot.add_cog(Engagement(bot))
