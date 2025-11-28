"""Moderation Cog - Moderation tools for server management."""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import logging
import re

from ..config import Config

logger = logging.getLogger('VelvetBot.Moderation')


class Moderation(commands.Cog):
    """Moderation commands for server management."""

    def __init__(self, bot):
        self.bot = bot

    def _create_embed(self, title: str, description: str, color: int = None) -> discord.Embed:
        """Create a branded embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or Config.COLORS['primary'],
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="VelvetBot Moderation")
        return embed

    async def _log_action(self, guild: discord.Guild, action: str, target: discord.Member, 
                          moderator: discord.Member, reason: str):
        """Log moderation action to log channel and database."""
        # Log to channel
        log_channel = guild.get_channel(Config.MOD_LOG_CHANNEL)
        if log_channel:
            embed = self._create_embed(
                f"\U0001F6E1 {action}",
                f"**Target:** {target.mention}\n**Moderator:** {moderator.mention}\n**Reason:** {reason}",
                Config.COLORS['warning']
            )
            await log_channel.send(embed=embed)
        
        # Log to database
        if self.bot.db:
            await self.bot.db.log_mod_action(guild.id, action, target.id, moderator.id, reason)

    @commands.hybrid_command(name="warn", description="Warn a member")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member."""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("\u274c You cannot warn someone with equal or higher role.")
        
        # Log to database
        if self.bot.db:
            await self.bot.db.add_warning(member.id, ctx.guild.id, ctx.author.id, reason)
        
        embed = self._create_embed(
            "\u26a0 Member Warned",
            f"{member.mention} has been warned.",
            Config.COLORS['warning']
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        
        # DM the user
        try:
            dm_embed = self._create_embed(
                f"\u26a0 Warning in {ctx.guild.name}",
                f"You have been warned.\n**Reason:** {reason}",
                Config.COLORS['warning']
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        await self._log_action(ctx.guild, "WARN", member, ctx.author, reason)

    @commands.hybrid_command(name="kick", description="Kick a member from the server")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("\u274c You cannot kick someone with equal or higher role.")
        
        # DM before kick
        try:
            dm_embed = self._create_embed(
                f"\U0001F462 Kicked from {ctx.guild.name}",
                f"You have been kicked.\n**Reason:** {reason}",
                Config.COLORS['error']
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        await member.kick(reason=f"{ctx.author}: {reason}")
        
        embed = self._create_embed(
            "\U0001F462 Member Kicked",
            f"{member.mention} has been kicked.",
            Config.COLORS['error']
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
        await self._log_action(ctx.guild, "KICK", member, ctx.author, reason)

    @commands.hybrid_command(name="ban", description="Ban a member from the server")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server."""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("\u274c You cannot ban someone with equal or higher role.")
        
        # DM before ban
        try:
            dm_embed = self._create_embed(
                f"\U0001F6AB Banned from {ctx.guild.name}",
                f"You have been banned.\n**Reason:** {reason}",
                Config.COLORS['error']
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=1)
        
        embed = self._create_embed(
            "\U0001F6AB Member Banned",
            f"{member.mention} has been banned.",
            Config.COLORS['error']
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
        await self._log_action(ctx.guild, "BAN", member, ctx.author, reason)

    @commands.hybrid_command(name="unban", description="Unban a user by ID")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        """Unban a user by their ID."""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")
            
            embed = self._create_embed(
                "\u2705 User Unbanned",
                f"{user.mention} has been unbanned.",
                Config.COLORS['success']
            )
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("\u274c User not found or not banned.")

    @commands.hybrid_command(name="mute", description="Timeout a member")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: str = "1h", *, reason: str = "No reason provided"):
        """Timeout a member. Duration examples: 10m, 1h, 1d, 7d"""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("\u274c You cannot mute someone with equal or higher role.")
        
        # Parse duration
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        match = re.match(r'(\d+)([smhd])', duration.lower())
        
        if not match:
            return await ctx.send("\u274c Invalid duration. Use format: 10m, 1h, 1d")
        
        amount, unit = int(match.group(1)), match.group(2)
        seconds = amount * time_units[unit]
        
        # Discord timeout max is 28 days
        if seconds > 28 * 86400:
            return await ctx.send("\u274c Maximum timeout is 28 days.")
        
        until = datetime.utcnow() + timedelta(seconds=seconds)
        await member.timeout(until, reason=f"{ctx.author}: {reason}")
        
        embed = self._create_embed(
            "\U0001F507 Member Muted",
            f"{member.mention} has been timed out for {duration}.",
            Config.COLORS['warning']
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
        await self._log_action(ctx.guild, "MUTE", member, ctx.author, f"{duration}: {reason}")

    @commands.hybrid_command(name="unmute", description="Remove timeout from a member")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Remove timeout from a member."""
        await member.timeout(None)
        embed = self._create_embed(
            "\U0001F50A Member Unmuted",
            f"{member.mention} has been unmuted.",
            Config.COLORS['success']
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="purge", description="Delete messages")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10):
        """Delete multiple messages."""
        if amount > 100:
            amount = 100
        
        deleted = await ctx.channel.purge(limit=amount + 1)
        embed = self._create_embed(
            "\U0001F9F9 Messages Purged",
            f"Deleted {len(deleted) - 1} messages.",
            Config.COLORS['info']
        )
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=3)

    @commands.hybrid_command(name="slowmode", description="Set channel slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 0):
        """Set slowmode delay. 0 to disable."""
        if seconds > 21600:  # 6 hours max
            seconds = 21600
        
        await ctx.channel.edit(slowmode_delay=seconds)
        
        if seconds == 0:
            embed = self._create_embed(
                "\U0001F40C Slowmode Disabled",
                "Slowmode has been disabled.",
                Config.COLORS['success']
            )
        else:
            embed = self._create_embed(
                "\U0001F40C Slowmode Enabled",
                f"Slowmode set to {seconds} seconds.",
                Config.COLORS['info']
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="warnings", description="View warnings for a member")
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """View warnings for a member."""
        if self.bot.db:
            warns = await self.bot.db.get_warnings(member.id, ctx.guild.id)
        else:
            warns = []
        
        embed = self._create_embed(
            f"Warnings for {member.display_name}",
            f"Total warnings: {len(warns)}",
            Config.COLORS['info']
        )
        
        for i, warn in enumerate(warns[-5:], 1):
            embed.add_field(
                name=f"Warning {i}",
                value=f"**Reason:** {warn.get('reason', 'N/A')}\n**Date:** {warn.get('created_at', 'N/A')}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearwarnings", description="Clear all warnings for a member")
    @commands.has_permissions(administrator=True)
    async def clearwarnings(self, ctx, member: discord.Member):
        """Clear all warnings for a member."""
        if self.bot.db:
            await self.bot.db.clear_warnings(member.id, ctx.guild.id)
        
        embed = self._create_embed(
            "\u2705 Warnings Cleared",
            f"Cleared all warnings for {member.mention}.",
            Config.COLORS['success']
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-moderation listener."""
        if message.author.bot or not message.guild:
            return
        
        # Check for excessive mentions (potential spam)
        if len(message.mentions) > 5:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, please don't spam mentions.",
                delete_after=5
            )
            logger.info(f"Auto-deleted mention spam from {message.author} in {message.guild}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
