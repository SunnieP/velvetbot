"""Clients cog for VelvetBot."""

import discord
from discord.ext import commands


class Clients(commands.Cog):
    """Cog for client management."""

    def __init__(self, bot):
        """Initialize the Clients cog."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the bot is ready."""
        pass


async def setup(bot):
    """Load the Clients cog."""
    await bot.add_cog(Clients(bot))
