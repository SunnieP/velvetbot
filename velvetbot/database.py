"""VelvetBot Database Models
SQLAlchemy async database with models for users, tickets, clients, and more.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Float, Text
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
    status = Column(String(50), default='active')
    total_revenue = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StreamAlert(Base):
    """Stream alert history."""
    __tablename__ = 'stream_alerts'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)
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
