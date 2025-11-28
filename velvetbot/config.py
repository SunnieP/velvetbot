"""VelvetBot Configuration
Environment-based configuration using Velvet & Sage brand colors.
"""

import os
from typing import Dict, Any, List


class Config:
    """Bot configuration settings."""
    
    # Bot Settings
    PREFIX = os.getenv('BOT_PREFIX', '!')
    
    # Brand Colors (Velvet & Sage palette)
    COLORS: Dict[str, int] = {
        'primary': 0x8B7355,    # Velvet Brown
        'secondary': 0x9CAF88,  # Sage Green
        'accent': 0xE8D5C4,     # Cream
        'success': 0x9CAF88,    # Sage Green
        'warning': 0xD4A574,    # Warm Tan
        'error': 0xC17767,      # Muted Coral
        'info': 0x8B7355        # Velvet Brown
    }
    
    # Channel IDs (configure in .env)
    CHANNELS: Dict[str, int] = {
        'logs': int(os.getenv('LOG_CHANNEL_ID', 0)),
        'welcome': int(os.getenv('WELCOME_CHANNEL_ID', 0)),
        'stream_alerts': int(os.getenv('STREAM_ALERTS_CHANNEL_ID', 0)),
        'tickets': int(os.getenv('TICKETS_CATEGORY_ID', 0)),
        'announcements': int(os.getenv('ANNOUNCEMENTS_CHANNEL_ID', 0))
    }
    
    # Shortcut accessors for commonly used channels
    MOD_LOG_CHANNEL = int(os.getenv('MOD_LOG_CHANNEL_ID', 0)) or int(os.getenv('LOG_CHANNEL_ID', 0))
    STREAM_NOTIFICATION_CHANNEL = int(os.getenv('STREAM_ALERTS_CHANNEL_ID', 0))
    
    # Role IDs (configure in .env)
    ROLES: Dict[str, int] = {
        'admin': int(os.getenv('ADMIN_ROLE_ID', 0)),
        'moderator': int(os.getenv('MOD_ROLE_ID', 0)),
        'member': int(os.getenv('MEMBER_ROLE_ID', 0)),
        'client': int(os.getenv('CLIENT_ROLE_ID', 0)),
        'stream_notify': int(os.getenv('STREAM_NOTIFY_ROLE_ID', 0))
    }
    
    # Shortcut for stream ping role
    STREAM_PING_ROLE = int(os.getenv('STREAM_NOTIFY_ROLE_ID', 0))
    
    # Streaming Configuration
    TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID', '')
    TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET', '')
    TWITCH_USERNAME = os.getenv('TWITCH_USERNAME', '')
    
    # Twitch channels to monitor (list)
    @classmethod
    def get_twitch_channels(cls) -> List[str]:
        username = cls.TWITCH_USERNAME
        if username:
            return [username]
        return []
    
    TWITCH_CHANNELS: List[str] = property(lambda self: Config.get_twitch_channels())
    
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
    YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID', '')
    
    # YouTube channels to monitor (list)
    @classmethod  
    def get_youtube_channels(cls) -> List[str]:
        channel_id = cls.YOUTUBE_CHANNEL_ID
        if channel_id:
            return [channel_id]
        return []
    
    YOUTUBE_CHANNELS: List[str] = property(lambda self: Config.get_youtube_channels())
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///velvetbot.db')
    
    # XP System Settings
    XP_PER_MESSAGE = 15
    XP_COOLDOWN = 60  # seconds
    
    # Level Roles (level: role_id)
    LEVEL_ROLES: Dict[int, int] = {
        5: int(os.getenv('LEVEL_5_ROLE_ID', 0)),
        10: int(os.getenv('LEVEL_10_ROLE_ID', 0)),
        25: int(os.getenv('LEVEL_25_ROLE_ID', 0)),
        50: int(os.getenv('LEVEL_50_ROLE_ID', 0)),
        100: int(os.getenv('LEVEL_100_ROLE_ID', 0))
    }
    
    # Auto-moderation Settings
    SPAM_THRESHOLD = 5   # messages
    SPAM_INTERVAL = 5    # seconds
    MAX_MENTIONS = 5
    
    # Ticket Categories
    TICKET_CATEGORIES = [
        {'name': 'Branding Inquiry', 'emoji': '\U0001F4BC', 'description': 'Questions about branding services'},
        {'name': 'The Hustl Support', 'emoji': '\U0001F680', 'description': 'Support for The Hustl clients'},
        {'name': 'Training/Analytics', 'emoji': '\U0001F4CA', 'description': 'Google Analytics training inquiries'},
        {'name': 'General Support', 'emoji': '\U0001F527', 'description': 'General questions and support'}
    ]
    
    @classmethod
    def get_color(cls, color_type: str) -> int:
        """Get a color from the palette."""
        return cls.COLORS.get(color_type, cls.COLORS['primary'])


# Create class-level list attributes
Config.TWITCH_CHANNELS = Config.get_twitch_channels()
Config.YOUTUBE_CHANNELS = Config.get_youtube_channels()
