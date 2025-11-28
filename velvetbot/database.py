"""VelvetBot Database Models
SQLAlchemy async database with models for users, tickets, clients, and more.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Float, Text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import Config

Base = declarative_base()


class User(Base):
    """User model for XP and leveling system."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    guild_id = Column(BigInteger, nullable=False)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    messages = Column(Integer, default=0)
    last_xp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Ticket(Base):
    """Support ticket model."""
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    guild_id = Column(BigInteger, nullable=False)
    channel_id = Column(BigInteger, nullable=True)
    category = Column(String(100), nullable=False)
    status = Column(String(20), default='open')
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)


class Client(Base):
    """Client model for business management."""
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    guild_id = Column(BigInteger, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    service_type = Column(String(100), nullable=True)
    revenue = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StreamAlert(Base):
    """Stream alert history."""
    __tablename__ = 'stream_alerts'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)
    channel = Column(String(100), nullable=True)
    stream_title = Column(String(255), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    peak_viewers = Column(Integer, default=0)
    notified = Column(Boolean, default=False)


class CustomCommand(Base):
    """Custom command storage."""
    __tablename__ = 'custom_commands'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, nullable=False)
    name = Column(String(50), nullable=False)
    response = Column(Text, nullable=False)
    created_by = Column(BigInteger, nullable=False)
    uses = Column(Integer, default=0)
    is_embed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class WarnLog(Base):
    """Moderation warning logs."""
    __tablename__ = 'warn_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    guild_id = Column(BigInteger, nullable=False)
    moderator_id = Column(BigInteger, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Database:
    """Async database handler."""
    
    def __init__(self):
        self.engine = create_async_engine(Config.DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def init(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    def get_session(self) -> AsyncSession:
        """Get a new database session."""
        return self.async_session()

    # User/XP Methods
    async def get_or_create_user(self, user_id: int, guild_id: int) -> User:
        """Get or create a user record."""
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id, User.guild_id == guild_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                user = User(user_id=user_id, guild_id=guild_id)
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user
    
    async def add_xp(self, user_id: int, guild_id: int, amount: int) -> tuple:
        """Add XP to a user. Returns (new_xp, new_level, leveled_up)."""
        async with self.get_session() as session:
            user = await self.get_or_create_user(user_id, guild_id)
            old_level = user.level
            user.xp += amount
            user.messages += 1
            user.last_xp = datetime.utcnow()
            
            # Calculate new level (simple formula: level = xp / 100)
            new_level = (user.xp // 100) + 1
            leveled_up = new_level > old_level
            user.level = new_level
            
            await session.commit()
            return user.xp, new_level, leveled_up

    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[User]:
        """Get XP leaderboard for a guild."""
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.guild_id == guild_id).order_by(User.xp.desc()).limit(limit)
            )
            return result.scalars().all()

    # Warning Methods
    async def add_warning(self, user_id: int, guild_id: int, moderator_id: int, reason: str):
        """Add a warning to a user."""
        async with self.get_session() as session:
            warn = WarnLog(user_id=user_id, guild_id=guild_id, moderator_id=moderator_id, reason=reason)
            session.add(warn)
            await session.commit()
    
    async def get_warnings(self, user_id: int, guild_id: int) -> List[Dict]:
        """Get all warnings for a user."""
        async with self.get_session() as session:
            result = await session.execute(
                select(WarnLog).where(WarnLog.user_id == user_id, WarnLog.guild_id == guild_id)
            )
            warns = result.scalars().all()
            return [{'reason': w.reason, 'created_at': w.created_at.strftime('%Y-%m-%d')} for w in warns]
    
    async def clear_warnings(self, user_id: int, guild_id: int):
        """Clear all warnings for a user."""
        async with self.get_session() as session:
            result = await session.execute(
                select(WarnLog).where(WarnLog.user_id == user_id, WarnLog.guild_id == guild_id)
            )
            for warn in result.scalars().all():
                await session.delete(warn)
            await session.commit()

    # Stream Methods
    async def log_stream(self, channel: str, platform: str, title: str):
        """Log a stream notification."""
        async with self.get_session() as session:
            alert = StreamAlert(channel=channel, platform=platform, stream_title=title, notified=True)
            session.add(alert)
            await session.commit()
    
    async def get_stream_stats(self) -> Dict[str, Any]:
        """Get stream statistics."""
        async with self.get_session() as session:
            result = await session.execute(select(StreamAlert))
            alerts = result.scalars().all()
            
            this_month = [a for a in alerts if a.started_at.month == datetime.utcnow().month]
            platforms = set(a.platform for a in alerts)
            
            return {
                'total': len(alerts),
                'this_month': len(this_month),
                'platforms': ', '.join(platforms) if platforms else 'None'
            }

    # Mod logging
    async def log_mod_action(self, guild_id: int, action: str, target_id: int, mod_id: int, reason: str):
        """Log a moderation action (for audit purposes)."""
        # Can be expanded to a separate ModLog table
        pass

    # Custom Commands
    async def get_custom_command(self, guild_id: int, name: str) -> Optional[CustomCommand]:
        """Get a custom command by name."""
        async with self.get_session() as session:
            result = await session.execute(
                select(CustomCommand).where(CustomCommand.guild_id == guild_id, CustomCommand.name == name)
            )
            return result.scalar_one_or_none()
    
    async def get_all_custom_commands(self, guild_id: int) -> List[CustomCommand]:
        """Get all custom commands for a guild."""
        async with self.get_session() as session:
            result = await session.execute(
                select(CustomCommand).where(CustomCommand.guild_id == guild_id)
            )
            return result.scalars().all()
