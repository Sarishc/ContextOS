"""Database base models."""
from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    id: Any
    __name__: str
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically."""
        return cls.__name__.lower()


class TimestampMixin:
    """Mixin for timestamp columns."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

