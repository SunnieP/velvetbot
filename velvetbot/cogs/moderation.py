"""Moderation Cog - Moderation tools for server management."""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional

from ..config import Config
from ..database import WarnLog


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
    
    @commands.command(name='warn')
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member."""
        async with self.bot.db.get_session() as session:
            warn = WarnLog(
                user_id=member.id,
                guild_id=ctx.guild.id,
                moderator_id=ctx.author.id,
                reason=reason
            )
            session.add(warn)
            await session.commit()
        
        embed = self._create_embed(
            "⚠️ Member Warned",
            f"{member.mention} has been warned.",
            Config.COLORS['warning']
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
        
        try:
            dm_embed = self._create_embed(
                "You have been warned",
                f"You received a warning in **{ctx.guild.name}**",
                Config.COLORS['warning']
            )
            dm_embed.add_field(name="Reason", value=reason)
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("You cannot kick this member.")
        
        await member.kick(reason=f"{ctx.author}: {reason}")
        
        embed = self._create_embed(
            "👢 Member Kicked",
            f"{member.mention} has been kicked.",
            Config.COLORS['error']
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server."""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("You cannot ban this member.")
        
        await member.ban(reason=f"{ctx.author}: {reason}")
        
        embed = self._create_embed(
            "🔨 Member Banned",
            f"{member.mention} has been banned.",
            Config.COLORS['error']
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name='mute')
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: str = "10m", *, reason: str = "No reason"):
        """Timeout a member. Duration: 1m, 1h, 1d"""
        units = {'m': 60, 'h': 3600, 'd': 86400}
        unit = duration[-1].lower()
        amount = int(duration[:-1])
        seconds = amount * units.get(unit, 60)
        
        until = datetime.utcnow() + timedelta(seconds=seconds)
        await member.timeout(until, reason=reason)
        
        embed = self._create_embed(
            "🔇 Member Muted",
            f"{member.mention} has been timed out for {duration}.",
            Config.COLORS['warning']
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='unmute')
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Remove timeout from a member."""
        await member.timeout(None)
        embed = self._create_embed(
            "🔊 Member Unmuted",
            f"{member.mention} has been unmuted.",
            Config.COLORS['success']
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='purge')
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10):
        """Delete multiple messages."""
        if amount > 100:
            amount = 100
        deleted = await ctx.channel.purge(limit=amount + 1)
        embed = self._create_embed(
            "🗑️ Messages Purged",
            f"Deleted {len(deleted) - 1} messages.",
            Config.COLORS['info']
        )
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=3)
    
    @commands.command(name='warnings')
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """View warnings for a member."""
        from sqlalchemy import select
        async with self.bot.db.get_session() as session:
            result = await session.execute(
                select(WarnLog).where(
                    WarnLog.user_id == member.id,
                    WarnLog.guild_id == ctx.guild.id
                )
            )
            warns = result.scalars().all()
        
        embed = self._create_embed(
            f"Warnings for {member.display_name}",
            f"Total warnings: {len(warns)}",
            Config.COLORS['info']
        )
        
        for i, warn in enumerate(warns[-5:], 1):
            embed.add_field(
                name=f"Warning {i}",
                value=f"**Reason:** {warn.reason}\n**Date:** {warn.created_at.strftime('%Y-%m-%d')}",
                inline=False
            )
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
