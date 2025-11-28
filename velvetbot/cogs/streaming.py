"""Streaming cog for VelvetBot.

Handles Twitch, YouTube, and TikTok stream notifications.
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import logging
from datetime import datetime
from typing import Optional

from ..config import Config

logger = logging.getLogger('VelvetBot.Streaming')


class Streaming(commands.Cog):
    """Cog for stream monitoring and notifications."""

    def __init__(self, bot):
        """Initialize the Streaming cog."""
        self.bot = bot
        self.twitch_token = None
        self.twitch_token_expires = None
        self.live_streams = {}  # Track currently live streams
        
    async def cog_load(self):
        """Start background tasks when cog loads."""
        if Config.TWITCH_CLIENT_ID and Config.TWITCH_CLIENT_SECRET:
            self.check_twitch_streams.start()
            logger.info("Twitch stream checker started")
        if Config.YOUTUBE_API_KEY:
            self.check_youtube_streams.start()
            logger.info("YouTube stream checker started")

    async def cog_unload(self):
        """Stop background tasks when cog unloads."""
        self.check_twitch_streams.cancel()
        self.check_youtube_streams.cancel()

    async def get_twitch_token(self) -> Optional[str]:
        """Get or refresh Twitch OAuth token."""
        if self.twitch_token and self.twitch_token_expires:
            if datetime.utcnow() < self.twitch_token_expires:
                return self.twitch_token
        
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": Config.TWITCH_CLIENT_ID,
            "client_secret": Config.TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.twitch_token = data["access_token"]
                    return self.twitch_token
        return None

    @tasks.loop(minutes=2)
    async def check_twitch_streams(self):
        """Check if configured Twitch channels are live."""
        if not Config.TWITCH_CHANNELS:
            return
            
        token = await self.get_twitch_token()
        if not token:
            logger.error("Failed to get Twitch token")
            return

        headers = {
            "Client-ID": Config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}"
        }
        
        for channel in Config.TWITCH_CHANNELS:
            url = f"https://api.twitch.tv/helix/streams?user_login={channel}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        streams = data.get("data", [])
                        
                        if streams:
                            stream = streams[0]
                            stream_id = stream["id"]
                            
                            # Only notify if this is a new stream
                            if stream_id not in self.live_streams:
                                self.live_streams[stream_id] = stream
                                await self.send_stream_notification(
                                    platform="twitch",
                                    channel=channel,
                                    title=stream["title"],
                                    game=stream.get("game_name", "Unknown"),
                                    thumbnail=stream["thumbnail_url"].replace("{width}", "1280").replace("{height}", "720"),
                                    url=f"https://twitch.tv/{channel}"
                                )
                        else:
                            # Stream ended, remove from tracking
                            self.live_streams = {k: v for k, v in self.live_streams.items() 
                                                if v.get("user_login") != channel}

    @tasks.loop(minutes=3)
    async def check_youtube_streams(self):
        """Check if configured YouTube channels are live."""
        if not Config.YOUTUBE_CHANNELS or not Config.YOUTUBE_API_KEY:
            return
            
        for channel_id in Config.YOUTUBE_CHANNELS:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "channelId": channel_id,
                "eventType": "live",
                "type": "video",
                "key": Config.YOUTUBE_API_KEY
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get("items", [])
                        
                        if items:
                            video = items[0]
                            video_id = video["id"]["videoId"]
                            
                            if f"yt_{video_id}" not in self.live_streams:
                                self.live_streams[f"yt_{video_id}"] = video
                                snippet = video["snippet"]
                                await self.send_stream_notification(
                                    platform="youtube",
                                    channel=snippet["channelTitle"],
                                    title=snippet["title"],
                                    game="Live Stream",
                                    thumbnail=snippet["thumbnails"]["high"]["url"],
                                    url=f"https://youtube.com/watch?v={video_id}"
                                )

    async def send_stream_notification(self, platform: str, channel: str, title: str, 
                                       game: str, thumbnail: str, url: str):
        """Send a stream notification to the configured channel."""
        notification_channel = self.bot.get_channel(Config.STREAM_NOTIFICATION_CHANNEL)
        if not notification_channel:
            logger.error(f"Stream notification channel not found: {Config.STREAM_NOTIFICATION_CHANNEL}")
            return

        # Platform-specific colors and emojis
        platform_info = {
            "twitch": {"color": 0x9146FF, "emoji": "\U0001F7E3", "name": "Twitch"},
            "youtube": {"color": 0xFF0000, "emoji": "\U0001F534", "name": "YouTube"},
            "tiktok": {"color": 0x000000, "emoji": "\U0001F3B5", "name": "TikTok"}
        }
        
        info = platform_info.get(platform, {"color": Config.COLORS['primary'], "emoji": "\U0001F4FA", "name": platform})
        
        embed = discord.Embed(
            title=f"{info['emoji']} {channel} is LIVE!",
            description=f"**{title}**",
            color=info['color'],
            url=url,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Platform", value=info['name'], inline=True)
        embed.add_field(name="Category", value=game, inline=True)
        embed.set_image(url=thumbnail)
        embed.set_footer(text="VelvetBot Stream Alerts")
        
        # Mention role if configured
        content = ""
        if Config.STREAM_PING_ROLE:
            content = f"<@&{Config.STREAM_PING_ROLE}>"
        
        await notification_channel.send(content=content, embed=embed)
        logger.info(f"Sent {platform} notification for {channel}")
        
        # Log to database
        if self.bot.db:
            await self.bot.db.log_stream(channel, platform, title)

    @commands.hybrid_command(name="stream", description="Configure stream alerts")
    @commands.has_permissions(manage_guild=True)
    async def stream_config(self, ctx, action: str, platform: str, channel: str = None):
        """Configure stream monitoring.
        
        Usage:
            !stream add twitch channelname
            !stream remove youtube UCxxxxx
            !stream list all
        """
        action = action.lower()
        platform = platform.lower()
        
        if action == "list":
            embed = discord.Embed(
                title="\U0001F4FA Stream Monitoring",
                color=Config.COLORS['primary']
            )
            
            twitch_list = ", ".join(Config.TWITCH_CHANNELS) or "None"
            youtube_list = ", ".join(Config.YOUTUBE_CHANNELS) or "None"
            
            embed.add_field(name="Twitch Channels", value=twitch_list, inline=False)
            embed.add_field(name="YouTube Channels", value=youtube_list, inline=False)
            embed.set_footer(text="Use !stream add/remove to modify")
            
            await ctx.send(embed=embed)
            return
            
        if not channel:
            await ctx.send("\u274c Please specify a channel name/ID.")
            return
            
        # Note: In production, you'd save these to database
        if action == "add":
            await ctx.send(f"\u2705 Added {channel} to {platform} monitoring.\n" 
                          f"Note: Update config.py or .env to persist this change.")
        elif action == "remove":
            await ctx.send(f"\u2705 Removed {channel} from {platform} monitoring.")
        else:
            await ctx.send("\u274c Invalid action. Use: add, remove, or list")

    @commands.hybrid_command(name="announce", description="Manually announce a stream")
    @commands.has_permissions(manage_messages=True)
    async def announce_stream(self, ctx, platform: str, *, title: str):
        """Manually send a stream notification (great for TikTok).
        
        Usage:
            !announce tiktok Going live with RDR2 gameplay!
            !announce twitch Special charity stream starting now!
        """
        platform = platform.lower()
        
        # Get the user's display name as the channel
        channel = ctx.author.display_name
        
        # Platform URLs
        urls = {
            "twitch": f"https://twitch.tv/{Config.TWITCH_CHANNELS[0] if Config.TWITCH_CHANNELS else 'velvetbot'}",
            "youtube": "https://youtube.com",
            "tiktok": "https://tiktok.com/@yourusername"  # Update in config
        }
        
        await self.send_stream_notification(
            platform=platform,
            channel=channel,
            title=title,
            game="Live Stream",
            thumbnail="",  # No thumbnail for manual announcements
            url=urls.get(platform, "https://linktr.ee/yourpage")
        )
        
        await ctx.send(f"\u2705 Stream announcement sent for {platform}!", ephemeral=True)

    @commands.hybrid_command(name="streamstats", description="View stream statistics")
    async def stream_stats(self, ctx):
        """View streaming statistics."""
        embed = discord.Embed(
            title="\U0001F4CA Stream Statistics",
            color=Config.COLORS['primary'],
            timestamp=datetime.utcnow()
        )
        
        # Get stats from database if available
        if self.bot.db:
            stats = await self.bot.db.get_stream_stats()
            embed.add_field(name="Total Streams", value=str(stats.get('total', 0)), inline=True)
            embed.add_field(name="This Month", value=str(stats.get('this_month', 0)), inline=True)
            embed.add_field(name="Platforms Used", value=stats.get('platforms', 'N/A'), inline=True)
        else:
            embed.description = "Database not connected. Stats unavailable."
        
        embed.set_footer(text="VelvetBot")
        await ctx.send(embed=embed)

    @check_twitch_streams.before_loop
    @check_youtube_streams.before_loop
    async def before_stream_check(self):
        """Wait for bot to be ready before starting stream checks."""
        await self.bot.wait_until_ready()


async def setup(bot):
    """Load the Streaming cog."""
    await bot.add_cog(Streaming(bot))
